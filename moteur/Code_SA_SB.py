#coloration des fils:
#brun: ground
#rouge: 3.3V
#orange: GP1, EN
#vert: GP0, DIR
import board
import digitalio
import pwmio
import rotaryio
import time

# --- Configuration des broches ---
# DIR sur GP0
dir_pin = digitalio.DigitalInOut(board.GP0)
dir_pin.direction = digitalio.Direction.OUTPUT

# --- Configuration Encodeur ---
# rotaryio gère automatiquement SA (GP2) et SB (GP3)
encodeur = rotaryio.IncrementalEncoder(board.GP2, board.GP3)


# EN sur GP1 (PWM)
# La fréquence est fixée à 1000 Hz
en_pin = pwmio.PWMOut(board.GP1, frequency=1000)

# --- Fonctions de pilotage ---

def moteur_avant(vitesse):
    """Vitesse de 0 à 100"""
    dir_pin.value = True
    # CircuitPython utilise un cycle de service sur 16 bits (0 à 65535)
    en_pin.duty_cycle = int(vitesse * 65535 / 100)

def moteur_arriere(vitesse):
    """Vitesse de 0 à 100"""
    dir_pin.value = False
    en_pin.duty_cycle = int(vitesse * 65535 / 100)

def moteur_stop():
    en_pin.duty_cycle = 0

# --- Test ---
moteur_avant(50) # Lance le moteur à 50%
derniere_position = 0

try:
    for _ in range(100): # Test pendant environ 5 secondes
        position_actuelle = encodeur.position
        vitesse_relative = position_actuelle - derniere_position
        
        print(f"Position: {position_actuelle} | Delta: {vitesse_relative}")
        
        derniere_position = position_actuelle
        time.sleep(0.1)
finally:
    moteur_stop() # Sécurité : arrêt du moteur