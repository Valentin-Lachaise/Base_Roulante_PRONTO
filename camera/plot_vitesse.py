# plot_vitesse.py sur l'ordinateur
# Version mise à jour avec les nouvelles données de test.

import matplotlib.pyplot as plt
import re

# --- Données brutes du nouveau test ---
donnees_brutes = """
D:0,0.00;G:0,0.00
D:2,0.00;G:2,0.00
D:4,0.00;G:4,0.00
D:6,0.00;G:6,0.55
D:8,1.10;G:8,1.23
D:10,1.78;G:10,1.91
D:12,2.38;G:12,2.55
D:14,3.01;G:14,3.10
D:16,3.61;G:16,3.74
D:18,4.29;G:18,4.33
D:20,4.88;G:20,4.93
D:22,5.48;G:22,5.56
D:24,6.11;G:24,6.16
D:26,6.79;G:26,6.79
D:28,7.39;G:28,7.43
D:30,8.07;G:30,8.07
D:32,8.70;G:32,8.65
D:34,9.34;G:34,9.30
D:36,9.98;G:36,9.85
D:38,10.60;G:38,10.52
D:40,11.21;G:40,11.12
D:42,11.89;G:42,11.72
D:44,12.47;G:44,12.34
D:46,13.12;G:46,12.95
D:48,13.79;G:48,13.57
D:50,14.39;G:50,14.18
D:52,15.03;G:52,14.82
D:54,15.69;G:54,15.44
D:56,16.32;G:56,16.06
D:58,16.97;G:58,16.63
D:60,17.62;G:60,17.32
D:62,18.26;G:62,17.96
D:64,18.87;G:64,18.49
D:66,19.53;G:66,19.15
D:68,20.15;G:68,19.72
D:70,20.80;G:70,20.38
D:72,21.40;G:72,21.06
D:74,22.06;G:74,21.59
D:76,22.76;G:76,22.25
D:78,23.35;G:78,22.84
D:80,23.96;G:80,23.41
D:82,24.63;G:82,24.07
D:84,25.28;G:84,24.64
D:86,25.90;G:86,25.26
D:88,26.51;G:88,25.87
D:90,27.17;G:90,26.54
D:92,27.97;G:92,27.24
D:94,28.59;G:94,27.91
D:96,29.27;G:96,28.59
D:98,30.02;G:98,29.30
D:100,30.92;G:100,30.16
"""

# Listes pour stocker les données analysées
consignes_d = []
vitesses_d = []
consignes_g = []
vitesses_g = []

print("Analyse des nouvelles donnees locales...")

# Boucle pour lire les données de la chaîne de caractères
for line in donnees_brutes.strip().split('\n'):
    data_str = line.strip()
    
    match = re.match(r"D:([\d.-]+),([\d.-]+);G:([\d.-]+),([\d.-]+)", data_str)
    if match:
        consigne_d, vitesse_d, consigne_g, vitesse_g = map(float, match.groups())
        
        consignes_d.append(consigne_d)
        vitesses_d.append(vitesse_d)
        consignes_g.append(consigne_g)
        vitesses_g.append(vitesse_g)

print(f"{len(consignes_d)} lignes de donnees analysees avec succes.")

# --- Traçage des graphiques ---
if consignes_d and consignes_g:
    print("Creation des graphiques...")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    fig.suptitle('Performance des Moteurs : Vitesse Reelle vs Consigne (Nouveau Test)')

    # Graphique pour le moteur Droit
    ax1.plot(consignes_d, vitesses_d, 'o-', label='Vitesse Reelle Droite', color='blue')
    ax1.plot([0, 100], [0, max(vitesses_d)], 'r--', label='Tendance attendue')
    ax1.set_title('Moteur Droit')
    ax1.set_ylabel('Vitesse Reelle (cm/s)')
    ax1.legend()
    ax1.grid(True)

    # Graphique pour le moteur Gauche
    ax2.plot(consignes_g, vitesses_g, 'o-', label='Vitesse Reelle Gauche', color='green')
    ax2.plot([0, 100], [0, max(vitesses_g)], 'r--', label='Tendance attendue')
    ax2.set_title('Moteur Gauche')
    ax2.set_xlabel('Consigne de Vitesse (%)')
    ax2.set_ylabel('Vitesse Reelle (cm/s)')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    plt.show()
else:
    print("Aucune donnee valide n'a ete trouvee pour tracer les graphiques.")