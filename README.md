# 🤖 Nom de ton Robot | Projet d'Ingénierie - IMT Atlantique
> Un système robotique complet basé sur Raspberry Pi Pico, conçu et fabriqué sur le campus de Nantes.

---

## 📋 Présentation du Projet
Ce projet documente la conception de A à Z d'un robot [Type de robot : mobile, bras, etc.]. 
L'objectif est de proposer une plateforme open-source alliant découpe laser, impression 3D et contrôle en Python.

## 🛠 Spécifications Techniques
* **Contrôleur :** Raspberry Pi Pico (RP2040)
* **Langage :** MicroPython / Python 3
* **Vision :** Caméra [Modèle]
* **Structure :** Châssis en [Matière] découpé au laser.

---

## 📂 Ressources de Fabrication

### 1. Conception Mécanique (CAD)
Les fichiers sont disponibles dans le dossier `/cad`.
* `Robot_Assembly.SLDASM` : Fichier assemblage SolidWorks.
* `Robot_Full.STEP` : Format universel pour consultation.

### 2. Découpe Laser
Les plans ont été tracés sous Inkscape.
* `Chassis_Plan.svg` : Prêt pour la découpe (Calques séparés pour gravure/découpe).

### 3. Électronique & Nomenclature (BOM)
| Composant | Quantité | Rôle |
| :--- | :--- | :--- |
| RPi Pico | 1 | Cerveau du robot |
| Drivers [Nom] | 2 | Contrôle moteurs |
| Moteurs [Nom] | 2 | Propulsion |
| Vis M3 | 20 | Assemblage |

---

## 💻 Installation et Code
Le code source se trouve dans `/src`. Pour lancer le robot :
1. Flasher le firmware MicroPython sur la Pico.
2. Téléverser le fichier `main.py`.
```python
# Extrait du code de contrôle moteur
import machine
pwm = machine.PWM(machine.Pin(15))
pwm.freq(1000)
