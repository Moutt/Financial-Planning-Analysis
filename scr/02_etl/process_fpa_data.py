import pandas as pd
import numpy as np
import os
import glob

# Configuração de caminhos
RAW_DIR = 'data/raw/'
PROCESSED_DIR = 'data/processed/'

# Garante que a pasta processed exista
os.makedirs(PROCESSED_DIR, exist_ok=True)

def padronizacao_colunas_numericas(df, coluna):
    """Limpa e converte strings monetárias/numéricas para float."""
    if coluna not in df.columns:
        return
    df[coluna] = df[coluna].astype(str)
    df[coluna] = df[coluna].str.replace(r'[R\$\s]', '', regex=True)
    df[coluna] = df[coluna].str.replace(',', '.')
    df[coluna] = pd.to_numeric(df[coluna], errors='coerce')

def normalizar_data(val):
    
    val = str(val).strip()
    if not val or val.lower() == 'nan':
        return np.nan
        
    if '/' in val:
        partes = val.split('/')
        if len(partes) == 3:
            return f"{partes[2]}-{int(partes[1]):02d}-01"
    elif '-' in val:
        partes = val.split('-')
        if len(partes) == 3:
            if len(partes[0]) == 4:
                return f"{partes[0]}-{int(partes[1]):02d}-01"
            elif len(partes[2]) == 4:
                return f"{partes[2]}-{int(partes[0]):02d}-01"
                
    dt = pd.to_datetime(val, errors='coerce')
    if pd.notna(dt):
        return dt.strftime('%Y-%m-01')
    return val

lista_dfs = []

print("Iniciando processamento e limpeza dos dados brutos...")

for caminho_completo in sorted(glob.glob(os.path.join(RAW_DIR, '*.csv'))):
    nome_arquivo = os.path.basename(caminho_completo)
    
    # Leitura com detecção automática de separador
    df_temp = pd.read_csv(caminho_completo, sep=None, engine='python')
    
    # 1. Higienização do nome do departamento (remove espaços extras e padroniza caixa)
    df_temp['Department'] = df_temp['Department'].astype(str).str.strip().str.upper()
    
    # 2. Padronização consistente das datas
    df_temp['Month'] = df_temp['Month'].apply(normalizar_data)
    
    # 3. Limpeza dos valores numéricos
    padronizacao_colunas_numericas(df_temp, 'Budget')
    padronizacao_colunas_numericas(df_temp, 'Actual')
    
    # 4. Recálculo consistente de Variance e Variance_pct
    df_temp['Variance'] = df_temp['Actual'] - df_temp['Budget']
    df_temp['Variance_pct'] = np.where(
        df_temp['Budget'] != 0,
        (df_temp['Variance'] / df_temp['Budget']).round(4),
        0.0
    )
    
    lista_dfs.append(df_temp)
    print(f" -> Arquivo '{nome_arquivo}' processado: {len(df_temp)} linhas ({df_temp['Department'].iloc[0]})")

# Consolidação final
df_consolidado = pd.concat(lista_dfs, ignore_index=True)

# Ordenação lógica por Departamento e Mês
df_consolidado = df_consolidado.sort_values(by=['Department', 'Month']).reset_index(drop=True)

# Salvando dados processados
caminho_saida = os.path.join(PROCESSED_DIR, 'df_consolidade.csv')
df_consolidado.to_csv(caminho_saida, index=False)

print(f"\n[SUCESSO] Base consolidada salva em: {caminho_saida}")
print(f"Total de linhas: {len(df_consolidado)}")
print(f"Departamentos únicos ({df_consolidado['Department'].nunique()}): {df_consolidado['Department'].unique().tolist()}")
print(f"Meses únicos ({df_consolidado['Month'].nunique()}): {sorted(df_consolidado['Month'].unique())}")