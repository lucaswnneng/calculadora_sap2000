import numpy as np

def vetor_unit(v):
    return v / np.linalg.norm(v)

def plano_base(p1, p2, p3):
    """
    Cria base ortonormal no plano definido por 3 pontos
    """
    v1 = p2 - p1
    v2 = p3 - p1

    normal = vetor_unit(np.cross(v1, v2))
    e1 = vetor_unit(v1)
    e2 = vetor_unit(np.cross(normal, e1))

    return p1, e1, e2

def projetar_ponto(ponto, origem, e1, e2):
    """
    Projeta ponto 3D no plano → coordenadas 2D
    """
    v = ponto - origem
    return np.array([np.dot(v, e1), np.dot(v, e2)])

class Plano_camera:
    def __init__(self, p1, p2, p3):
        self.origem, self.e1, self.e2 = plano_base(p1, p2, p3)

    def projetar(self, ponto):
        return projetar_ponto(ponto, self.origem, self.e1, self.e2)