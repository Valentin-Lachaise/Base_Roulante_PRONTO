"""
Viewer PC pour verifier l'orientation de la camera.
Lance test_camera.py sur le Pico, puis lance ce script sur le PC.

Dependances : pip install pyserial pillow
"""

import serial
import serial.tools.list_ports
from PIL import Image, ImageTk
import tkinter as tk
import struct

WIDTH = 40
HEIGHT = 30
FRAME_SIZE = WIDTH * HEIGHT
HEADER = b"P5\n40 30\n255\n"

def find_pico_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if "USB Serial" in p.description or "Pico" in p.description or "CircuitPython" in p.description:
            return p.device
    # Si pas trouve automatiquement, lister les ports disponibles
    print("Ports disponibles :")
    for p in ports:
        print(f"  {p.device} - {p.description}")
    return input("Entrez le port COM (ex: COM3) : ").strip()

def main():
    port = find_pico_port()
    print(f"Connexion sur {port}...")

    ser = serial.Serial(port, 115200, timeout=2)
    print("Connecte. Attente images...")

    root = tk.Tk()
    root.title("Viewer camera - verifiez orientation")
    root.geometry(f"{WIDTH*8}x{HEIGHT*8+60}")

    label_img = tk.Label(root)
    label_img.pack()

    info = tk.Label(root, text="", font=("Courier", 10), justify="left")
    info.pack()

    img_ref = [None]

    def read_frame():
        # Chercher le header PGM dans le flux
        buf = b""
        while True:
            byte = ser.read(1)
            if not byte:
                root.after(50, read_frame)
                return
            buf += byte
            if buf.endswith(HEADER):
                break
            if len(buf) > len(HEADER) * 2:
                buf = buf[-len(HEADER):]

        # Lire les pixels
        data = ser.read(FRAME_SIZE)
        if len(data) != FRAME_SIZE:
            root.after(50, read_frame)
            return

        img = Image.frombytes("L", (WIDTH, HEIGHT), bytes(data))
        img_big = img.resize((WIDTH * 8, HEIGHT * 8), Image.NEAREST)

        tk_img = ImageTk.PhotoImage(img_big)
        label_img.config(image=tk_img)
        img_ref[0] = tk_img

        val_min = min(data)
        val_max = max(data)
        noirs = sum(1 for p in data if p == 0)
        info.config(text=f"min={val_min}  max={val_max}  pixels noirs={noirs}/{FRAME_SIZE}")

        root.after(100, read_frame)

    root.after(100, read_frame)
    root.mainloop()
    ser.close()

if __name__ == "__main__":
    main()
