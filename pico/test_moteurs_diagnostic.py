import board
import digitalio
import pwmio
import time

# Test diagnostic moteur droit vs gauche
# Observe quel moteur tourne a chaque etape

dir_pin_droite = digitalio.DigitalInOut(board.GP14)
dir_pin_droite.direction = digitalio.Direction.OUTPUT
dir_pin_droite.value = True

dir_pin_gauche = digitalio.DigitalInOut(board.GP15)
dir_pin_gauche.direction = digitalio.Direction.OUTPUT
dir_pin_gauche.value = True

en_pin_droite = pwmio.PWMOut(board.GP16, frequency=20000)
en_pin_gauche = pwmio.PWMOut(board.GP17, frequency=20000)

def droite(v):
    v = max(-100, min(100, v))
    en_pin_droite.duty_cycle = 32768 + int((v / 100.0) * 32767)

def gauche(v):
    v = max(-100, min(100, v))
    en_pin_gauche.duty_cycle = 32768 + int((v / 100.0) * 32767)

def stop():
    droite(0)
    gauche(0)

print("Etape 1 : DROIT AVANT 30% - gauche arrete")
droite(30)
gauche(0)
time.sleep(3)
stop()
time.sleep(1)

print("Etape 2 : GAUCHE AVANT 30% - droit arrete")
droite(0)
gauche(30)
time.sleep(3)
stop()
time.sleep(1)

print("Etape 3 : DROIT ARRIERE 30%")
droite(-30)
gauche(0)
time.sleep(3)
stop()
time.sleep(1)

print("Etape 4 : GAUCHE ARRIERE 30%")
droite(0)
gauche(-30)
time.sleep(3)
stop()
time.sleep(1)

print("Etape 5 : LES DEUX AVANT 30%")
droite(30)
gauche(30)
time.sleep(3)
stop()

print("Termine")
