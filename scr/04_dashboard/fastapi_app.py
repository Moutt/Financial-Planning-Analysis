from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import duckdb
import pandas as pd
import os
import uvicorn

app = FastAPI(title="FP&A Modern Dashboard")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

def load_data(dept: str = None, quarter: str = None):
    caminho_sql = os.path.join(BASE_DIR, 'scr', '03_sql', 'vw_resumo_departamento.sql')
    if not os.path.exists(caminho_sql):
        caminho_sql = 'scr/03_sql/vw_resumo_departamento.sql'
        
    with open(caminho_sql, 'r', encoding='utf-8') as arquivo:
        query = arquivo.read()
    
    caminho_csv = os.path.join(BASE_DIR, 'data', 'processed', 'df_consolidade.csv').replace('\\', '/')
    if not os.path.exists(caminho_csv):
        caminho_csv = 'data/processed/df_consolidade.csv'
        
    query_exec = query.replace('data/processed/df_consolidade.csv', caminho_csv)
    
    df = duckdb.query(query_exec).to_df()
    df['Month'] = pd.to_datetime(df['Month']).dt.strftime('%Y-%m-%d')
    
    # Aplica filtros se existirem
    if dept and dept != "Todos":
        df = df[df['Department'] == dept]
    if quarter and quarter != "Todos":
        df = df[df['Quarter'] == quarter]
        
    return df

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/favicon.ico")
async def favicon():
    from fastapi import Response
    return Response(content=b"", media_type="image/x-icon")

@app.get("/api/filters")
async def get_filters():
    df = load_data()
    departments = ["Todos"] + sorted(df['Department'].unique().tolist())
    quarters = ["Todos"] + sorted(df['Quarter'].unique().tolist())
    return {"departments": departments, "quarters": quarters}

@app.get("/api/kpis")
async def get_kpis(dept: str = Query("Todos"), quarter: str = Query("Todos")):
    df = load_data(dept, quarter)
    total_budget = df['Budget'].sum()
    total_actual = df['Actual'].sum()
    total_variance = df['Variance'].sum()
    variance_pct = (total_variance / total_budget * 100) if total_budget else 0
    
    return {
        "budget": float(total_budget),
        "actual": float(total_actual),
        "variance": float(total_variance),
        "variance_pct": float(variance_pct)
    }

@app.get("/api/departments")
async def get_departments(dept: str = Query("Todos"), quarter: str = Query("Todos")):
    df = load_data(dept, quarter)
    if df.empty:
        return []
        
    df_dept = df.groupby('Department').agg({
        'Budget': 'sum',
        'Actual': 'sum',
        'Variance': 'sum'
    }).reset_index()
    
    df_dept['Variance_pct'] = (df_dept['Variance'] / df_dept['Budget']) * 100
    return df_dept.to_dict(orient="records")

@app.get("/api/trend")
async def get_trend(dept: str = Query("Todos"), quarter: str = Query("Todos")):
    df = load_data(dept, quarter)
    if df.empty:
        return []
        
    df_trend = df.groupby('Month_Label').agg({
        'Budget': 'sum',
        'Actual': 'sum',
        'Variance': 'sum',
        'Month': 'min'
    }).reset_index()
    
    df_trend = df_trend.sort_values('Month')
    return df_trend.to_dict(orient="records")

@app.get("/api/insights")
async def get_insights(dept: str = Query("Todos"), quarter: str = Query("Todos")):
    df = load_data(dept, quarter)
    if df.empty:
        return {"insights": ["Nenhum dado encontrado para os filtros selecionados."]}
        
    insights = []
    
    # Execução geral
    budget = df['Budget'].sum()
    actual = df['Actual'].sum()
    exec_rate = (actual / budget * 100) if budget else 0
    
    if exec_rate > 100:
        insights.append(f"A taxa de execução está em {exec_rate:.1f}%, caracterizando um cenário geral de **Overrun (Estouro)**.")
    else:
        insights.append(f"A taxa de execução está em {exec_rate:.1f}%, caracterizando um cenário geral de **Saving (Economia)**.")
        
    # Maior ofensor
    dept_agg = df.groupby('Department')['Variance'].sum().reset_index()
    maior_overrun = dept_agg[dept_agg['Variance'] > 0].sort_values(by='Variance', ascending=False)
    maior_saving = dept_agg[dept_agg['Variance'] < 0].sort_values(by='Variance', ascending=True)
    
    if not maior_overrun.empty:
        pior_dept = maior_overrun.iloc[0]
        insights.append(f"O departamento **{pior_dept['Department']}** é o maior ofensor de custos, com estouro de R$ {pior_dept['Variance']:,.0f}.")
        
    if not maior_saving.empty:
        melhor_dept = maior_saving.iloc[0]
        insights.append(f"O departamento **{melhor_dept['Department']}** lidera em economias, preservando R$ {abs(melhor_dept['Variance']):,.0f}.")
        
    return {"insights": insights}

if __name__ == "__main__":
    import socket
    def get_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]
            
    porta_livre = get_free_port()
    print("=" * 60)
    print(f"SERVIDOR INICIADO COM SUCESSO!")
    print(f"ACESSE O DASHBOARD AQUI: http://localhost:{porta_livre}")
    print("=" * 60)
    
    uvicorn.run("fastapi_app:app", host="127.0.0.1", port=porta_livre)
