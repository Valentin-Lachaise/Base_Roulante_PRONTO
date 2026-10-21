import board
import busio
import adafruit_ov7670
import usb_cdc
import time
import digitalio
import pwmio
import rotaryio
import displayio
import terminalio
from i2cdisplaybus import I2CDisplayBus
from adafruit_display_text import label
import adafruit_displayio_sh1106

# ================================================================
# PARAMETRES A CALIBRER
# ================================================================
DEAD_ZONE    = 20    # PWM% minimum pour que les moteurs tournent sur le sol
PERIODE_MS   = 150   # duree d un cycle macro-PWM en ms
VITESSE_BASE = 22    # vitesse effective de base (en dessous de dead zone)
VITESSE_MIN = 10

COEFF_ANGLE    = 5.0  # correction due a l angle de la ligne  (a calibrer)
COEFF_DECALAGE = 2.0  # correction due au decalage lateral    (a calibrer)

SEUIL_NOIR_ARRIVE = 160 # moyenne de luminosite en dessous de laquelle tout le sol est noir (a calibrer)
VITESSE_ROTATION  = 24  # vitesse en marche arriere pour retrouver la ligne

ECART_MINIMUM  = 30   # contraste minimum par rangee pour detecter la ligne

# ================================================================
# SETUP ECRAN (SH1106, I2C sur GP26=SDA / GP27=SCL)
# ================================================================
displayio.release_displays()

i2c_display = busio.I2C(scl=board.GP27, sda=board.GP26)
display_bus  = I2CDisplayBus(i2c_display, device_address=0x3C)
display      = adafruit_displayio_sh1106.SH1106(display_bus, width=132, height=64)

splash = displayio.Group()
display.root_group = splash

color_white = displayio.Palette(1)
color_white[0] = 0xFFFFFF
color_black = displayio.Palette(1)
color_black[0] = 0x000000

battery_x      = 2
battery_y      = 20
battery_width  = 50
battery_height = 24
border         = 2

body_bitmap  = displayio.Bitmap(battery_width, battery_height, 1)
body_sprite  = displayio.TileGrid(body_bitmap,  pixel_shader=color_white, x=battery_x,          y=battery_y)
splash.append(body_sprite)

inner_bitmap = displayio.Bitmap(battery_width - border * 2, battery_height - border * 2, 1)
inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=color_black, x=battery_x + border, y=battery_y + border)
splash.append(inner_sprite)

tip_bitmap = displayio.Bitmap(4, 10, 1)
tip_sprite = displayio.TileGrid(tip_bitmap, pixel_shader=color_white,
                                x=battery_x + battery_width,
                                y=battery_y + (battery_height // 2) - 5)
splash.append(tip_sprite)

# Note : GP28 est utilise pour la LED, la batterie affiche "--%" statiquement
text_area_batt = label.Label(
    terminalio.FONT, text="--%", color=0xFFFFFF,
    x=battery_x + 10, y=battery_y + (battery_height // 2)
)
splash.append(text_area_batt)

text_area_statut = label.Label(
    terminalio.FONT, text="En attente\ndu bouton", color=0xFFFFFF, x=64, y=20
)
splash.append(text_area_statut)

# ================================================================
# SETUP BOUTON (GP22, branche sur GND -> actif LOW, pull-up)
# ================================================================
bouton = digitalio.DigitalInOut(board.GP22)
bouton.direction = digitalio.Direction.INPUT
bouton.pull      = digitalio.Pull.UP

# ================================================================
# SETUP LED (GP28)
# ================================================================
led = digitalio.DigitalInOut(board.GP28)
led.direction = digitalio.Direction.OUTPUT
led.value     = False

# ================================================================
# SETUP MOTEURS (PmodDHB1, mode anti-phase)
# ================================================================
dir_pin_droite = digitalio.DigitalInOut(board.GP14)
dir_pin_droite.direction = digitalio.Direction.OUTPUT
dir_pin_droite.value = True

dir_pin_gauche = digitalio.DigitalInOut(board.GP15)
dir_pin_gauche.direction = digitalio.Direction.OUTPUT
dir_pin_gauche.value = True

en_pin_droite = pwmio.PWMOut(board.GP16, frequency=20000)
en_pin_gauche = pwmio.PWMOut(board.GP17, frequency=20000)

encodeur_g = rotaryio.IncrementalEncoder(board.GP19, board.GP18)
encodeur_d = rotaryio.IncrementalEncoder(board.GP21, board.GP20)


def _pwm_droite(vitesse):
    vitesse = max(-100, min(100, vitesse))
    en_pin_droite.duty_cycle = 32768 + int((vitesse / 100.0) * 32767)

def _pwm_gauche(vitesse):
    vitesse = max(-100, min(100, vitesse))
    en_pin_gauche.duty_cycle = 32768 + int((vitesse / 100.0) * 32767)

def stop():
    _pwm_droite(0)
    _pwm_gauche(0)


# ================================================================
# SETUP CAMERA (OV7670, paysage, flip_y) - I2C sur GP8=SDA / GP9=SCL
# ================================================================
xclk = pwmio.PWMOut(board.GP11, frequency=10_000_000, duty_cycle=32768)
time.sleep(0.5)

i2c_camera = busio.I2C(board.GP9, board.GP8)

try:
    cam = adafruit_ov7670.OV7670(
        i2c_camera,
        [board.GP0, board.GP1, board.GP2, board.GP3,
         board.GP4, board.GP5, board.GP6, board.GP7],
        board.GP10,   # PCLK
        board.GP13,   # VSYNC
        board.GP12    # HREF
    )
    cam.size       = adafruit_ov7670.OV7670_SIZE_DIV16
    cam.colorspace = adafruit_ov7670.OV7670_COLOR_YUV
    cam.flip_y     = True
    cam.gain_control     = False
    cam.exposure_control = False
except Exception as e:
    text_area_statut.text = "Erreur\ncamera"
    print(f"Erreur camera : {e}")
    while True:
        time.sleep(1)

width, height = 40, 30
raw_buf   = bytearray(width * height * 2)
gray_buf  = bytearray(width * height)
row_seuil = bytearray(height)
serial    = usb_cdc.console


# ================================================================
# REGRESSION LINEAIRE
# Camera en paysage, flip_y=True :
#   i (colonne) = axe lateral  : i=0 droite image = droite robot (miroir)
#   j (ligne)   = axe profondeur : j=0=loin, j=height-1=pres du robot
#
# Resultat : u = a*v + b
#   b > 0 : ligne a droite du robot  -> tourner a droite
#   b < 0 : ligne a gauche du robot  -> tourner a gauche
#   a > 0 : ligne part vers la droite au loin -> anticiper droite
# ================================================================
def reg_lin_pico(buffer, width, height):
    n = sum_x = sum_y = sum_xx = sum_xy = 0

    centre_u     = (width  - 1) / 2.0
    marge_i      = 3
    marge_j_loin = 2
    marge_j_pres = 2

    for j in range(marge_j_loin, height - marge_j_pres):
        for i in range(marge_i, width - marge_i):
            if buffer[i + width * j] == 0:
                v = height - 1 - j
                u = centre_u - i

                n += 1
                sum_x  += v
                sum_y  += u
                sum_xx += v * v
                sum_xy += v * u

    if n < 2:
        return 0, 0

    denominateur = n * sum_xx - sum_x * sum_x
    if denominateur == 0:
        return 0, 0

    a = (n * sum_xy - sum_x * sum_y) / denominateur
    b = (sum_y - a * sum_x) / n
    return a, b


# ================================================================
# GUIDAGE AVEC MACRO-PWM
# ================================================================
def guider(a, b):
    correction = COEFF_DECALAGE * b + COEFF_ANGLE * a

    vd = max(0, min(100, VITESSE_BASE - correction))
    vg = max(0, min(100, VITESSE_BASE + correction))

    ratio_d = (vd / DEAD_ZONE) if vd > 0 else 0.0
    ratio_g = (vg / DEAD_ZONE) if vg > 0 else 0.0

    # Normaliser pour que le moteur le plus rapide soit ON 90% du temps
    ratio_max = max(ratio_d, ratio_g)
    if ratio_max > 0:
        scale = 0.9 / ratio_max
        ratio_d = ratio_d * scale
        ratio_g = ratio_g * scale

    pwm_d = vd if vd >= DEAD_ZONE else DEAD_ZONE
    pwm_g = vg if vg >= DEAD_ZONE else DEAD_ZONE

    t_on_d  = PERIODE_MS * ratio_d / 1000.0
    t_on_g  = PERIODE_MS * ratio_g / 1000.0
    t_total = PERIODE_MS / 1000.0

    t_both = min(t_on_d, t_on_g)
    _pwm_droite(pwm_d)
    _pwm_gauche(pwm_g)
    if t_both > 0:
        time.sleep(t_both)

    if t_on_d > t_on_g:
        _pwm_gauche(0)
        time.sleep(t_on_d - t_on_g)
        _pwm_droite(0)
    elif t_on_g > t_on_d:
        _pwm_droite(0)
        time.sleep(t_on_g - t_on_d)
        _pwm_gauche(0)
    else:
        _pwm_droite(0)
        _pwm_gauche(0)

    t_off = t_total - max(t_on_d, t_on_g)
    if t_off > 0:
        time.sleep(t_off)


# ================================================================
# CALIBRATION DEAD ZONE
# ================================================================
def calibrer_dead_zone():
    global DEAD_ZONE, VITESSE_BASE
    text_area_statut.text = "Calibration\nen cours..."
    encodeur_g.position = 0
    encodeur_d.position = 0
    for pwm in range(20, 61):
        _pwm_droite(pwm)
        _pwm_gauche(pwm)
        time.sleep(0.25)
        if abs(encodeur_g.position) > VITESSE_MIN or abs(encodeur_d.position) > VITESSE_MIN:
            DEAD_ZONE = pwm
            VITESSE_BASE = pwm + 3
            stop()
            print("Dead zone:", DEAD_ZONE, " Vitesse base:", VITESSE_BASE)
            return
    stop()
    print("Calibration echouee, dead zone inchangee:", DEAD_ZONE)


# ================================================================
# BOUCLE PRINCIPALE
# ================================================================
ETAT_ATTENTE   = 0
ETAT_COURSE    = 1
ETAT_RECHERCHE = 2
ETAT_ARRIVE    = 3

etat = ETAT_ATTENTE
stop()

while True:

    # ---- ATTENTE : on attend l'appui sur le bouton ----
    if etat == ETAT_ATTENTE:
        text_area_statut.text = "En attente\ndu bouton"
        if not bouton.value:
            time.sleep(0.05)               # anti-rebond
            while not bouton.value:        # attendre relachement
                pass
            calibrer_dead_zone()
            for _ in range(3):             # clignote 3 fois
                led.value = True
                time.sleep(0.2)
                led.value = False
                time.sleep(0.2)
            etat = ETAT_COURSE
        else:
            time.sleep(0.05)
        continue

    # ---- ARRIVE : fin de course ----
    if etat == ETAT_ARRIVE:
        led.value = True
        text_area_statut.text = "Arrive!"
        stop()
        if not bouton.value:
            time.sleep(0.05)
            while not bouton.value:
                pass
            led.value = False
            etat = ETAT_ATTENTE
        else:
            time.sleep(0.05)
        continue

    # ---- COURSE / RECHERCHE : capture et traitement image ----
    cam.capture(raw_buf)

    # Passe 1 : min/max par rangee + luminosite globale
    val_sum = 0
    for j in range(height):
        row_min = 255
        row_max = 0
        base = j * width * 2
        for i in range(0, width * 2, 2):
            val = raw_buf[base + i]
            val_sum += val
            if val < row_min:
                row_min = val
            elif val > row_max:
                row_max = val
        ecart = row_max - row_min
        row_seuil[j] = (row_min + ecart // 2) if ecart > ECART_MINIMUM else 0

    val_moy = val_sum // (width * height)

    # Passe 2 : binarisation avec le seuil propre a chaque rangee
    for j in range(height):
        seuil = row_seuil[j]
        base_raw  = j * width * 2
        base_gray = j * width
        for i in range(width):
            val = raw_buf[base_raw + i * 2]
            gray_buf[base_gray + i] = 0 if val <= seuil else 255

    if serial:
        serial.write(b"P5\n40 30\n255\n")
        serial.write(gray_buf)

    # --- Detection fin de parcours ---
    if etat == ETAT_COURSE and val_moy < SEUIL_NOIR_ARRIVE:
        etat = ETAT_ARRIVE

    (a, b) = reg_lin_pico(gray_buf, width, height)
    etats = ["ATTENTE", "COURSE", "RECHERCHE", "ARRIVE"]
    print("a:", a, " b:", b, " moy:", val_moy, " etat:", etats[etat])

    # ---- COURSE : suivi de ligne ----
    if etat == ETAT_COURSE:
        if a == 0 and b == 0:
            text_area_statut.text = "Ligne non\ndetectee"
            etat = ETAT_RECHERCHE
            stop()
        else:
            text_area_statut.text = "Ligne\ndetectee"
            guider(a, b)

    # ---- RECHERCHE : demi-tour jusqu'a retrouver la ligne ----
    elif etat == ETAT_RECHERCHE:
        if a != 0 or b != 0:
            etat = ETAT_COURSE
        else:
            _pwm_gauche(-VITESSE_ROTATION)
            _pwm_droite(-VITESSE_ROTATION)
