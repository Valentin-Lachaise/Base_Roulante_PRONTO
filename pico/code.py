import board
import busio
import adafruit_ov7670
import usb_cdc
import time
import board
import digitalio
import pwmio
import rotaryio
import displayio
import terminalio
import analogio
from i2cdisplaybus import I2CDisplayBus
from adafruit_display_text import label
import adafruit_displayio_sh1106



#---------------------------SETUP ECRAN ET BATTERIE----------------------------

displayio.release_displays()

i2c = busio.I2C(scl=board.GP27, sda=board.GP26)
display_bus = I2CDisplayBus(i2c, device_address=0x3C)

WIDTH = 132
HEIGHT = 64

display = adafruit_displayio_sh1106.SH1106(display_bus, width=WIDTH, height=HEIGHT)

splash = displayio.Group()
display.root_group = splash

color_white = displayio.Palette(1)
color_white[0] = 0xFFFFFF
color_black = displayio.Palette(1)
color_black[0] = 0x000000

battery_x = 2
battery_y = 20
battery_width = 50
battery_height = 24
border = 2

body_bitmap = displayio.Bitmap(battery_width, battery_height, 1)
body_sprite = displayio.TileGrid(body_bitmap, pixel_shader=color_white, x=battery_x, y=battery_y)
splash.append(body_sprite)

inner_bitmap = displayio.Bitmap(battery_width - border * 2, battery_height - border * 2, 1)
inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=color_black, x=battery_x + border, y=battery_y + border)
splash.append(inner_sprite)

tip_width = 4
tip_height = 10
tip_x = battery_x + battery_width
tip_y = battery_y + (battery_height // 2) - (tip_height // 2)

tip_bitmap = displayio.Bitmap(tip_width, tip_height, 1)
tip_sprite = displayio.TileGrid(tip_bitmap, pixel_shader=color_white, x=tip_x, y=tip_y)
splash.append(tip_sprite)

text_area_batt = label.Label(
    terminalio.FONT, text="--%", color=0xFFFFFF, x=battery_x + 10, y=battery_y + (battery_height // 2)
)
splash.append(text_area_batt)

text_ligne = "Ligne\ndétectée"
text_area_ligne = label.Label(
    terminalio.FONT, text=text_ligne, color=0xFFFFFF, x=64, y=32
)
splash.append(text_area_ligne)

vbat_pin = analogio.AnalogIn(board.GP28)


#------------------------SETUP CALIBRATION----------------------

vitesse_prec_d = 12
vitesse_prec_g = 12

def absolute_val(a):
    if (a<0):
        return -a
    else:
        return a

def calibration(angle, decalage):
    global vitesse_prec_d, vitesse_prec_g
    #amelioration possible: ajouter un facteur a l'aide de la derivée de la courbe

    decalage_max = 0 #a determiner
    angle_max = 0#a determiner

    #les vitesses moteur initialement demandées sont les suivantes, c'est la vitesse "constante" du robot
    vitesse_constante_gauche = 18 / (1+absolute_val(angle))
    vitesse_constante_droite = 18 / (1+absolute_val(angle))
    amplification_angle = 5


     #a definir avec l'experience
    amplification_de_decalage = 0.4
    #amplification de décalage a determiner avec l'experience

    #on modifie la vitesse droite ou gauche pour pivoter le robot
    if(angle>angle_max):
        vitesse_constante_gauche += amplification_angle*(angle)
        # vitesse_constante_droite -= amplification_angle*(angle) /2


    if(-angle>angle_max):
        vitesse_constante_droite += amplification_angle*(-angle)
        # vitesse_constante_gauche -= amplification_angle*(-angle)/2


    if(decalage>decalage_max):
        vitesse_constante_gauche += (decalage)*amplification_de_decalage/2
        # vitesse_constante_droite -= (decalage)*amplification_de_decalage

    if(-decalage>decalage_max):
        vitesse_constante_droite += (-decalage)*amplification_de_decalage/2
        # vitesse_constante_gauche -= (-decalage)*amplification_de_decalage

    vitesse_constante_droite = (vitesse_constante_droite + vitesse_prec_d)/2
    vitesse_constante_gauche = (vitesse_constante_gauche + vitesse_prec_g)/2

    vitesse_constante_droite = max(0, min(100, vitesse_constante_droite))
    vitesse_constante_gauche = max(0, min(100, vitesse_constante_gauche))

    #on renvoie les vitesses demandées, puis a l'aide de la vitesse réelle, le code "main" atteint la vitesse requise
    vitesse_prec_d = vitesse_constante_droite
    vitesse_prec_g = vitesse_constante_gauche
    return vitesse_constante_droite, vitesse_constante_gauche


def pid(vitesse_cible_g, vitesse_reele_g, vitesse_cible_d, vitesse_reele_d):

    pid_factor = 5 # a determiner
    return ((vitesse_cible_d-vitesse_reele_d)*pid_factor, (vitesse_cible_g-vitesse_reele_g)*pid_factor)


#------------------------SETUP REGRESSION----------------------


def reg_lin_pico(buffer, width, height):
    n = sum_x = sum_y = sum_xx = sum_xy = 0

    # --- Paramètres synchronisés avec OpenCV ---
    # Si OpenCV : pts_source haut = [8, 0] et [22, 0] -> largeur = 22 - 8 = 14
    largeur_bas = 30.0   # Largeur totale de l'image redressée
    largeur_haut = 14.0  # Largeur capturée au point le plus lointain
    hauteur_image = 40.0 # Profondeur totale

    # Calcul de la matrice d'homographie 1D
    B = largeur_haut / largeur_bas
    A = (1.0 - B) / hauteur_image

    for j in range(1, height):
        for i in range(1, width):
            if buffer[i + width * j] == 0:
                x_rot = j
                y_rot = width - 1 - i

                # 1. Calcul du coefficient de profondeur Z pour ce pixel
                # y_rot va de 0 (tout en haut, horizon lointain) à 39 (tout en bas, nez du robot)
                Z = A * y_rot + B

                # 2. Correction de l'axe horizontal (gauche/droite)
                y_val_brut = x_rot - (height // 2)
                y_corrige = y_val_brut / Z

                # 3. Correction de l'axe vertical (avance)
                # On divise par Z pour redresser la profondeur, puis on inverse
                # pour que l'axe "x_val" soit à 0 près du robot et à 40 au loin.
                x_val_corrige = hauteur_image - (y_rot / Z)

                # Accumulation
                n += 1
                sum_x += x_val_corrige
                sum_y += y_corrige
                sum_xx += x_val_corrige * x_val_corrige
                sum_xy += x_val_corrige * y_corrige

    if n < 2:
        return 0, 0

    denominateur = (n * sum_xx - (sum_x ** 2))
    if denominateur == 0:
        return 0, 0

    a = (n * sum_xy - sum_x * sum_y) / denominateur
    b = (sum_y - a * sum_x) / n

    decal_ligne_droite = 0.09
    return a-decal_ligne_droite, b



#------------------------SETUP MOTEUR----------------------
# --- Tables de correspondance Vitesse (extraites de vos tests) ---
# Format: (consigne_pwm, vitesse_reelle_cms)
TABLE_MOTEUR_D = [
    (0, 0.0), (8, 1.1), (10, 1.78), (12, 2.38), (14, 3.01), (16, 3.61), 
    (18, 4.29), (20, 4.88), (22, 5.48), (24, 6.11), (26, 6.79), (28, 7.39), 
    (30, 8.07), (32, 8.7), (34, 9.34), (36, 9.98), (38, 10.6), (40, 11.21), 
    (42, 11.89), (44, 12.47), (46, 13.12), (48, 13.79), (50, 14.39), (52, 15.03), 
    (54, 15.69), (56, 16.32), (58, 16.97), (60, 17.62), (62, 18.26), (64, 18.87), 
    (66, 19.53), (68, 20.15), (70, 20.8), (72, 21.4), (74, 22.06), (76, 22.76), 
    (78, 23.35), (80, 23.96), (82, 24.63), (84, 25.28), (86, 25.9), (88, 26.51), 
    (90, 27.17), (92, 27.97), (94, 28.59), (96, 29.27), (98, 30.02), (100, 30.92)
]

TABLE_MOTEUR_G = [
    (0, 0.0), (6, 0.55), (8, 1.23), (10, 1.91), (12, 2.55), (14, 3.1), 
    (16, 3.74), (18, 4.33), (20, 4.93), (22, 5.56), (24, 6.16), (26, 6.79), 
    (28, 7.43), (30, 8.07), (32, 8.65), (34, 9.3), (36, 9.85), (38, 10.52), 
    (40, 11.12), (42, 11.72), (44, 12.34), (46, 12.95), (48, 13.57), (50, 14.18), 
    (52, 14.82), (54, 15.44), (56, 16.06), (58, 16.63), (60, 17.32), (62, 17.96), 
    (64, 18.49), (66, 19.15), (68, 19.72), (70, 20.38), (72, 21.06), (74, 21.59), 
    (76, 22.25), (78, 22.84), (80, 23.41), (82, 24.07), (84, 24.64), (86, 25.26), 
    (88, 25.87), (90, 26.54), (92, 27.24), (94, 27.91), (96, 28.59), (98, 29.3), 
    (100, 30.16)
]


def get_consigne_droite(vitesse_cms):
    """
    Calcule la consigne PWM pour le moteur droit à partir d'une vitesse en cm/s.
    """
    if vitesse_cms <= 0:
        return 0

    # On parcourt la table pour trouver l'intervalle contenant notre vitesse
    for i in range(len(TABLE_MOTEUR_D) - 1):
        pwm1, v1 = TABLE_MOTEUR_D[i]
        pwm2, v2 = TABLE_MOTEUR_D[i+1]

        if v1 <= vitesse_cms <= v2:
            if v2 - v1 == 0:
                return pwm1
            
            # Interpolation linéaire
            proportion = (vitesse_cms - v1) / (v2 - v1)
            return pwm1 + proportion * (pwm2 - pwm1)

    # Si la vitesse est plus grande que toutes les valeurs de la table, retourner 100
    return 100


def get_consigne_gauche(vitesse_cms):
    """
    Calcule la consigne PWM pour le moteur gauche à partir d'une vitesse en cm/s.
    """
    if vitesse_cms <= 0:
        return 0

    # On parcourt la table pour trouver l'intervalle contenant notre vitesse
    for i in range(len(TABLE_MOTEUR_G) - 1):
        pwm1, v1 = TABLE_MOTEUR_G[i]
        pwm2, v2 = TABLE_MOTEUR_G[i+1]

        if v1 <= vitesse_cms <= v2:
            if v2 - v1 == 0:
                return pwm1
            
            # Interpolation linéaire
            proportion = (vitesse_cms - v1) / (v2 - v1)
            return pwm1 + proportion * (pwm2 - pwm1)

    # Si la vitesse est plus grande que toutes les valeurs de la table, retourner 100
    return 100


dir_pin_droite = digitalio.DigitalInOut(board.GP14)
dir_pin_droite.direction = digitalio.Direction.OUTPUT

# DIR Gauche sur GP15
dir_pin_gauche = digitalio.DigitalInOut(board.GP15)
dir_pin_gauche.direction = digitalio.Direction.OUTPUT

# La fréquence est fixée à 10000 Hz
# EN droite sur GP16 (PWM)
en_pin_droite = pwmio.PWMOut(board.GP16, frequency=10000)
# EN gauche sur GP17 (PWM)
en_pin_gauche = pwmio.PWMOut(board.GP17, frequency=10000)


#utiliser 18-21 pour les SA et SB, a setup si besoin
encodeur_g = rotaryio.IncrementalEncoder(board.GP19, board.GP18)
encodeur_d = rotaryio.IncrementalEncoder(board.GP20, board.GP21)




# --- Fonctions de pilotage droite ---

def pos_droite():
    return encodeur_d.position

def moteur_avant_droite(vitesse):
    vitesse = max(0, min(100, vitesse))
    dir_pin_droite.value = True # Activation de la puce
    # De 50% (32768) à 100% (65535)
    en_pin_droite.duty_cycle = 32768 + int((vitesse / 100.0) * 32767)

def moteur_arriere_droite(vitesse):
    vitesse = max(0, min(100, vitesse))
    dir_pin_droite.value = True
    # De 50% (32768) à 0% (0)
    en_pin_droite.duty_cycle = 32768 - int((vitesse / 100.0) * 32768)

def moteur_stop_droite():
    dir_pin_droite.value = True
    en_pin_droite.duty_cycle = 32768 # Point mort

# --- Fonctions de pilotage gauche ---

def pos_gauche():
    return encodeur_g.position

def moteur_avant_gauche(vitesse):
    vitesse = max(0, min(100, vitesse))
    dir_pin_gauche.value = True
    en_pin_gauche.duty_cycle = 32768 + int((vitesse / 100.0) * 32767)

def moteur_arriere_gauche(vitesse):
    vitesse = max(0, min(100, vitesse))
    dir_pin_gauche.value = True
    en_pin_gauche.duty_cycle = 32768 - int((vitesse / 100.0) * 32768)

def moteur_stop_gauche():
    dir_pin_gauche.value = True
    en_pin_gauche.duty_cycle = 32768 # Point mort

#------------------------FIN SETUP MOTEUR----------------------









#------------------------SETUP CAMERA----------------------

# 1. Horloge maître
xclk = pwmio.PWMOut(board.GP11, frequency=10_000_000, duty_cycle=32768)
time.sleep(0.5)

# 2. Configuration I2C
i2c = busio.I2C(board.GP9, board.GP8)

# 3. Initialisation 160x120
try:
    cam = adafruit_ov7670.OV7670(
        i2c,
        [board.GP0, board.GP1, board.GP2, board.GP3, board.GP4, board.GP5, board.GP6, board.GP7],
        board.GP10,   # PCLK
        board.GP13,   # VSYNC
        board.GP12    # HREF
    )
    # DIV4 donne 160x120
    cam.size = adafruit_ov7670.OV7670_SIZE_DIV16
    cam.colorspace = adafruit_ov7670.OV7670_COLOR_YUV
    cam.flip_y = True

    # Désactiver le contrôle automatique du gain et de l'exposition
    cam.gain_control = False
    cam.exposure_control = False

    # Activer le test pattern pour le calibrage
except Exception as e:
    print(f"Erreur : {e}")
    while True: time.sleep(1)

width, height = 40, 30
rotated_width, rotated_height = height, width
rotated_buf = bytearray(rotated_width * rotated_height)
raw_buf = bytearray(width * height * 2)
gray_buf = bytearray(width * height)
serial = usb_cdc.console
#----------------FIN SETUP CAMERA-----------------




derniere_position_g = 0
derniere_position_d = 0
a=0
b=0

seuil_dynamique = 0
ecart_minimum = 90 # Différence requise entre le blanc du sol et le noir de la ligne (à ajuster)


TICKS_PAR_TOUR = 480  # Nombre de ticks de l'encodeur pour un tour de roue
DIAMETRE_ROUE_CM = 6.5  # Diamètre de la roue en cm
PERIMETRE_ROUE_CM = DIAMETRE_ROUE_CM * 3.1415
last_time = time.monotonic()


erreur_lin_PID = 0.1
erreur_g_prec = 0
erreur_d_prec = 0
facteur_diff_PID = 1
# Dans votre 'while True'
while True:
    voltage = (vbat_pin.value / 65535) * 3.3

    if voltage < 1.5:
        body_sprite.hidden = True
        inner_sprite.hidden = True
        tip_sprite.hidden = True

        text_area_batt.text = "Défaut\nbatterie"
        text_area_batt.x = 2
        text_area_batt.y = 28
        text_area_batt.hidden = False

        # time.sleep(0.5)

    elif voltage < 1.8:
        body_sprite.hidden = True
        inner_sprite.hidden = True
        tip_sprite.hidden = True

        text_area_batt.text = "Recharger\nbatterie"
        text_area_batt.x = 2
        text_area_batt.y = 28

        text_area_batt.hidden = not text_area_batt.hidden

        # time.sleep(0.5)
    else:
        body_sprite.hidden = False
        inner_sprite.hidden = False
        tip_sprite.hidden = False
        text_area_batt.hidden = False

        percent = ((voltage - 1.82) / (2.21 - 1.82)) * 100
        if percent < 0:
            percent = 0
        elif percent > 100:
            percent = 100

        text_area_batt.text = f"{int(percent)}%"
        text_area_batt.x = battery_x + 10
        text_area_batt.y = battery_y + (battery_height // 2)


    cam.capture(raw_buf)

    val_min = 255
    val_max = 0
    idx = 0

    for i in range(0, width * height * 2, 2):
        val = raw_buf[i]

        # 1. Recherche du min et max pour la frame SUIVANTE
        if val < val_min:
            val_min = val
        elif val > val_max:
            val_max = val

        # 2. Application du seuil calculé à la frame précédente
        gray_buf[idx] = 0 if val <= seuil_dynamique else 255
        idx += 1

    # 3. Calcul du seuil pour la frame SUIVANTE
    ecart = val_max - val_min

    if ecart > ecart_minimum:
        # Contraste suffisant : il y a une ligne.
        # On place le seuil dans le tiers le plus sombre de l'image.
        seuil_dynamique = val_min + int(ecart * 0.5)
    else:
        # Sol uni (pas de ligne).
        # On passe le seuil en négatif pour que la binarisation renvoie 100% de pixels blancs (255).
        seuil_dynamique = -1

    # serial.write(b"P5\n30 40\n255\n")
    # serial.write(gray_buf)

    current_time = time.monotonic()
    delta_t = current_time - last_time
    last_time = current_time

    #vitesse actuelle si besoin:
    # #vitesse gauche
    
    position_actuelle_g = pos_gauche()
    position_actuelle_d = pos_droite()
    if(delta_t>0):
        vitesse_reele_g =( (position_actuelle_g - derniere_position_g)/TICKS_PAR_TOUR/delta_t ) *  PERIMETRE_ROUE_CM
        vitesse_reele_d =( (position_actuelle_d - derniere_position_d)/TICKS_PAR_TOUR/delta_t ) * PERIMETRE_ROUE_CM
    
    derniere_position_d = position_actuelle_d
    derniere_position_g = position_actuelle_g



    (a, b) = reg_lin_pico(gray_buf, width, height)
    print("a:", a)
    print("b:", b)
    print(get_consigne_droite(vitesse_reele_d))
    print(get_consigne_gauche(vitesse_reele_g))
    if(a ==0 and b== 0):
        #pas de ligne noire sur l'image
        moteur_arriere_droite(16)
        moteur_arriere_gauche(15)


    else:
        # vitesse reele max droite: 162
        # vitesse reele max gauche: 168

        (vitesse_d, vitesse_g) = calibration(a, b)
        moteur_avant_droite(vitesse_d)
        moteur_avant_gauche(vitesse_g)
        # (vitesse_d, vitesse_g) = (20, 20)
        # erreur_d = (vitesse_d - get_consigne_droite(vitesse_reele_d))*erreur_lin_PID
        # erreur_g = (vitesse_g - get_consigne_gauche(vitesse_reele_g))*erreur_lin_PID
        # erreur_diff_g = (erreur_g_prec-erreur_g)*facteur_diff_PID
        # erreur_diff_d = (erreur_d_prec-erreur_d)*facteur_diff_PID

        # moteur_avant_gauche(vitesse_d+erreur_d-erreur_diff_d)
        # moteur_avant_droite(vitesse_g+erreur_g-erreur_diff_g)

        # moteur_avant_gauche(vitesse_d)
        # moteur_avant_droite(vitesse_g)


