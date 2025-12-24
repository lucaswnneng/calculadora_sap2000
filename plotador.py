import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
import matplotlib.tri as mtri
from matplotlib.ticker import MaxNLocator, FuncFormatter
from sap_para_df import sap_para_df
from matematica import *

# ===============================
# LEITURA DO EXCEL SAP2000
# ===============================

arquivo_joints = "joints_sap2000.xlsx"
arquivo_dados  = "dados_sap2000.xlsx"

joints_df = sap_para_df(arquivo_joints, "Joint Coordinates")
frames_df = sap_para_df(arquivo_dados, "Connectivity - Frame")
areas_df  = sap_para_df(arquivo_dados, "Connectivity - Area")
area_esforcos_df = sap_para_df(arquivo_dados, "Element Forces - Area Shells")

# ===============================
# DICIONÁRIO DE JOINTS
# ===============================

joints = {
    row["Joint"]: np.array([row["XorR"], row["Y"], row["Z"]])
    for _, row in joints_df.iterrows()
}

# ===============================
# PLANO DE VISÃO
# ===============================

P1 = np.array([0.0, 0.0, 0.0])
P2 = np.array([1.0, 0.0, 0.0])
P3 = np.array([0.0, 1.0, 0.0])

origem, e1, e2 = plano_base(P1, P2, P3)

# ===============================
# PARÂMETROS
# ===============================

fck = 30 # MPa
fctm = 0.30 * fck**(2/3) if fck <= 50 else 2.12 * np.log(1 + 0.1 * (fck+8)) # MPa
fctkinf = 0.7 * fctm # MPa
gammac = 1.4
fctd = fctkinf / gammac # MPa
thaurd = 0.25 * fctd * 100 # tf/m²
bw = 1 # m
h = 1.5 # m
As = 28.05 # cm²/m
d_ = 0.065 # m
d = h - d_ # m
phi1 = As * 0.0001 / (bw * d)
k = max([1, abs(1.6 - d)])
gammaf = 1.4

# ===============================
# OPÇÕES
# ===============================

valor_a_plotar = "Vrd1"
caso = "COMB1"

area_esforcos_df["Vrd1"] = bw * d * (thaurd * k * (1.2 + 40 * phi1) + 0.15 * (-gammaf * area_esforcos_df["F11"] / h)) / gammaf # tf/m

area_esforcos_df = area_esforcos_df[area_esforcos_df["OutputCase"] == caso]

# ===============================
# RESULTADOS NODAIS (média)
# ===============================

esforco_no = {}

for _, lin in areas_df.iterrows():
    area = lin["Area"]
    if area not in area_esforcos_df["Area"].values:
        continue

    for col in ["Joint1", "Joint2", "Joint3", "Joint4"]:
        if col in lin and not pd.isna(lin[col]):
            j = lin[col]
            valor = area_esforcos_df.loc[(area_esforcos_df["Area"] == area) &
                                         (area_esforcos_df["Joint"] == j),
                                         valor_a_plotar].iloc[0]
            
            esforco_no.setdefault(j, []).append(valor)

esforco_no = {j: np.mean(v) for j, v in esforco_no.items()}

# ===============================
# NORMALIZAÇÃO
# ===============================

valores = np.array(list(esforco_no.values()))
norm = colors.Normalize(vmin=valores.min(), vmax=valores.max())
cmap = cm.gist_rainbow
n = cmap.N
offset = 0.0
newcolors = cmap(np.linspace(0, 1, n))
newcolors = np.roll(newcolors, int(n * offset), axis=0)
cmap = colors.ListedColormap(newcolors)

# ===============================
# MALHA TRIANGULAR GLOBAL
# ===============================

xs, ys, vals = [], [], []
triangles = []
node_index = {}

def get_node_index(j):
    if j not in node_index:
        node_index[j] = len(xs)
        p = projetar_ponto(joints[j], origem, e1, e2)
        xs.append(p[0])
        ys.append(p[1])
        vals.append(esforco_no.get(j, 0.0))
    return node_index[j]

for _, lin in areas_df.iterrows():
    nodes = []

    for col in ["Joint1", "Joint2", "Joint3", "Joint4"]:
        if col in lin and not pd.isna(lin[col]):
            nodes.append(lin[col])

    if len(nodes) == 3:
        triangles.append([
            get_node_index(nodes[0]),
            get_node_index(nodes[1]),
            get_node_index(nodes[2])
        ])

    elif len(nodes) == 4:
        i0 = get_node_index(nodes[0])
        i1 = get_node_index(nodes[1])
        i2 = get_node_index(nodes[2])
        i3 = get_node_index(nodes[3])

        triangles.append([i0, i1, i2])
        triangles.append([i0, i2, i3])

triang = mtri.Triangulation(xs, ys, triangles)

# ===============================
# PLOTAGEM
# ===============================

fig, ax = plt.subplots(figsize=(9, 7))

# ---------- FRAMES ----------
if frames_df is not None:
    for _, lin in frames_df.iterrows():
        p1 = projetar_ponto(joints[lin["JointI"]], origem, e1, e2)
        p2 = projetar_ponto(joints[lin["JointJ"]], origem, e1, e2)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="black", linewidth=1)

# ---------- ÁREAS (GRADIENTE REAL) ----------
tpc = ax.tripcolor(
    triang,
    vals,
    shading="gouraud",
    cmap=cmap,
    norm=norm
)

# ===============================
# AJUSTES FINAIS
# ===============================

ax.set_aspect("equal")
ax.axis("off")
ax.set_title("SAP2000 – Visualização 2D (Interpolação Nodal)")

cbar = plt.colorbar(tpc, ax=ax, fraction=0.04, pad=0.2)
cbar.locator = MaxNLocator(nbins=10)
cbar.formatter = FuncFormatter(lambda x, _: f"{x:.2f}")
cbar.update_ticks()
cbar.set_label(f"{valor_a_plotar} médio |tf/m|",labelpad=10)

plt.show()
