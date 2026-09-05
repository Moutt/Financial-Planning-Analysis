# FP&A Variance Analysis & Executive Intelligence

Projeto corporativo de **Planejamento Financeiro, Análise de Variação Orçamentária (Budget vs. Actual / OPEX) e Diagnóstico Estatístico Avançado**, construído com **Python, DuckDB, Pandas, SciPy, Plotly, Seaborn e Streamlit**.

---

## Estrutura do Repositório

```text
fpa_variance_analysis/
│
├── data/
│   ├── raw/                           # Bases brutas por departamento (.csv)
│   └── processed/                     # Base consolidada e limpa (df_consolidade.csv)
│
├── notebooks/
│   └── analise_e_insights_fpa.ipynb   # 📓 Estudo estatístico, EDA, anomalias & simulação Monte Carlo
│
├── scr/
│   ├── 01_ingestion/
│   │   └── coleta_de_dados.py         # Ingestão via KaggleHub e simulação de ruído
│   ├── 02_etl/
│   │   ├── process_fpa_data.py        # Pipeline ETL de higienização e recálculo
│   │   └── load_aws.py                # Script de carga para Data Lake AWS S3 (Bronze)
│   ├── 03_sql/
│   │   └── vw_resumo_departamento.sql # View analítica executada in-memory via DuckDB
│   └── 04_dashboard/
│       └── app.py                     # 📊 Painel Executivo Streamlit de Alta Performance
│
├── requirements.txt                   # Dependências do projeto
└── README.md                          # Documentação do projeto
```

---

## Notebook Analítico & Estudos Estatísticos (`notebooks/`)

O notebook (`notebooks/analise_e_insights_fpa.ipynb`) contém um diagnóstico aprofundado distribuído em **9 etapas analíticas**:

1. **Setup & Ingestão com DuckDB**: Conexão in-memory de alta velocidade sobre a view analítica.
2. **Análise Exploratória (EDA) & Distribuições**: Estatísticas descritivas, assimetria (*skewness*), curtose e boxplots de dispersão por departamento.
3. **Decomposição de Variância & Curva ABC (Pareto)**: Identificação dos centros de custo Classe A que concentram mais de 65% do OPEX corporativo (*Operations*, *Finance* e *Marketing*).
4. **Dinâmica Temporal & Sazonalidade (MoM & Q1-Q4)**: Evolução mensal, curva S acumulada (*YTD*) e ritmo de consumo do orçamento.
5. **Detecção de Anomalias & Outliers**: Mapeamento de eventos críticos via Z-Score ($|Z| \ge 1.96$), IQR e regras gerenciais de desvio ($|\Delta\%| > 8\%$).
6. **Matriz de Calor (Heatmap)**: Matriz de desvio orçamentário cruzando Departamentos $\times$ Meses.
7. **Testes Estatísticos de Hipóteses**:
   - **Teste t Pareado & Wilcoxon** ($p = 0.798$): Confirma que o orçamento corporativo não possui viés de subestimação sistemática.
   - **ANOVA One-Way & Kruskal-Wallis** ($p = 0.154$): Avalia a homogeneidade de desvio entre áreas.
   - **Correlação de Pearson/Spearman**: Mede a relação entre volume orçado e desvio relativo.
8. **Simulação de Monte Carlo & Projeções**: 10.000 iterações estocásticas para estimar a probabilidade de estouro anual (~49%) e intervalos de confiança a 95%.
9. **Sumário Executivo & Recomendações Estratégicas**: Plano de ação em 5 pilares para CFOs e líderes de FP&A (ZBB, travas trimestrais, governança de anomalias, *Rolling Forecast*).

---

## Dashboard Executivo Web (FastAPI + Tailwind) (`scr/04_dashboard/`)

O painel interativo foi atualizado para uma arquitetura Web moderna (limpa, rápida e totalmente customizada) que descarta limitações de frameworks baseados em Python.

- **Backend:** `scr/04_dashboard/fastapi_app.py` (Servidor API rápido via FastAPI e uvicorn).
- **Frontend:** `scr/04_dashboard/templates/index.html` (UI/UX clean, responsiva com Tailwind CSS e gráficos fluidos ECharts).
- **Recursos Visuais:** Design "Glassmorphism", cores corporativas de status, cartões flutuantes e ponteiro de atualização ao vivo.

---

## Como Executar

### 1. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 2. Executar o Pipeline de Dados (ETL)
```bash
python scr/02_etl/process_fpa_data.py
```

### 3. Iniciar o Servidor do Dashboard (FastAPI)
```bash
python scr/04_dashboard/fastapi_app.py
```
> O script encontrará uma porta livre automaticamente e exibirá o link no console (ex: `http://localhost:51197`). Basta clicar no link!

### 4. Abrir o Notebook Analítico no Jupyter / VS Code
```bash
jupyter notebook notebooks/analise_e_insights_fpa.ipynb
```
