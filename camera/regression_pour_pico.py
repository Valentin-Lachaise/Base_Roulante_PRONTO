def reg_lin_pico(buffer, width, height):
    n = 0
    sum_x = 0
    sum_y = 0
    sum_xx = 0
    sum_xy = 0
    
    # On centre les axes comme dans votre code
    # x_offset = height - i
    # y_offset = j - width // 2
    
    # Parcours du buffer sans créer de listes
    for j in range(height):
        for i in range(width):
            if buffer[i + width * j] <= 120: # Si point noir, on considère <=120 noir (a potentiellement modifier)
                # Application du changement de repère
                #      ^
                #      |
                #      |
                #------|------>
                #      0
                x_val = height - i
                y_val = j - (width // 2)
                
                # Accumulation pour les formules de régression
                n += 1
                sum_x += x_val
                sum_y += y_val
                sum_xx += x_val * x_val
                sum_xy += x_val * y_val

    if n < 2:
        return 0, 0

    # Calcul de la variance et covariance de manière intégrée
    # Formule : a = (n*sum_xy - sum_x*sum_y) / (n*sum_xx - sum_x^2)
    denominateur = (n * sum_xx - (sum_x ** 2))
    
    if denominateur == 0:
        return 1000, 1000 #pas de ligne sur l'image
        
    a = (n * sum_xy - sum_x * sum_y) / denominateur
    b = (sum_y - a * sum_x) / n
    
    return a, b