import board
import busio
import adafruit_ov7670
import usb_cdc
import time
import digitalio
import pwmio
import rotaryio

#------------------------SETUP PARAMÈTRES----------------------

vitesse_prec_d = 12
vitesse_prec_g = 12
erreur_lin_PID = 0.5
ampli_angle = 10
ampli_decalage = 0.1

#------------------------LOGIQUE DOUBLE ZONE----------------------

def calcul_zones_pico(buffer, width, height):
    # Zone PROCHE (Bas de l'image, lignes 20 à 25) -> Erreur immédiate
    somme_i_proche = nb_proche = 0
    # Zone LOINTAINE (Milieu/Haut, lignes 5 à 10) -> Anticipation
    somme_i_loin = nb_loin = 0
    
    centre_i = width // 2
    
    for j in range(5, 26):
        # On ne traite que les deux bandes horizontales
        if (5 <= j <= 10) or (20 <= j <= 25):
            for i in range(5, width): # Ignore la bande noire parasite du bord
                if buffer[i + width * j] == 0: # Si pixel noir
                    if j >= 20:
                        somme_i_proche += i
                        nb_proche += 1
                    else:
                        somme_i_loin += i
                        nb_loin += 1
                        
    # Calcul des erreurs par rapport au centre (i)
    err_p = (somme_i_proche / nb_proche) - centre_i if nb_proche > 0 else 0
    err_l = (somme_i_loin / nb_loin) - centre_i if nb_loin > 0 else 0
    
    # On simule 'a' et 'b' pour ton viewer PC :
    # a = l'angle (différence entre loin et proche)
    # b = le décalage (erreur proche)
    return (err_l - err_p), err_p, (nb_proche + nb_loin)

#------------------------MOTEURS & ENCODEURS----------------------

dir_pin_droite = digitalio.DigitalInOut(board.GP14)
dir_pin_droite.direction = digitalio.Direction.OUTPUT
dir_pin_gauche = digitalio.DigitalInOut(board.GP15)
dir_pin_gauche.direction = digitalio.Direction.OUTPUT

en_pin_droite = pwmio.PWMOut(board.GP16, frequency=10000)
en_pin_gauche = pwmio.PWMOut(board.GP17, frequency=10000)

encodeur_g = rotaryio.IncrementalEncoder(board.GP19, board.GP18)
encodeur_d = rotaryio.IncrementalEncoder(board.GP20, board.GP21)

def moteur_avant_droite(v):
    dir_pin_droite.value = True
    en_pin_droite.duty_cycle = 32768 + int(max(0, min(100, v)) * 327.67)

def moteur_avant_gauche(v):
    dir_pin_gauche.value = True
    en_pin_gauche.duty_cycle = 32768 + int(max(0, min(100, v)) * 327.67)

def moteur_arriere_droite(v):
    dir_pin_droite.value = True
    en_pin_droite.duty_cycle = 32768 - int(max(0, min(100, v)) * 327.68)

def moteur_arriere_gauche(v):
    dir_pin_gauche.value = True
    en_pin_gauche.duty_cycle = 32768 - int(max(0, min(100, v)) * 327.68)

def moteur_stop():
    en_pin_droite.duty_cycle = 32768
    en_pin_gauche.duty_cycle = 32768

#------------------------SETUP CAMERA----------------------

xclk = pwmio.PWMOut(board.GP11, frequency=10_000_000, duty_cycle=32768)
time.sleep(0.5)
i2c = busio.I2C(board.GP9, board.GP8)

try:
    cam = adafruit_ov7670.OV7670(
        i2c, [board.GP0, board.GP1, board.GP2, board.GP3, board.GP4, board.GP5, board.GP6, board.GP7],
        board.GP10, board.GP13, board.GP12
    )
    cam.size = adafruit_ov7670.OV7670_SIZE_DIV16
    cam.colorspace = adafruit_ov7670.OV7670_COLOR_YUV
    cam.flip_y = True
    cam.gain_control = True # Réactivé pour la luminosité
    cam.exposure_control = True
except Exception as e:
    print(f"Erreur Caméra: {e}")
    while True: time.sleep(1)

width, height = 40, 30
raw_buf = bytearray(width * height * 2)
gray_buf = bytearray(width * height)
serial = usb_cdc.console

#------------------------BOUCLE PRINCIPALE----------------------

derniere_pos_g = derniere_pos_d = 0
seuil_dynamique = 110
ecart_min = 90

while True:
    cam.capture(raw_buf)

    # 1. Binarisation et seuil dynamique
    v_min, v_max, idx = 255, 0, 0
    for i in range(0, width * height * 2, 2):
        val = raw_buf[i]
        if val < v_min: v_min = val
        elif val > v_max: v_max = val
        gray_buf[idx] = 0 if val <= seuil_dynamique else 255
        idx += 1
    
    ecart = v_max - v_min
    seuil_dynamique = v_min + int(ecart * 0.5) if ecart > ecart_min else -1

    # 2. Envoi Viewer PC
    serial.write(b"P5\n30 40\n255\n")
    serial.write(gray_buf)

    # 3. Calcul des erreurs (Double Zone)
    a, b, nb_pixels = calcul_zones_pico(gray_buf, width, height)
    
    # Encodeurs
    pos_g = encodeur_g.position
    pos_d = encodeur_d.position
    vit_r_g = (pos_g - derniere_pos_g)*100/272+4
    vit_r_d = (pos_d - derniere_pos_d)*100/280+4
    derniere_pos_g, derniere_pos_d = pos_g, pos_d

    # Log pour PC (4 lignes obligatoires)
    print(f"a: {a}")
    print(f"b: {b}")
    print(vit_r_d)
    print(vit_r_g)

    # 4. Contrôle Robot
    if nb_pixels < 2: # Ligne perdue
        moteur_arriere_droite(15)
        moteur_arriere_gauche(15)
    else:
        # Pilotage par anticipation
        v_base = 20
        
        # Ralentissement si gros virage détecté au loin (a est grand)
        facteur_virage = abs(a) / 10.0
        v_base = v_base * (1.0 - min(0.4, facteur_virage))
        
        # Correction PID simplifiée sur l'erreur proche (b)
        correction = b * ampli_decalage + a * ampli_angle
        
        vit_d = v_base - correction
        vit_g = v_base + correction
        
        # PID sur vitesse réelle
        err_d = (vit_d - vit_r_d) * erreur_lin_PID
        err_g = (vit_g - vit_r_g) * erreur_lin_PID
        if vit_d >= 0:
            moteur_avant_droite(vit_d + err_d)
        else:
            moteur_arriere_droite(abs(vit_d + err_d))

        if vit_g >= 0:
            moteur_avant_gauche(vit_g + err_g)
        else:
            moteur_arriere_gauche(abs(vit_g + err_g))