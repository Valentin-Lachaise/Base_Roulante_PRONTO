import board
import busio
import adafruit_ov7670
import usb_cdc
import time
import board
import digitalio
import pwmio
import rotaryio


#------------------------SETUP CALIBRATION----------------------

vitesse_prec_d = 12
vitesse_prec_g = 12



def calibration(angle, decalage):
    global vitesse_prec_d, vitesse_prec_g
    #amelioration possible: ajouter un facteur a l'aide de la derivée de la courbe

    decalage_max = 0 #a determiner
    angle_max = 0#a determiner

    #les vitesses moteur initialement demandées sont les suivantes, c'est la vitesse "constante" du robot
    vitesse_constante_gauche = 25
    vitesse_constante_droite = 25
    amplification_angle = 25


     #a definir avec l'experience
    amplification_de_decalage = 0
    #amplification de décalage a determiner avec l'experience

    #on modifie la vitesse droite ou gauche pour pivoter le robot
    if(angle>angle_max):
        vitesse_constante_droite += amplification_angle*(angle)
        # vitesse_constante_droite -= amplification_angle*(angle) /3


    if(-angle>angle_max):
        vitesse_constante_gauche += amplification_angle*(-angle)
        # vitesse_constante_gauche -= amplification_angle*(-angle)/3


    if(decalage>decalage_max):
        vitesse_constante_gauche += decalage*amplification_de_decalage/2

    if(-decalage>decalage_max):
        vitesse_constante_droite += (-decalage)*amplification_de_decalage/2

    # vitesse_constante_droite = (vitesse_constante_droite + vitesse_prec_d)/2
    # vitesse_constante_gauche = (vitesse_constante_gauche + vitesse_prec_g)/2

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

    for j in range(40, 120):
        for i in range(5, width):
            if buffer[i + width * j] <= 120:
                # 1. Rotation virtuelle de 90° anti-horaire
                # La nouvelle largeur devient 'height' (60)
                # La nouvelle hauteur devient 'width' (80)
                x_rot = j
                y_rot = width - 1 - i

                # 2. Application de votre changement de repère sur l'image tournée
                x_val = width - y_rot          # Axe vertical (avance)
                y_val = x_rot - (height // 2)  # Axe horizontal (gauche/droite)

                # Accumulation
                n += 1
                sum_x += x_val
                sum_y += y_val
                sum_xx += x_val * x_val
                sum_xy += x_val * y_val

    if n < 2:
        return 0, 0

    denominateur = (n * sum_xx - (sum_x ** 2))
    if denominateur == 0:
        return 0, 0

    a = (n * sum_xy - sum_x * sum_y) / denominateur
    b = (sum_y - a * sum_x) / n

    return a, b




#------------------------SETUP MOTEUR----------------------


dir_pin_droite = digitalio.DigitalInOut(board.GP14)
dir_pin_droite.direction = digitalio.Direction.OUTPUT

# DIR Gauche sur GP15
dir_pin_gauche = digitalio.DigitalInOut(board.GP15)
dir_pin_gauche.direction = digitalio.Direction.OUTPUT

# La fréquence est fixée à 10000 Hz
# EN droite sur GP16 (PWM)
en_pin_droite = pwmio.PWMOut(board.GP16, frequency=20000)
# EN gauche sur GP17 (PWM)
en_pin_gauche = pwmio.PWMOut(board.GP17, frequency=20000)


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
    cam.size = adafruit_ov7670.OV7670_SIZE_DIV4
    cam.colorspace = adafruit_ov7670.OV7670_COLOR_YUV
    cam.flip_y = True

    # Désactiver le contrôle automatique du gain et de l'exposition
    cam.gain_control = False
    cam.exposure_control = False

    # Activer le test pattern pour le calibrage
except Exception as e:
    print(f"Erreur : {e}")
    while True: time.sleep(1)

width, height = 160, 120
rotated_width, rotated_height = height, width
rotated_buf = bytearray(rotated_width * rotated_height)
raw_buf = bytearray(width * height * 2)
gray_buf = bytearray(width * height)
# serial = usb_cdc.console
#----------------FIN SETUP CAMERA-----------------




derniere_position_g = 0
derniere_position_d = 0
a=0
b=0

seuil_dynamique = 0
ecart_minimum = 90 # Différence requise entre le blanc du sol et le noir de la ligne (à ajuster)

erreur_lin_PID = 0.5

# Dans votre 'while True'
while True:
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


    #     # 2. Rotation de 90 degrés (sens antihoraire)
    # for j in range(height): # j = ancienne ligne
    #     for i in range(width):  # i = ancienne colonne
    #         # Le pixel à (i, j) va à (j, width - 1 - i) dans la nouvelle image
    #         # Mais comme les dimensions sont inversées, la nouvelle position est (j, new_height - 1 - i)
    #         new_i = j
    #         new_j = width - 1 - i
    #         rotated_buf[new_j * rotated_width + new_i] = gray_buf[j * width + i]
    # Envoi au Viewer avec les nouvelles dimensions
    # serial.write(b"P5\n30 40\n255\n")
    # serial.write(gray_buf)

    #vitesse actuelle si besoin:

    # #vitesse gauche
    position_actuelle_g = pos_gauche()
    vitesse_reele_g = (position_actuelle_g - derniere_position_g)*100/272+4
    derniere_position_g = position_actuelle_g

    # #vitesse droite
    position_actuelle_d = pos_droite()
    vitesse_reele_d = (position_actuelle_d - derniere_position_d)*100/280+4
    derniere_position_d = position_actuelle_d

    (a, b) = reg_lin_pico(gray_buf, width, height)
    # print("a:", a)
    # print("b:", b)
    # print(vitesse_reele_d)
    # print(vitesse_reele_g)
    # if(a ==0 and b==0):
    if(a ==0 and b==0):
        #pas de ligne noire sur l'image
        moteur_arriere_droite(25)
        moteur_arriere_gauche(25)


    else:
        #vitesse reele max droite: 280
        #vitesse reele max gauche: 272
        (vitesse_d, vitesse_g) = calibration(a, b)
        moteur_avant_droite(vitesse_d)
        moteur_avant_gauche(vitesse_g)
        print("a:", a)
        print("b:", b)
        print(vitesse_d)
        print(vitesse_g)
        # time.sleep(0.01) #attendre 10ms
        # erreur_d= (vitesse_d - vitesse_reele_d)*erreur_lin_PID
        # erreur_g= (vitesse_g - vitesse_reele_g)*erreur_lin_PID
        # moteur_avant_gauche(vitesse_d+erreur_d)
        # moteur_avant_droite(vitesse_g+erreur_g)

        # moteur_avant_droite(15*0.8)
        # moteur_avant_gauche(15)

        #(vitesse_d, vitesse_g) = pid(vitesse_g, vitesse_reele_g, vitesse_d, vitesse_reele_d)




