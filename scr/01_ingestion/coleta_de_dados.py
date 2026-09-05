import os
import random
import numpy as np
import pandas as pd
import kagglehub
from kagglehub import KaggleDatasetAdapter

# Garante que a pasta exista para não dar erro na hora de salvar
os.makedirs('data/raw', exist_ok=True)

# Set the path to the file
file_path = "fpa_variance_data_monthly.csv"

# Load the latest version
fpa_variance_df = kagglehub.load_dataset(
    KaggleDatasetAdapter.PANDAS,
    "ameernassar/fp-and-a-variance-analysis",
    file_path
)

# A MÁGICA DA SUJEIRA ACONTECE AQUI
def aplicar_sujeira(df):
    df_messy = df.copy()
    
    # 1. Bagunçando os nomes dos Departamentos (espaços extras, maiúsculas/minúsculas)
    deps_sujos = []
    for dep in df_messy['Department']:
        rand = random.random()
        if rand < 0.2:
            deps_sujos.append(f"  {dep.upper()}  ") # Tudo maiúsculo e com espaços
        elif rand < 0.4:
            deps_sujos.append(dep.lower())          # Tudo minúsculo
        else:
            deps_sujos.append(dep)
    df_messy['Department'] = deps_sujos

    # 2. Bagunçando as Datas da coluna 'Month'
    # Converte temporariamente para datetime só para podermos formatar errado depois
    df_messy['Month_temp'] = pd.to_datetime(df_messy['Month'])
    datas_sujas = []
    for dt in df_messy['Month_temp']:
        if pd.isna(dt):
            datas_sujas.append(np.nan)
            continue
            
        rand = random.random()
        if rand < 0.3:
            datas_sujas.append(dt.strftime('%d/%m/%Y')) # Formato BR (Dia/Mês/Ano)
        elif rand < 0.6:
            datas_sujas.append(dt.strftime('%m-%d-%Y')) # Formato US com traço
        else:
            datas_sujas.append(dt.strftime('%Y-%m-%d')) # Padrão
    df_messy['Month'] = datas_sujas
    df_messy = df_messy.drop(columns=['Month_temp'])

    # 3. Bagunçando os Valores de 'Actual' (Simulando digitação manual)
    actual_sujo = []
    for val in df_messy['Actual']:
        rand = random.random()
        if rand < 0.3:
            actual_sujo.append(f"R$ {val}") # Colocaram o símbolo da moeda no Excel
        else:
            actual_sujo.append(val)
    df_messy['Actual'] = actual_sujo

    return df_messy


# 1. Guardamos a lista de departamentos originais ANTES da sujeira
departamentos_originais = fpa_variance_df['Department'].unique()

# 2. Criamos uma coluna de backup para não perder a referência limpa
fpa_variance_df['Department_Clean_Backup'] = fpa_variance_df['Department']

# 3. Aplicamos a sujeira (isso vai bagunçar apenas a coluna 'Department' principal)
fpa_variance_df = aplicar_sujeira(fpa_variance_df)

print("\nSeparando e salvando arquivos:")

cont = 0
# 4. Iteramos sobre a lista ORIGINAL de departamentos
for departamento in departamentos_originais:
    cont += 1
    
    # 5. Filtramos usando a coluna de backup (que continuou limpa)
    fpa_variance = fpa_variance_df[fpa_variance_df['Department_Clean_Backup'] == departamento]
    
    # 6. Excluímos a coluna de backup para que ela não vá para o CSV final
    # Assim, o arquivo salvo terá apenas a coluna 'Department' bagunçada
    fpa_variance = fpa_variance.drop(columns=['Department_Clean_Backup'])
    
    # Criamos o nome do arquivo usando o nome original e limpo
    nome_arquivo = str(departamento).strip().replace(" ", "_")
    
    if cont < 2:
        fpa_variance.to_csv(f"data/raw/{nome_arquivo}.csv", index=False)
    elif cont < 4:
        fpa_variance.to_csv(f"data/raw/{nome_arquivo}.csv", index=False, sep=';')
    else:
        fpa_variance.to_csv(f"data/raw/{nome_arquivo}.csv", index=False, decimal=',', sep=';')
        
    print(f"Departamento '{departamento}' salvo no arquivo {nome_arquivo}.csv com {len(fpa_variance)} linhas.")