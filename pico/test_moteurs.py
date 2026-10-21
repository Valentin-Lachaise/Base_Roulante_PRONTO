import board
import digitalio
import pwmio
import time

# --- PmodDHB1 : mode anti-phase ---
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


# ============================================================
# ETAPE 0 : Validation du principe pull-down
# GP14/GP15 a LOW = moteurs desactives meme avec commande pleine vitesse
# Si les moteurs ne bougent pas pendant ce test -> les resistances hardware
# pull-down sur GP14/GP15 resoudront le probleme au boot
# ============================================================

print("=== ETAPE 0 : test pull-down (moteurs doivent rester immobiles) ===")
dir_pin_droite.value = False   # simule l'etat LOW au boot
dir_pin_gauche.value = False
_pwm_droite(100)               # commande pleine vitesse malgre tout
_pwm_gauche(100)
time.sleep(3)
stop()
dir_pin_droite.value = True    # re-active les moteurs
dir_pin_gauche.value = True
print("Si les moteurs n'ont pas bouge -> pull-down hardware va marcher")
time.sleep(2)


# ============================================================
# ETAPE 1 : Trouver la dead zone SUR LE SOL
# Place le robot sur le sol et note la premiere valeur
# ou les deux roues tournent. C'est ta DEAD_ZONE.
# ============================================================

DEAD_ZONE = 24   # <-- a ajuster apres etape 1

# print("=== ETAPE 1 : calibration dead zone ===")
# print("Pose le robot sur le sol.")
# print("Note la premiere valeur ou les roues tournent.")
# time.sleep(3)

# for v in range(5, 40):
#     print("vitesse:", v, "%")
#     _pwm_droite(v)
#     _pwm_gauche(v)
#     time.sleep(1)

# stop()
# time.sleep(2)


# ============================================================
# ETAPE 2 : Test macro-PWM a differentes vitesses lentes
# Modifie DEAD_ZONE avec la valeur trouvee a l'etape 1
# ============================================================

PERIODE_MS = 50   # duree d'un cycle macro en ms (essaie 50, 100, 150)

def avancer_lent(vitesse_voulue, duree_s):
    # vitesse_voulue : 0-100 (peut etre en dessous de DEAD_ZONE)
    print("vitesse voulue:", vitesse_voulue, "%  (dead zone:", DEAD_ZONE, "%)")
    t_fin = time.monotonic() + duree_s

    while time.monotonic() < t_fin:
        if vitesse_voulue >= DEAD_ZONE:
            _pwm_droite(vitesse_voulue)
            _pwm_gauche(vitesse_voulue)
            time.sleep(PERIODE_MS / 1000)
        else:
            ratio = vitesse_voulue / DEAD_ZONE
            t_on  = PERIODE_MS * ratio / 1000
            t_off = PERIODE_MS * (1 - ratio) / 1000
            _pwm_droite(DEAD_ZONE)
            _pwm_gauche(DEAD_ZONE)
            time.sleep(t_on)
            stop()
            time.sleep(t_off)

    stop()


print("=== ETAPE 2 : test macro-PWM ===")
print("Modifie DEAD_ZONE dans le code avec la valeur trouvee a l'etape 1")
time.sleep(3)

# Test a differentes vitesses effectives
for vitesse in [DEAD_ZONE, 10, 7, 5, 3]:
    print("--- avancer a", vitesse, "% pendant 3s ---")
    avancer_lent(vitesse, 3)
    time.sleep(1)

print("=== FIN ===")
