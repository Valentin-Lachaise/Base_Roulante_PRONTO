
def mat_to_list(mat):
    n = len(mat)
    list = []
    for i in range(n):
        for j in range(n):
            if mat[i][j]==0 :
                #on centre les axes au milieu de l'image
                #(       ^        )
                #(       |        )
                #(       |        )
                #( ------|------> )
                #        0
                list.append((n-i, j-int(n/2)))
    return list

def variance(x):
    n = len(x)
    if n == 0:
        raise ValueError("La liste est vide")
    m = sum(x) / n
    return sum((xi - m) ** 2 for xi in x) / n

def covariance(x, y):
    if len(x) != len(y):
        raise ValueError("Les listes doivent avoir la même longueur")
    n = len(x)
    if n == 0:
        raise ValueError("Les listes sont vides")
    mx = sum(x) / n
    my = sum(y) / n
    return sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / n

def moyenne(x):
    n = len(x)
    return sum(x)/n


def reg_lin(mat):
    l = mat_to_list(mat)
    if(len(l)!=0):
        (x, y) = zip(*l) #unzip list to two lists
        if(variance(x) !=0):
            a = covariance(x, y) / variance(x)
        else:
            return 0, 0
        b = moyenne(y) - a*moyenne(x)
        
    #la regression linéaire calculée est a*x + b
        return (a, b) 
    return 0, 0



