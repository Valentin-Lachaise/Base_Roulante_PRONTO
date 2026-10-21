#coloration des fils:
#brun: ground
#rouge: 3.3V
#orange: GP1, EN
#vert: GP0, DIR
import board
import digitalio
import pwmio
import time
import rotaryio

#GP1 à 13 utilisés par la camera, utiliser GP14-17
# --- Configuration des broches ---
# DIR Droite sur GP13
dir_pin_droite = digitalio.DigitalInOut(board.GP14)
dir_pin_droite.direction = digitalio.Direction.OUTPUT

# DIR Gauche sur GP14
dir_pin_gauche = digitalio.DigitalInOut(board.GP15)
dir_pin_gauche.direction = digitalio.Direction.OUTPUT

# La fréquence est fixée à 10000 Hz
# EN droite sur GP15 (PWM)
en_pin_droite = pwmio.PWMOut(board.GP16, frequency=10000)
# EN gauche sur GP16 (PWM)
en_pin_gauche = pwmio.PWMOut(board.GP17, frequency=10000)


#utiliser 18-21 pour les SA et SB, a setup si besoin
encodeur_g = rotaryio.IncrementalEncoder(board.GP18, board.GP19)
encodeur_d = rotaryio.IncrementalEncoder(board.GP20, board.GP21)

# --- Fonctions de pilotage droite ---

def pos_droite():
    return encodeur_d.position

def moteur_avant_droite(vitesse):
    """Vitesse de 0 à 100"""
    dir_pin_droite.value = True
    # CircuitPython utilise un cycle de service sur 16 bits (0 à 65535)
    en_pin_droite.duty_cycle = int(vitesse * 65535 / 100)

def moteur_arriere_droite(vitesse):
    """Vitesse de 0 à 100"""
    dir_pin_droite.value = False
    en_pin_droite.duty_cycle = int(vitesse * 65535 / 100)

def moteur_stop_droite():
    en_pin_droite.duty_cycle = 0
    
# --- Fonctions de pilotage gauche ---

def pos_gauche():
    return encodeur_g.position

def moteur_avant_gauche(vitesse):
    """Vitesse de 0 à 100"""
    dir_pin_gauche.value = True
    # CircuitPython utilise un cycle de service sur 16 bits (0 à 65535)
    en_pin_gauche.duty_cycle = int(vitesse * 65535 / 100)

def moteur_arriere_gauche(vitesse):
    """Vitesse de 0 à 100"""
    dir_pin_gauche.value = False
    en_pin_gauche.duty_cycle = int(vitesse * 65535 / 100)

def moteur_stop_gauche():
    en_pin_gauche.duty_cycle = 0

# --- Test ---

moteur_avant_droite(80)
time.sleep(3)
moteur_stop_droite()

moteur_avant_gauche(80)
time.sleep(3)
moteur_stop_gauche()


