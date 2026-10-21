import serial
import serial.tools.list_ports
import numpy as np
import cv2

# --- CONFIG ---
PORT = "COM8"    # changer si besoin (voir Gestionnaire de peripheriques)
BAUD = 921600
WIDTH, HEIGHT = 40, 30

def find_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        desc = p.description.lower()
        if "circuitpython" in desc or "pico" in desc or "usb serial" in desc:
            print(f"Pico detecte sur {p.device} ({p.description})")
            return p.device
    print(f"Pico non detecte automatiquement, utilisation de {PORT}")
    print("Ports disponibles :")
    for p in ports:
        print(f"  {p.device} - {p.description}")
    return PORT

ser = serial.Serial(find_port(), BAUD, timeout=1)
print("Connecte. En attente d'images...")
print("Appuyez sur Echap pour quitter.")

while True:
    # Lecture du header PGM (3 lignes : "P5", "40 30", "255")
    line = ser.readline().decode(errors='ignore').strip()
    if line != "P5":
        continue

    ser.readline()  # "40 30"
    ser.readline()  # "255"

    data = ser.read(WIDTH * HEIGHT)
    if len(data) != WIDTH * HEIGHT:
        print(f"Trame incomplete ({len(data)}/{WIDTH * HEIGHT})")
        ser.reset_input_buffer()
        continue

    # Image brute (telle que capturee par la camera)
    img_brute = np.frombuffer(data, dtype=np.uint8).reshape((HEIGHT, WIDTH))

    # Flip horizontal pour affichage uniquement (image miroir corrigee visuellement)
    # Ne pas appliquer ce flip dans le code Pico - la regression.py gere deja le miroir
    img_brute = cv2.flip(img_brute, 1)

    # Binarisation de l'image brute (camera en paysage, plus de rotation)
    _, img_bin = cv2.threshold(img_brute, 128, 255, cv2.THRESH_BINARY)

    # --- Agrandissement pour affichage ---
    scale = 12
    img_brute_show = cv2.resize(img_brute, (WIDTH * scale, HEIGHT * scale), interpolation=cv2.INTER_NEAREST)
    img_bin_show   = cv2.resize(img_bin,   (WIDTH * scale, HEIGHT * scale), interpolation=cv2.INTER_NEAREST)

    # Annotations
    # Bas de l'image = pres du robot (j=height-1), haut = loin (j=0)
    # Gauche = gauche robot (i=0), droite = droite robot (i=width-1)
    cv2.putText(img_brute_show, "LOIN (j=0)",
                (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 128, 1)
    cv2.putText(img_brute_show, "PRES DU ROBOT (j=29)",
                (5, HEIGHT * scale - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 128, 1)
    cv2.putText(img_brute_show, "GAUCHE",
                (5, HEIGHT * scale // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, 128, 1)
    cv2.putText(img_brute_show, "DROITE",
                (WIDTH * scale - 80, HEIGHT * scale // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, 128, 1)

    # Ligne centrale (centre lateral = u=0)
    cx = WIDTH * scale // 2
    cv2.line(img_brute_show, (cx, 0), (cx, HEIGHT * scale), 128, 1)
    cv2.line(img_bin_show,   (cx, 0), (cx, HEIGHT * scale), 128, 1)

    cv2.imshow("1. Image BRUTE (camera paysage)", img_brute_show)
    cv2.imshow("2. Image BINARISEE", img_bin_show)

    # Vider le buffer pour eviter le retard
    ser.reset_input_buffer()

    if cv2.waitKey(1) & 0xFF == 27:
        break

ser.close()
cv2.destroyAllWindows()
