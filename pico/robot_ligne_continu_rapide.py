import board
import busio
import adafruit_ov7670
import usb_cdc
import time
import digitalio
import pwmio

# ================================================================
# PARAMETRES A CALIBRER
# ================================================================
VITESSE_MIN    = 21    # vitesse dans les virages
VITESSE_MAX    = 40    # vitesse en ligne droite (a calibrer)
SEUIL_ANGLE    = 0.5   # |a| au-dela duquel on est a vitesse min (a calibrer)

COEFF_ANGLE    = 4.0   # correction due a l angle de la ligne
COEFF_DECALAGE = 1.5   # correction due au decalage lateral

SEUIL_NOIR_ARRIVE = 200 # moyenne de luminosite en dessous de laquelle tout le sol est noir (a calibrer)
VITESSE_ROTATION  = 24  # vitesse en marche arriere pour retrouver la ligne

# ================================================================
# SETUP BOUTON (GP22, branche sur GND -> actif LOW, pull-up)
# ================================================================
bouton = digitalio.DigitalInOut(board.GP22)
bouton.direction = digitalio.Direction.INPUT
bouton.pull      = digitalio.Pull.UP

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
# SETUP CAMERA (OV7670, paysage, flip_y)
# ================================================================
xclk = pwmio.PWMOut(board.GP11, frequency=10_000_000, duty_cycle=32768)
time.sleep(0.5)

i2c = busio.I2C(board.GP9, board.GP8)

try:
    cam = adafruit_ov7670.OV7670(
        i2c,
        [board.GP0, board.GP1, board.GP2, board.GP3,
         board.GP4, board.GP5, board.GP6, board.GP7],
        board.GP10,
        board.GP13,
        board.GP12
    )
    cam.size = adafruit_ov7670.OV7670_SIZE_DIV16
    cam.colorspace = adafruit_ov7670.OV7670_COLOR_YUV
    cam.flip_y = True
    cam.gain_control = False
    cam.exposure_control = False
except Exception as e:
    print(f"Erreur camera : {e}")
    while True:
        time.sleep(1)

width, height = 40, 30
raw_buf  = bytearray(width * height * 2)
gray_buf = bytearray(width * height)
serial   = usb_cdc.console


# ================================================================
# REGRESSION LINEAIRE
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
# GUIDAGE ADAPTATIF
# Vitesse proportionnelle a la droiture de la ligne :
#   |a| = 0   -> VITESSE_MAX (ligne droite)
#   |a| >= SEUIL_ANGLE -> VITESSE_MIN (virage)
# ================================================================
def guider(a, b):
    droiture = max(0.0, 1.0 - abs(a) / SEUIL_ANGLE)
    vitesse  = VITESSE_MIN + (VITESSE_MAX - VITESSE_MIN) * droiture

    correction = COEFF_DECALAGE * b + COEFF_ANGLE * a
    vd = max(0, min(100, vitesse - correction))
    vg = max(0, min(100, vitesse + correction))
    _pwm_droite(vd)
    _pwm_gauche(vg)


# ================================================================
# BOUCLE PRINCIPALE
# ================================================================
seuil_dynamique = 0
ecart_minimum   = 90

ETAT_ATTENTE   = 0
ETAT_COURSE    = 1
ETAT_RECHERCHE = 2
ETAT_ARRIVE    = 3

etat = ETAT_ATTENTE
stop()

while True:
    # --- Capture et binarisation ---
    cam.capture(raw_buf)

    val_min = 255
    val_max = 0
    val_sum = 0
    idx = 0
    for i in range(0, width * height * 2, 2):
        val = raw_buf[i]
        if val < val_min:
            val_min = val
        elif val > val_max:
            val_max = val
        val_sum += val
        gray_buf[idx] = 0 if val <= seuil_dynamique else 255
        idx += 1

    val_moy = val_sum // (width * height)

    ecart = val_max - val_min
    if ecart > ecart_minimum:
        seuil_dynamique = val_min + int(ecart * 0.5)
    else:
        seuil_dynamique = -1

    # --- Envoi image debug ---
    if serial:
        serial.write(b"P5\n40 30\n255\n")
        serial.write(gray_buf)

    # --- Detection fin de parcours (luminosite moyenne basse = sol noir) ---
    if etat == ETAT_COURSE and val_moy < SEUIL_NOIR_ARRIVE:
        etat = ETAT_ARRIVE

    # --- Regression ---
    (a, b) = reg_lin_pico(gray_buf, width, height)

    # --- Debug ---
    droiture = max(0.0, 1.0 - abs(a) / SEUIL_ANGLE)
    vitesse_actuelle = VITESSE_MIN + (VITESSE_MAX - VITESSE_MIN) * droiture
    etats = ["ATTENTE", "COURSE", "RECHERCHE", "ARRIVE"]
    print("a:", a, " b:", b, " v:", int(vitesse_actuelle), " moy:", val_moy, " etat:", etats[etat])

    # --- Machine d etat ---
    if etat == ETAT_ATTENTE:
        stop()
        if not bouton.value:
            time.sleep(0.05)
            while not bouton.value:
                pass
            etat = ETAT_COURSE

    elif etat == ETAT_ARRIVE:
        stop()
        if not bouton.value:
            time.sleep(0.05)
            while not bouton.value:
                pass
            etat = ETAT_ATTENTE

    elif etat == ETAT_COURSE:
        if a == 0 and b == 0:
            etat = ETAT_RECHERCHE
            stop()
        else:
            guider(a, b)

    elif etat == ETAT_RECHERCHE:
        if a != 0 or b != 0:
            etat = ETAT_COURSE
        else:
            _pwm_gauche(-VITESSE_ROTATION)
            _pwm_droite(-VITESSE_ROTATION)
