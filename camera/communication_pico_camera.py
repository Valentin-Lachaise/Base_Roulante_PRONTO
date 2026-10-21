import board
import busio
import adafruit_ov7670
import usb_cdc
import time
import pwmio



# 1. Horloge maître
xclk = pwmio.PWMOut(board.GP11, frequency=24_000_000, duty_cycle=32768)
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
except Exception as e:
    print(f"Erreur : {e}")
    while True: time.sleep(1)

width, height = 160, 120
raw_buf = bytearray(width * height * 2)
gray_buf = bytearray(width * height)
serial = usb_cdc.console

while True:
    cam.capture(raw_buf)

    # Extraction optimisée
    for i in range(width * height):
        gray_buf[i] = raw_buf[i * 2]

    # Envoi au Viewer avec les nouvelles dimensions
    serial.write(b"P5\n160 120\n255\n")
    serial.write(gray_buf)
