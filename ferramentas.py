import pandas as pd

def sap_para_df(arquivo_excel, planilha):
    """
    Lê um arquivo Excel exportado do SAP2000 e retorna um DataFrame
    com nomes de colunas formatados (nome + unidade).
    """

    print(f"Lendo planilha '{planilha}' do arquivo '{arquivo_excel}'...")
    
    # Verifica se há dados na planilha
    if planilha not in pd.ExcelFile(arquivo_excel).sheet_names:
        return None

    # Lê o arquivo inteiro sem assumir cabeçalho
    df_raw = pd.read_excel(
        arquivo_excel,
        sheet_name=planilha,
        header=None
    )
    print(f"Planilha '{planilha}' lida com {df_raw.shape[0]} linhas e {df_raw.shape[1]} colunas.")

    # Linha 2 → nomes das colunas (índice 1)
    col_nomes = df_raw.iloc[1]


    # Concatena nome + unidade
    colunas = [f"{name}" for name in col_nomes]

    print("Formatando DataFrame...")
    # Dados começam a partir da linha 4 (índice 3)
    if df_raw.shape[0] > 3:
        df = df_raw.drop(index=[0, 1, 2])
    else:
        df = pd.DataFrame(columns=colunas)

    # Aplica os novos nomes de colunas
    df.columns = colunas

    # (Opcional) resetar índice
    df.reset_index(drop=True, inplace=True)
    print("DataFrame formatado.")

    return df
