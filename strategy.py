from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from concreto import Concreto
import matplotlib.tri as mtri
from matematica import projetar_ponto
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter


class Calculo_strategy(ABC):
    output_col = "output_calculo"

    @abstractmethod
    def gerar_resultado(self, args):
        pass


class Plot_strategy(ABC):
    @abstractmethod
    def gerar_grafico(self, args):
        pass


class Layout_strategy(ABC):
    @abstractmethod
    def gerar_layout(self, args):
        pass


class Calculo_resistencia_cisalhamento_laje_strategy(Calculo_strategy):
    def gerar_resultado(self, args):
        output_col = super().output_col
        esforco_df_key, areas_df_key = "esforcos_df", "areas_df"
        esforcos_df = args[esforco_df_key].copy()
        areas_df = args[areas_df_key]

        fck = args["fck"]
        gammac = args["gammac"]
        gammaf = args["gammaf"]
        concreto = Concreto(fck, gammac=gammac)
        fctd = concreto.fctd
        thaurd = 0.25 * fctd * 100  # tf/m²
        bw = 1  # m
        h = 1.5  # m
        As = 28.05  # cm²/m
        d_ = 0.065  # m
        d = h - d_  # m
        phi1 = As * 0.0001 / (bw * d)
        k = max([1, abs(1.6 - d)])

        esforcos_df["Vrd1"] = (
            bw
            * d
            * (
                thaurd * k * (1.2 + 40 * phi1)
                + 0.15 * (-gammaf * esforcos_df["F11"] / h)
            )
            / gammaf
        )  # tf/m
        
        esforcos_df[output_col] = np.maximum(np.abs(esforcos_df["V13"]) - esforcos_df["Vrd1"], 0)

        esforcos_df = esforcos_df[["Area", "Joint", output_col]]

        result_dados = {}
        esforcos_areas = esforcos_df["Area"].values
        joint_cols = ["Joint1", "Joint2", "Joint3", "Joint4"]
        for _, lin in areas_df.iterrows():
            area = lin["Area"]
            if area not in esforcos_areas:
                continue

            for col in joint_cols:
                if col in lin and not pd.isna(lin[col]):
                    j = lin[col]
                    valor = esforcos_df.loc[
                        (esforcos_df["Area"] == area) & (esforcos_df["Joint"] == j),
                        output_col,
                    ].iloc[0]

                    result_dados.setdefault(j, []).append(valor)

        result_dados = {j: np.mean(v) for j, v in result_dados.items()}
        return result_dados


class Plot_triangulacao_strategy(Plot_strategy):
    def gerar_grafico(self, args):
        joints_key = "joints"
        joints = args[joints_key]
        plano_camera_key = "plano_camera"
        plano_camera = args[plano_camera_key]
        resultados_key = "resultados"
        resultado_nodal = args[resultados_key]
        areas_df_key = "areas_df"
        areas_df = args[areas_df_key]
        ax_key = "ax"
        ax = args[ax_key]

        xs, ys, vals = [], [], []
        triangles = []
        node_index = {}

        def get_node_index(j):
            if j not in node_index:
                node_index[j] = len(xs)
                p = plano_camera.projetar(joints[j])
                xs.append(p[0])
                ys.append(p[1])
                vals.append(resultado_nodal.get(j, 0.0))
            return node_index[j]

        for _, lin in areas_df.iterrows():
            nodes = []

            for col in ["Joint1", "Joint2", "Joint3", "Joint4"]:
                if col in lin and not pd.isna(lin[col]):
                    nodes.append(lin[col])

            if len(nodes) == 3:
                triangles.append(
                    [
                        get_node_index(nodes[0]),
                        get_node_index(nodes[1]),
                        get_node_index(nodes[2]),
                    ]
                )

            elif len(nodes) == 4:
                i0 = get_node_index(nodes[0])
                i1 = get_node_index(nodes[1])
                i2 = get_node_index(nodes[2])
                i3 = get_node_index(nodes[3])

                triangles.append([i0, i1, i2])
                triangles.append([i0, i2, i3])

        triang = mtri.Triangulation(xs, ys, triangles)

        cmap_key = "cmap"
        cmap = args[cmap_key]
        norm_key = "norm"
        norm = args[norm_key]

        return ax.tripcolor(triang, vals, shading="gouraud", cmap=cmap, norm=norm)


class Layout_simples_strategy(Layout_strategy):
    def gerar_layout(self, args):
        ax_key = "ax"
        ax = args[ax_key]
        ax.set_aspect("equal")
        ax.axis("off")

        ax_title_key = "ax_title"
        ax_title = args[ax_title_key]
        ax.set_title(ax_title)

        mappable_key = "mappable"
        mappable = args[mappable_key]
        cbar = plt.colorbar(mappable, ax=ax, fraction=0.04, pad=0.2)
        cbar.locator = MaxNLocator(nbins=10)
        cbar.formatter = FuncFormatter(lambda x, _: f"{x:.2f}")
        cbar.update_ticks()

        cbar_label_key = "cbar_label"
        cbar_label = args[cbar_label_key]
        cbar.set_label(cbar_label, labelpad=10)
