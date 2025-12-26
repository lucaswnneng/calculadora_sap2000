import numpy as np
import pandas as pd
from ferramentas import sap_para_df
from matematica import *
from strategy import (
    Calculo_resistencia_cisalhamento_laje_strategy,
    Plot_triangulacao_strategy,
    Layout_simples_strategy,
)
import matplotlib.colors as mpl_colors
import matplotlib.cm as mpl_cm
import matplotlib.pyplot as plt


class Plotador:
    def __init__(
        self,
        arquivo_joints,
        arquivos_dados,
        calculo_strategy,
        plot_strategy,
        layout_strategy,
    ):
        self.arquivo_joints = arquivo_joints
        self.arquivo_dados = arquivos_dados
        self.calculo_strategy = calculo_strategy
        self.plot_strategy = plot_strategy
        self.layout_strategy = layout_strategy

        self.joints = self.carregar_joints()

        self.areas_df = sap_para_df(arquivos_dados[0], "Connectivity - Area")

        self.area_esforcos_df = [
            sap_para_df(arquivo_dados, "Element Forces - Area Shells")
            for arquivo_dados in arquivos_dados
        ]
        self.area_esforcos_df = pd.concat(self.area_esforcos_df, ignore_index=True)

        self.plano_camera = Plano_camera(
            np.array([0.0, 0.0, 0.0]),
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
        )

    def carregar_joints(self):
        print("Carregando joints...")
        joints_df = sap_para_df(arquivo_joints, "Joint Coordinates")

        joints = {
            row["Joint"]: np.array([row["XorR"], row["Y"], row["Z"]])
            for _, row in joints_df.iterrows()
        }
        print(f"{len(joints)} joints carregados.")
        return joints

    def plotar(self):
        print("Calculando resultados...")
        resultados = self.calculo_strategy.gerar_resultado(
            {
                "esforcos_df": self.area_esforcos_df,
                "areas_df": self.areas_df,
                "fck": 30,
                "gammac": 1.4,
                "gammaf": 1.4,
            }
        )
        print("Resultados calculados.")

        print("Calculando cores...")
        valores = np.array(list(resultados.values()))
        norm = mpl_colors.Normalize(vmin=valores.min(), vmax=valores.max())
        cmap = mpl_cm.autumn_r
        print("Cores calculadas.")

        fig, ax = plt.subplots(figsize=(9, 7))

        print("Gerando gráfico...")
        plot_dados = self.plot_strategy.gerar_grafico(
            {
                "joints": self.joints,
                "areas_df": self.areas_df,
                "resultados": resultados,
                "plano_camera": self.plano_camera,
                "norm": norm,
                "cmap": cmap,
                "ax": ax,
            }
        )
        print("Gráfico gerado.")

        print("Gerando layout...")
        self.layout_strategy.gerar_layout(
            {
                "ax": ax,
                "ax_title": "Regiões com a necessidade de armação de cisalhamento",
                "mappable": plot_dados,
                "cbar_label": "abs(V) - Vrd1 |tf/m|",
            }
        )
        print("Layout gerado.")

        plt.show()


if __name__ == "__main__":
    arquivo_joints = "dados/joints_sap2000.xlsx"
    arquivos_dados = [
        f"dados/dados_sap2000_{i}.xlsx"
        for i in ["1a70", "71a140", "141a210", "211a288"]
    ]
    plotador = Plotador(
        arquivo_joints,
        arquivos_dados,
        Calculo_resistencia_cisalhamento_laje_strategy(),
        Plot_triangulacao_strategy(),
        Layout_simples_strategy(),
    )
    plotador.plotar()
