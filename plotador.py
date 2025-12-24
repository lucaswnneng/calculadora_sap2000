import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sap_para_df import sap_para_df

# ===============================
# FUNÇÕES GEOMÉTRICAS
# ===============================

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

# ===============================
# LEITURA DO EXCEL SAP2000
# ===============================

arquivo = "teste.xlsx"

joints_df = sap_para_df(arquivo, "Joint Coordinates")
frames_df = sap_para_df(arquivo, "Connectivity - Frame")
areas_df  = sap_para_df(arquivo, "Connectivity - Area")

# ===============================
# DICIONÁRIO DE JOINTS
# ===============================

# JointName → np.array([X, Y, Z])
joints = {
    row["Joint"]: np.array([row["XorR"], row["Y"], row["Z"]])
    for _, row in joints_df.iterrows()
}

# ===============================
# PLANO DE VISÃO (USUÁRIO)
# ===============================

# Exemplo de plano isométrico genérico
P1 = np.array([0.0, 0.0, 0.0])
P2 = np.array([1.0, 0.0, 0.0])
P3 = np.array([0.0, 1.0, 0.0])

origem, e1, e2 = plano_base(P1, P2, P3)

# ===============================
# PLOTAGEM
# ===============================

fig, ax = plt.subplots(figsize=(10, 10))

# ---------- FRAMES ----------
for _, lin in frames_df.iterrows():
    j1 = joints[lin["JointI"]]
    j2 = joints[lin["JointJ"]]

    p1_2d = projetar_ponto(j1, origem, e1, e2)
    p2_2d = projetar_ponto(j2, origem, e1, e2)

    ax.plot(
        [p1_2d[0], p2_2d[0]],
        [p1_2d[1], p2_2d[1]],
        color="black",
        linewidth=1
    )

# ---------- AREAS ----------
for _, lin in areas_df.iterrows():
    pts_2d = []

    for col in ["Joint1", "Joint2", "Joint3", "Joint4"]:
        if col in lin and not pd.isna(lin[col]):
            pt_3d = joints[lin[col]]
            pts_2d.append(projetar_ponto(pt_3d, origem, e1, e2))

    if len(pts_2d) < 3:
        continue  # área inválida

    pts_2d.append(pts_2d[0])  # fecha polígono

    xs = [p[0] for p in pts_2d]
    ys = [p[1] for p in pts_2d]

    ax.plot(xs, ys, color="gray", linewidth=0.8)
    ax.fill(xs, ys, color="lightgray", alpha=0.4)

# ===============================
# AJUSTES FINAIS
# ===============================

ax.set_aspect("equal")
ax.axis("off")
ax.set_title("SAP2000 – Visualização 2D (Projeção Isométrica)")

plt.show()
