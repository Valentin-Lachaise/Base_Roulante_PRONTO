from moteur.Code_moteurs_droite_gauche import moteur_avant_droite, moteur_arriere_droite, moteur_arriere_gauche, moteur_avant_gauche, moteur_stop_droite, moteur_stop_gauche

def calibration(angle, decalage):

    #amelioration possible: ajouter un facteur a l'aide de la derivée de la courbe

    decalage_max = 10 #a determiner
    angle_max = 1.1#a determiner

    #les vitesses moteur initialement demandées sont les suivantes, c'est la vitesse "constante" du robot
    vitesse_constante_gauche = 30
    vitesse_constante_droite = 30 
    amplification_angle = 10 #a definir avec l'experience
    amplification_de_decalage = 0.1#amplification de décalage a determiner avec l'experience

    #on modifie la vitesse droite ou gauche pour pivoter le robot
    if(angle>angle_max):
        vitesse_constante_gauche += amplification_angle*(angle)

    if(-angle>angle_max):
        vitesse_constante_droite += amplification_angle*(angle)

    if(decalage>decalage_max):
        vitesse_constante_gauche += decalage*amplification_de_decalage

    if(-decalage>decalage_max):
        vitesse_constante_droite += (decalage)*amplification_de_decalage

    #on renvoie les vitesses demandées, puis a l'aide de la vitesse réelle, le code "main" atteint la vitesse requise
    return vitesse_constante_droite, vitesse_constante_gauche