from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from concreto import Concreto
import matplotlib.tri as mtri
from matematica import projetar_ponto
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter
import sys


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
        esforco_df_key = "esforcos_df"
        esforcos_df = args[esforco_df_key].copy()

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

        print("Calculando resistência ao cisalhamento das lajes...")
        esforcos_df["Vrd1_13"] = (
            bw
            * d
            * (
                thaurd * k * (1.2 + 40 * phi1)
                + 0.15 * (-gammaf * esforcos_df["F11"] / h)
            )
            / gammaf
        )  # tf/m

        esforcos_df["Vrd1_23"] = (
            bw
            * d
            * (
                thaurd * k * (1.2 + 40 * phi1)
                + 0.15 * (-gammaf * esforcos_df["F22"] / h)
            )
            / gammaf
        )  # tf/m

        esforcos_df["Diff1"] = np.maximum(
            np.abs(esforcos_df["V13"]) - esforcos_df["Vrd1_13"], 0
        )

        esforcos_df["Diff2"] = np.maximum(
            np.abs(esforcos_df["V23"]) - esforcos_df["Vrd1_23"], 0
        )

        print(esforcos_df["Diff1"].max(), "Máximo Diff1")
        print(esforcos_df["Diff2"].max(), "Máximo Diff2")

        esforcos_df[output_col] = esforcos_df[["Diff1", "Diff2"]].max(axis=1)

        print("Cálculo da resistência ao cisalhamento concluído.")

        esforcos_df = esforcos_df[["Area", "Joint", output_col]]

        print("Agregando resultados por nó...")
        result_dados = esforcos_df.groupby("Joint")[output_col].max().to_dict()
        print("Agregação concluída.")
        print(max(result_dados.values()), "Máximo geral por nó")

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
