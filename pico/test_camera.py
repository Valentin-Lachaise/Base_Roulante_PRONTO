import board
import busio
import adafruit_ov7670
import usb_cdc
import time
import pwmio

# Lance ce fichier, ouvre un terminal serie (115200 bauds) et lance le viewer Python
# sur ton PC pour voir l'image en direct et verifier l'orientation.

xclk = pwmio.PWMOut(board.GP11, frequency=10_000_000, duty_cycle=32768)
time.sleep(0.5)

i2c = busio.I2C(board.GP9, board.GP8)

try:
    cam = adafruit_ov7670.OV7670(
        i2c,
        [board.GP0, board.GP1, board.GP2, board.GP3, board.GP4, board.GP5, board.GP6, board.GP7],
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
raw_buf = bytearray(width * height * 2)
gray_buf = bytearray(width * height)
serial = usb_cdc.console

seuil_dynamique = 0
ecart_minimum = 90

print("Camera OK - envoi images en continu")

while True:
    cam.capture(raw_buf)

    val_min = 255
    val_max = 0
    idx = 0
    for i in range(0, width * height * 2, 2):
        val = raw_buf[i]
        if val < val_min:
            val_min = val
        elif val > val_max:
            val_max = val
        gray_buf[idx] = 0 if val <= seuil_dynamique else 255
        idx += 1

    ecart = val_max - val_min
    if ecart > ecart_minimum:
        seuil_dynamique = val_min + int(ecart * 0.5)
    else:
        seuil_dynamique = -1

    # Envoi image brute (niveaux de gris) en PGM sur le port serie
    # Format : P5 largeur hauteur valeur_max données
    if serial:
        serial.write(b"P5\n40 30\n255\n")
        serial.write(gray_buf)
