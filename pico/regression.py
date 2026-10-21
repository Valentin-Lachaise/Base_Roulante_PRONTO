def reg_lin_pico(buffer, width, height):
    n = sum_x = sum_y = sum_xx = sum_xy = 0

    # Camera en paysage (non rotee 90deg), flip_y=True :
    #   i (colonne, 0..width-1)  = axe LATERAL  (i=0=gauche, i=width-1=droite) [confirme]
    #   j (ligne,   0..height-1) = axe PROFONDEUR (j=0=loin, j=height-1=pres du robot) [avec flip_y]
    #
    # Regression : u = a*v + b
    #   u = position laterale centree   : 0=milieu, <0=gauche, >0=droite
    #   v = profondeur depuis le robot  : 0=pres (j=height-1), height-1=loin (j=0)
    #   a = angle de la ligne
    #   b = decalage lateral au pied du robot (v=0 = bas de l'image = pres du robot)
    #   -> a=0 et b=0 quand le robot est centre sur une ligne droite

    centre_u = (width - 1) / 2.0   # centre lateral (i=19.5 pour width=40)

    marge_i = 3          # exclure les bords lateraux (ligne parasite sur le bord)
    marge_j_pres = 2     # exclure les lignes trop proches (sous la camera)
    marge_j_loin = 2     # exclure les lignes les plus lointaines (bruit)

    for j in range(marge_j_loin, height - marge_j_pres):
        for i in range(marge_i, width - marge_i):
            if buffer[i + width * j] == 0:
                v = height - 1 - j     # profondeur : 0=pres (j=height-1), max=loin (j=0)
                u = centre_u - i       # lateral centre : <0=gauche, >0=droite (image miroir H)

                n += 1
                sum_x += v
                sum_y += u
                sum_xx += v * v
                sum_xy += v * u

    if n < 2:
        return 0, 0

    denominateur = n * sum_xx - sum_x * sum_x
    if denominateur == 0:
        return 0, 0

    a = (n * sum_xy - sum_x * sum_y) / denominateur
    b = (sum_y - a * sum_x) / n

    return a, b
