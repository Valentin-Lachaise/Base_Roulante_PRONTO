# main.py sur la Pico W pour le test de vitesse des moteurs
# Ce script augmente progressivement la vitesse des moteurs et mesure la vitesse réelle via des encodeurs.
# Version finale corrigée pour CircuitPython (time.monotonic et usb_cdc)

import time
import math
import digitalio
import pwmio
import rotaryio
import board
import usb_cdc

# --- Configuration des broches (reprise de code.py) ---
# Moteur Droit
dir_pin_droite = digitalio.DigitalInOut(board.GP14)
dir_pin_droite.direction = digitalio.Direction.OUTPUT
en_pin_droite = pwmio.PWMOut(board.GP16, frequency=10000)

# Moteur Gauche
dir_pin_gauche = digitalio.DigitalInOut(board.GP15)
dir_pin_gauche.direction = digitalio.Direction.OUTPUT
en_pin_gauche = pwmio.PWMOut(board.GP17, frequency=10000)

# Encodeurs
encodeur_g = rotaryio.IncrementalEncoder(board.GP19, board.GP18)
encodeur_d = rotaryio.IncrementalEncoder(board.GP20, board.GP21)


# --- Paramètres de calcul de vitesse ---
# À ajuster selon votre matériel
TICKS_PAR_TOUR = 480  # Nombre de ticks de l'encodeur pour un tour de roue
DIAMETRE_ROUE_CM = 6.5  # Diamètre de la roue en cm
PERIMETRE_ROUE_CM = DIAMETRE_ROUE_CM * math.pi


# --- Fonctions de contrôle moteur (exactement comme dans code.py) ---

def pos_droite():
    return encodeur_d.position

def moteur_avant_droite(vitesse):
    vitesse = max(0, min(100, vitesse))
    dir_pin_droite.value = True # Activation de la puce
    en_pin_droite.duty_cycle = 32768 + int((vitesse / 100.0) * 32767)

def moteur_arriere_droite(vitesse):
    vitesse = max(0, min(100, vitesse))
    dir_pin_droite.value = True
    en_pin_droite.duty_cycle = 32768 - int((vitesse / 100.0) * 32768)

def moteur_stop_droite():
    dir_pin_droite.value = True
    en_pin_droite.duty_cycle = 32768 # Point mort

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


# --- Boucle Principale ---
# CORRECTION: Utiliser usb_cdc.console pour la communication série en CircuitPython
serial = usb_cdc.console

serial.write(b"Debut du test des moteurs dans 5 secondes...\n")
time.sleep(5)
serial.write(b"Test en cours...\n")

# Sauvegarder la position initiale des encodeurs
last_pos_d = pos_droite()
last_pos_g = pos_gauche()
last_time = time.monotonic()

# Boucle pour augmenter la consigne de vitesse de 0 à 100
for consigne in range(0, 101, 5):
    
    moteur_avant_droite(consigne)
    moteur_avant_gauche(consigne)
    
    time.sleep(0.2)
    
    # --- Calcul de la vitesse réelle ---
    current_time = time.monotonic()
    delta_t = current_time - last_time
    last_time = current_time
    
    current_pos_d = pos_droite()
    current_pos_g = pos_gauche()
    
    delta_ticks_d = current_pos_d - last_pos_d
    delta_ticks_g = current_pos_g - last_pos_g
    
    last_pos_d = current_pos_d
    last_pos_g = current_pos_g
    
    vitesse_reelle_d = 0
    vitesse_reelle_g = 0
    
    if delta_t > 0:
        tours_par_sec_d = (delta_ticks_d / TICKS_PAR_TOUR) / delta_t
        tours_par_sec_g = (delta_ticks_g / TICKS_PAR_TOUR) / delta_t
        
        vitesse_reelle_d = tours_par_sec_d * PERIMETRE_ROUE_CM
        vitesse_reelle_g = tours_par_sec_g * PERIMETRE_ROUE_CM

    # CORRECTION: Envoyer les données via serial.write, encodées en bytes avec une nouvelle ligne
    data_string = f"D:{consigne},{vitesse_reelle_d:.2f};G:{consigne},{vitesse_reelle_g:.2f}\n"
    serial.write(data_string.encode('utf-8'))

# Arrêter les moteurs à la fin du test
moteur_stop_droite()
moteur_stop_gauche()
serial.write(b"Test termine.\n")# main.py sur la Pico W pour le test de vitesse des moteurs
# Ce script augmente progressivement la vitesse des moteurs et mesure la vitesse réelle via des encodeurs.
# Version finale corrigée pour CircuitPython (time.monotonic et usb_cdc)

import time
import math
import digitalio
import pwmio
import rotaryio
import board
import usb_cdc

# --- Configuration des broches (reprise de code.py) ---
# Moteur Droit
dir_pin_droite = digitalio.DigitalInOut(board.GP14)
dir_pin_droite.direction = digitalio.Direction.OUTPUT
en_pin_droite = pwmio.PWMOut(board.GP16, frequency=10000)

# Moteur Gauche
dir_pin_gauche = digitalio.DigitalInOut(board.GP15)
dir_pin_gauche.direction = digitalio.Direction.OUTPUT
en_pin_gauche = pwmio.PWMOut(board.GP17, frequency=10000)

# Encodeurs
encodeur_g = rotaryio.IncrementalEncoder(board.GP19, board.GP18)
encodeur_d = rotaryio.IncrementalEncoder(board.GP20, board.GP21)


# --- Paramètres de calcul de vitesse ---
# À ajuster selon votre matériel
TICKS_PAR_TOUR = 480  # Nombre de ticks de l'encodeur pour un tour de roue
DIAMETRE_ROUE_CM = 6.5  # Diamètre de la roue en cm
PERIMETRE_ROUE_CM = DIAMETRE_ROUE_CM * math.pi


# --- Fonctions de contrôle moteur (exactement comme dans code.py) ---

def pos_droite():
    return encodeur_d.position

def moteur_avant_droite(vitesse):
    vitesse = max(0, min(100, vitesse))
    dir_pin_droite.value = True # Activation de la puce
    en_pin_droite.duty_cycle = 32768 + int((vitesse / 100.0) * 32767)

def moteur_arriere_droite(vitesse):
    vitesse = max(0, min(100, vitesse))
    dir_pin_droite.value = True
    en_pin_droite.duty_cycle = 32768 - int((vitesse / 100.0) * 32768)

def moteur_stop_droite():
    dir_pin_droite.value = True
    en_pin_droite.duty_cycle = 32768 # Point mort

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


# --- Boucle Principale ---
# CORRECTION: Utiliser usb_cdc.console pour la communication série en CircuitPython
serial = usb_cdc.console

serial.write(b"Debut du test des moteurs dans 5 secondes...\n")
time.sleep(5)
serial.write(b"Test en cours...\n")

# Sauvegarder la position initiale des encodeurs
last_pos_d = pos_droite()
last_pos_g = pos_gauche()
last_time = time.monotonic()

# Boucle pour augmenter la consigne de vitesse de 0 à 100
for consigne in range(0, 101, 5):
    
    moteur_avant_droite(consigne)
    moteur_avant_gauche(consigne)
    
    time.sleep(0.2)
    
    # --- Calcul de la vitesse réelle ---
    current_time = time.monotonic()
    delta_t = current_time - last_time
    last_time = current_time
    
    current_pos_d = pos_droite()
    current_pos_g = pos_gauche()
    
    delta_ticks_d = current_pos_d - last_pos_d
    delta_ticks_g = current_pos_g - last_pos_g
    
    last_pos_d = current_pos_d
    last_pos_g = current_pos_g
    
    vitesse_reelle_d = 0
    vitesse_reelle_g = 0
    
    if delta_t > 0:
        tours_par_sec_d = (delta_ticks_d / TICKS_PAR_TOUR) / delta_t
        tours_par_sec_g = (delta_ticks_g / TICKS_PAR_TOUR) / delta_t
        
        vitesse_reelle_d = tours_par_sec_d * PERIMETRE_ROUE_CM
        vitesse_reelle_g = tours_par_sec_g * PERIMETRE_ROUE_CM

    # CORRECTION: Envoyer les données via serial.write, encodées en bytes avec une nouvelle ligne
    data_string = f"D:{consigne},{vitesse_reelle_d:.2f};G:{consigne},{vitesse_reelle_g:.2f}\n"
    serial.write(data_string.encode('utf-8'))

# Arrêter les moteurs à la fin du test
moteur_stop_droite()
moteur_stop_gauche()
serial.write(b"Test termine.\n")