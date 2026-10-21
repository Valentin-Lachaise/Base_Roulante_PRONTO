import serial
import numpy as np
import cv2

PORT = "COM8" 
BAUD = 921600 
WIDTH, HEIGHT = 40, 30 

ser = serial.Serial(PORT, BAUD, timeout=1)

while True:
    line = ser.readline().decode(errors='ignore').strip()
    if line == "P5":
        ser.readline() # saute les dimensions
        ser.readline() # saute "255"
        
        data = ser.read(WIDTH * HEIGHT)
        if len(data) == WIDTH * HEIGHT:
            # Lecture des 4 valeurs envoyées par la Pico
            a_pico = ser.readline().decode(errors='ignore').strip()
            b_pico = ser.readline().decode(errors='ignore').strip()
            print(f"Valeurs Pico: a={a_pico}, b={b_pico}")
            
            vitesse_d_pico = ser.readline().decode(errors='ignore').strip()
            vitesse_g_pico = ser.readline().decode(errors='ignore').strip()
            print(f"Valeurs Pico: vitesse_d={vitesse_d_pico}, vitesse_g={vitesse_g_pico}")

            # Reconstitution de l'image et rotation
            img = np.frombuffer(data, dtype=np.uint8).reshape((HEIGHT, WIDTH))
            rotated_img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            # --- REDRESSEMENT DE L'IMAGE (BIRD'S EYE VIEW) ---
            # X centre = 15. Largeur max = 30. Hauteur max = 40.
            
            pts_source = np.float32([
                [8, 0],   [22, 0],  # Haut (lointain) : zone rétrécie (ajuster ces deux valeurs)
                [0, 40],  [30, 40]  # Bas (proche) : pleine largeur
            ])
            
            pts_dest = np.float32([
                [0, 0],   [30, 0],  # Haut : étiré à la largeur totale (30)
                [0, 40],  [30, 40]  # Bas : reste identique
            ])
            
            matrice = cv2.getPerspectiveTransform(pts_source, pts_dest)
            
            # Application de la transformation avec la taille de sortie correcte (30x40)
            img_redressee = cv2.warpPerspective(rotated_img, matrice, (30, 40))

            # Binarisation et affichage
            _, binary_img = cv2.threshold(img_redressee, 120, 255, cv2.THRESH_BINARY)
            
            # Agrandissement pour l'affichage (ratio 30x40 conservé -> 480x640)
            show_img = cv2.resize(binary_img, (480, 640), interpolation=cv2.INTER_NEAREST)
            cv2.imshow("OV7670 Vue de dessus", show_img)
            # # Binarisation
            # _, binary_img = cv2.threshold(rotated_img, 120, 255, cv2.THRESH_BINARY)

            # # Agrandissement corrigé (Largeur=480, Hauteur=640)
            # show_img = cv2.resize(binary_img, (480, 640), interpolation=cv2.INTER_NEAREST)
            # cv2.imshow("OV7670 High Res", show_img)
            
            # VIDER LE BUFFER : Empêche le décalage et le retard d'image
            ser.reset_input_buffer()
            
    if cv2.waitKey(1) & 0xFF == 27:
        break

ser.close()
cv2.destroyAllWindows()