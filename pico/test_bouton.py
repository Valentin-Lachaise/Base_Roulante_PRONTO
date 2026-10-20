import board
import digitalio
import time

# Bouton branche entre GP22 et GND (actif LOW)
# Pull.UP interne -> au repos True, appuye False
bouton = digitalio.DigitalInOut(board.GP22)
bouton.direction = digitalio.Direction.INPUT
bouton.pull      = digitalio.Pull.UP

print("Test bouton GP22 (Pull.UP, bouton vers GND)")
print("Valeur au repos :", bouton.value)  # doit afficher True

while True:
    print("bouton =", bouton.value)
    time.sleep(0.2)
