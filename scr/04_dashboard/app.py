import streamlit as st
import duckdb
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA E ESTILOS
# ==============================================================================
st.set_page_config(
    page_title="FP&A Intelligence | Planejamento e OPEX",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS para elevar o visual a padrão executivo
st.markdown("""
<style>
    /* Estilo geral */
    .main .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
    }
    
    /* Cartões KPI Customizados */
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #8E8EA0;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 6px;
    }
    .metric-delta {
        font-size: 0.85rem;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .delta-saving {
        color: #10B981;
    }
    .delta-overrun {
        color: #EF4444;
    }
    .delta-neutral {
        color: #3B82F6;
    }

    /* Badges e Pílulas */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-success {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-danger {
        background-color: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .badge-info {
        background-color: rgba(59, 130, 246, 0.15);
        color: #3B82F6;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        border-radius: 8px;
        font-weight: 600;
        padding: 0 16px;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# CARREGAMENTO E PROCESSAMENTO DE DADOS COM DUCKDB
# ==============================================================================
# Raiz do projeto (sobe 2 níveis a partir de scr/04_dashboard/app.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@st.cache_data(show_spinner="Carregando e processando base financeira com DuckDB...")
def carregar_dados_via_sql():
    # Localização do arquivo SQL
    caminho_sql = os.path.join(BASE_DIR, 'scr', '03_sql', 'vw_resumo_departamento.sql')
    if not os.path.exists(caminho_sql):
        caminho_sql = 'scr/03_sql/vw_resumo_departamento.sql'
        
    with open(caminho_sql, 'r', encoding='utf-8') as arquivo:
        query = arquivo.read()
    
    # Caminho absoluto para o CSV processado (usando barras normais para compatibilidade DuckDB)
    caminho_csv = os.path.join(BASE_DIR, 'data', 'processed', 'df_consolidade.csv').replace('\\', '/')
    if not os.path.exists(caminho_csv):
        caminho_csv = 'data/processed/df_consolidade.csv'
        
    query_exec = query.replace('data/processed/df_consolidade.csv', caminho_csv)
    
    df = duckdb.query(query_exec).to_df()
    df['Month'] = pd.to_datetime(df['Month'])
    df = df.sort_values(by=['Department', 'Month']).reset_index(drop=True)
    return df

df_raw = carregar_dados_via_sql()

# ==============================================================================
# BARRA LATERAL (SIDEBAR) & FILTROS GLOBAIS
# ==============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/combo-chart.png", width=64)
    st.title("FP&A Suite")
    st.caption("Planejamento Orçamentário & Análise de Variação OPEX")
    st.markdown("---")
    
    st.subheader("🎯 Filtros Globais")
    
    # 1. Filtro de Departamentos
    todos_deptos = sorted(df_raw['Department'].unique().tolist())
    
    # Ações rápidas de seleção
    col_btn1, col_btn2 = st.columns(2)
    if 'selected_deptos' not in st.session_state:
        st.session_state.selected_deptos = todos_deptos
        
    if col_btn1.button("✅ Todos", use_container_width=True):
        st.session_state.selected_deptos = todos_deptos
    if col_btn2.button("🧹 Limpar", use_container_width=True):
        st.session_state.selected_deptos = [todos_deptos[0]] if todos_deptos else []
    
    departamentos_selecionados = st.multiselect(
        "Selecione as Áreas / Departamentos:",
        options=todos_deptos,
        default=st.session_state.selected_deptos
    )
    
    # 2. Filtro de Trimestres
    todos_quarters = sorted(df_raw['Quarter'].unique().tolist())
    quarters_selecionados = st.multiselect(
        "Trimestres (Quarters):",
        options=todos_quarters,
        default=todos_quarters
    )
    
    # 3. Filtro de Intervalo Temporal (Meses)
    min_date = df_raw['Month'].min().to_pydatetime()
    max_date = df_raw['Month'].max().to_pydatetime()
    
    date_range = st.slider(
        "Período de Análise:",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="MMM/YYYY"
    )
    
    st.markdown("---")
    st.subheader("⚙️ Configurações de Exibição")
    
    # Unidade Monetária
    unidade = st.radio(
        "Escala dos Valores:",
        options=["R$ Reais (Original)", "R$ Milhares (k)", "R$ Milhões (M)"],
        index=0
    )
    
    # Fator de escala
    if unidade == "R$ Milhões (M)":
        divisor = 1_000_000
        sufixo = " M"
    elif unidade == "R$ Milhares (k)":
        divisor = 1_000
        sufixo = "k"
    else:
        divisor = 1
        sufixo = ""
        
    st.markdown("---")
    st.caption("🚀 **Engine:** DuckDB In-Memory")
    st.caption(f"📅 **Registros Carregados:** {len(df_raw)} linhas")

# ==============================================================================
# FUNÇÕES AUXILIARES DE FORMATAÇÃO
# ==============================================================================
def format_moeda(val, divisor=divisor, sufixo=sufixo):
    if pd.isna(val):
        return "R$ 0,00"
    val_scaled = val / divisor
    if divisor == 1:
        return f"R$ {val_scaled:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        return f"R$ {val_scaled:,.2f}{sufixo}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_pct(val):
    if pd.isna(val):
        return "0.0%"
    sinal = "+" if val > 0 else ""
    return f"{sinal}{val * 100:.1f}%".replace(".", ",")

# ==============================================================================
# APLICAÇÃO DOS FILTROS
# ==============================================================================
if not departamentos_selecionados:
    st.warning("⚠️ Por favor, selecione pelo menos um departamento na barra lateral.")
    st.stop()

if not quarters_selecionados:
    st.warning("⚠️ Por favor, selecione pelo menos um trimestre na barra lateral.")
    st.stop()

# Filtragem do dataframe
df_filtrado = df_raw[
    (df_raw['Department'].isin(departamentos_selecionados)) &
    (df_raw['Quarter'].isin(quarters_selecionados)) &
    (df_raw['Month'] >= pd.to_datetime(date_range[0])) &
    (df_raw['Month'] <= pd.to_datetime(date_range[1]))
].copy()

if df_filtrado.empty:
    st.info("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# ==============================================================================
# HEADER PRINCIPAL
# ==============================================================================
col_title, col_status = st.columns([3, 1])
with col_title:
    st.title("📊 Painel Executivo de FP&A e Gestão de OPEX")
    st.markdown("**Acompanhamento de Realização Orçamentária (Budget vs. Actual) & Análise de Variações**")

with col_status:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='text-align: right;'><span class='badge badge-info'>📅 {date_range[0].strftime('%b/%Y')} - {date_range[1].strftime('%b/%Y')}</span> "
        f"<span class='badge badge-success'>🏢 {len(departamentos_selecionados)} Áreas</span></div>", 
        unsafe_allow_html=True
    )

# ==============================================================================
# CÁLCULOS DOS KPIS PRINCIPAIS
# ==============================================================================
total_budget = df_filtrado['Budget'].sum()
total_actual = df_filtrado['Actual'].sum()
total_variance = df_filtrado['Variance'].sum()
variance_pct_geral = (total_variance / total_budget) if total_budget != 0 else 0
burn_rate = (total_actual / total_budget * 100) if total_budget != 0 else 0

# Contagem de departamentos
dept_totals = df_filtrado.groupby('Department')[['Budget', 'Actual', 'Variance']].sum().reset_index()
dept_totals['Variance_pct'] = np.where(dept_totals['Budget'] != 0, dept_totals['Variance'] / dept_totals['Budget'], 0)
num_overrun = (dept_totals['Variance'] > 0).sum()
num_saving = (dept_totals['Variance'] < 0).sum()
num_on_target = (dept_totals['Variance'] == 0).sum()

# ==============================================================================
# CARDS DE KPIS EXECUTIVOS (TOP RIBBON)
# ==============================================================================
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">🎯 Orçamento (Budget)</div>
        <div class="metric-value">{format_moeda(total_budget)}</div>
        <div class="metric-delta delta-neutral"><span>Planejado Aprovado</span></div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">💳 Gasto Real (Actual)</div>
        <div class="metric-value">{format_moeda(total_actual)}</div>
        <div class="metric-delta delta-neutral"><span>Total Executado</span></div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    is_saving = total_variance <= 0
    delta_class = "delta-saving" if is_saving else "delta-overrun"
    status_label = "Economia Líquida (Saving)" if is_saving else "Estouro Líquido (Overrun)"
    icon = "📉" if is_saving else "📈"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">⚖️ Variação Líquida ({icon})</div>
        <div class="metric-value {delta_class}">{format_moeda(total_variance)}</div>
        <div class="metric-delta {delta_class}"><span>{format_pct(variance_pct_geral)} vs. Budget ({status_label})</span></div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    burn_class = "delta-saving" if burn_rate <= 100 else "delta-overrun"
    badge_burn = "No Limite" if burn_rate <= 100 else "Acima do Teto"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">🔥 Taxa de Execução (Burn)</div>
        <div class="metric-value {burn_class}">{burn_rate:.1f}%</div>
        <div class="metric-delta {burn_class}"><span>Status: <b>{badge_burn}</b></span></div>
    </div>
    """, unsafe_allow_html=True)

with kpi5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">🏢 Saúde dos Departamentos</div>
        <div class="metric-value" style="font-size: 1.35rem; margin-top: 4px;">
            <span style="color: #10B981;">{num_saving} Economia</span> | <span style="color: #EF4444;">{num_overrun} Estouro</span>
        </div>
        <div class="metric-delta delta-neutral"><span>Total: {len(dept_totals)} Áreas</span></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# ABAS DE NAVEGAÇÃO ANALÍTICA
# ==============================================================================
tab_exec, tab_temporal, tab_dept, tab_matrix, tab_sim, tab_data = st.tabs([
    "📌 Visão Executiva & Cascata",
    "📈 Tendências & Sazonalidade",
    "🏢 Deep-Dive Departamental",
    "🔥 Matriz de Risco & Dispersão",
    "🔍 Simulador What-If",
    "📋 Base de Dados & Exportação"
])

# ------------------------------------------------------------------------------
# TAB 1: VISÃO EXECUTIVA & CASCATA
# ------------------------------------------------------------------------------
with tab_exec:
    st.markdown("### 🌉 Ponte Orçamentária (Waterfall Bridge)")
    st.caption("Visualização de como cada departamento contribuiu para o desvio líquido total em relação ao Orçamento Inicial.")
    
    col_wf, col_bar = st.columns([1.2, 1])
    
    with col_wf:
        # Preparação dos dados da cascata
        wf_dept = dept_totals.sort_values(by='Variance', ascending=False)
        
        x_labels = ["Budget Inicial"] + list(wf_dept['Department']) + ["Actual Final"]
        y_values = [total_budget / divisor] + list(wf_dept['Variance'] / divisor) + [total_actual / divisor]
        measure_types = ["absolute"] + ["relative"] * len(wf_dept) + ["total"]
        
        # Textos com formatação
        text_labels = [f"{format_moeda(total_budget)}"]
        for v in wf_dept['Variance']:
            text_labels.append(f"{'+' if v>0 else ''}{format_moeda(v)}")
        text_labels.append(f"{format_moeda(total_actual)}")
        
        fig_waterfall = go.Figure(go.Waterfall(
            name="Ponte de Desvio",
            orientation="v",
            measure=measure_types,
            x=x_labels,
            y=y_values,
            text=text_labels,
            textposition="outside",
            connector={"line": {"color": "rgba(128, 128, 128, 0.4)", "dash": "dot"}},
            decreasing={"marker": {"color": "#10B981"}},  # Verde para economia (reduz gasto)
            increasing={"marker": {"color": "#EF4444"}},  # Vermelho para estouro (aumenta gasto)
            totals={"marker": {"color": "#3B82F6"}}       # Azul para totais
        ))
        
        fig_waterfall.update_layout(
            title="Ponte Orçamentária: Orçado ➔ Variações por Área ➔ Realizado",
            waterfallgap=0.3,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=50, b=50),
            yaxis=dict(title=f"Valor ({unidade})", showgrid=True, gridcolor="rgba(128, 128, 128, 0.15)")
        )
        st.plotly_chart(fig_waterfall, use_container_width=True)
        
    with col_bar:
        # Comparativo Budget vs Actual por Área
        dept_summary_sorted = dept_totals.sort_values(by='Actual', ascending=True)
        
        fig_dept_comp = go.Figure()
        fig_dept_comp.add_trace(go.Bar(
            y=dept_summary_sorted['Department'],
            x=dept_summary_sorted['Budget'] / divisor,
            name='Orçado (Budget)',
            orientation='h',
            marker_color='#3B82F6'
        ))
        fig_dept_comp.add_trace(go.Bar(
            y=dept_summary_sorted['Department'],
            x=dept_summary_sorted['Actual'] / divisor,
            name='Realizado (Actual)',
            orientation='h',
            marker_color='#6366F1'
        ))
        
        fig_dept_comp.update_layout(
            title="Orçado vs. Realizado por Departamento",
            barmode='group',
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=50, b=50),
            xaxis=dict(title=f"Valor ({unidade})", showgrid=True, gridcolor="rgba(128, 128, 128, 0.15)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_dept_comp, use_container_width=True)
        
    st.markdown("---")
    
    # Destaques: Maiores Economias e Maiores Desvios
    col_top_overrun, col_top_saving = st.columns(2)
    
    with col_top_overrun:
        st.markdown("#### 🚨 Top Áreas com Maior Estouro (Overrun)")
        overruns = dept_totals[dept_totals['Variance'] > 0].sort_values(by='Variance', ascending=False).head(4)
        if overruns.empty:
            st.success("🎉 Nenhuma área apresentou estouro no período selecionado!")
        else:
            for _, row in overruns.iterrows():
                st.markdown(f"""
                <div style="background: rgba(239, 68, 68, 0.08); border-left: 4px solid #EF4444; border-radius: 4px; padding: 10px 14px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; font-weight: 600;">
                        <span>{row['Department']}</span>
                        <span style="color: #EF4444;">+{format_moeda(row['Variance'])} ({format_pct(row['Variance_pct'])})</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #8E8EA0; margin-top: 2px;">
                        Orçado: {format_moeda(row['Budget'])} | Realizado: {format_moeda(row['Actual'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
    with col_top_saving:
        st.markdown("#### 🏆 Top Áreas com Maior Economia (Saving)")
        savings = dept_totals[dept_totals['Variance'] < 0].sort_values(by='Variance', ascending=True).head(4)
        if savings.empty:
            st.info("Nenhuma área gerou economia líquida no período.")
        else:
            for _, row in savings.iterrows():
                st.markdown(f"""
                <div style="background: rgba(16, 185, 129, 0.08); border-left: 4px solid #10B981; border-radius: 4px; padding: 10px 14px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; font-weight: 600;">
                        <span>{row['Department']}</span>
                        <span style="color: #10B981;">{format_moeda(row['Variance'])} ({format_pct(row['Variance_pct'])})</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #8E8EA0; margin-top: 2px;">
                        Orçado: {format_moeda(row['Budget'])} | Realizado: {format_moeda(row['Actual'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 2: TENDÊNCIAS TEMPORAIS & TRIMESTRES
# ------------------------------------------------------------------------------
with tab_temporal:
    st.markdown("### 📈 Evolução Mensal & Acumulada")
    
    # Agregação por Mês
    df_monthly = df_filtrado.groupby('Month')[['Budget', 'Actual', 'Variance']].sum().reset_index()
    df_monthly['Variance_pct'] = np.where(df_monthly['Budget'] != 0, df_monthly['Variance'] / df_monthly['Budget'], 0)
    df_monthly['Month_Label'] = df_monthly['Month'].dt.strftime('%b/%Y')
    
    # Acumulado (YTD)
    df_monthly['Budget_Cum'] = df_monthly['Budget'].cumsum()
    df_monthly['Actual_Cum'] = df_monthly['Actual'].cumsum()
    df_monthly['Variance_Cum'] = df_monthly['Actual_Cum'] - df_monthly['Budget_Cum']
    
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        # Gráfico Mensal Linhas
        fig_monthly = go.Figure()
        fig_monthly.add_trace(go.Scatter(
            x=df_monthly['Month_Label'],
            y=df_monthly['Budget'] / divisor,
            name='Budget Mensal',
            mode='lines+markers',
            line=dict(color='#3B82F6', width=3, dash='dot'),
            marker=dict(size=7)
        ))
        fig_monthly.add_trace(go.Scatter(
            x=df_monthly['Month_Label'],
            y=df_monthly['Actual'] / divisor,
            name='Actual Mensal',
            mode='lines+markers',
            line=dict(color='#EF4444', width=3),
            marker=dict(size=7)
        ))
        
        fig_monthly.update_layout(
            title="Evolução Mensal: Orçado vs. Realizado",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=50, b=50),
            xaxis=dict(showgrid=True, gridcolor="rgba(128, 128, 128, 0.15)"),
            yaxis=dict(title=f"Valor ({unidade})", showgrid=True, gridcolor="rgba(128, 128, 128, 0.15)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_monthly, use_container_width=True)
        
    with col_t2:
        # Curva S Acumulada
        fig_cum = go.Figure()
        fig_cum.add_trace(go.Scatter(
            x=df_monthly['Month_Label'],
            y=df_monthly['Budget_Cum'] / divisor,
            name='Budget Acumulado',
            mode='lines+markers',
            line=dict(color='#3B82F6', width=3),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.08)'
        ))
        fig_cum.add_trace(go.Scatter(
            x=df_monthly['Month_Label'],
            y=df_monthly['Actual_Cum'] / divisor,
            name='Actual Acumulado',
            mode='lines+markers',
            line=dict(color='#10B981' if df_monthly['Variance_Cum'].iloc[-1] <= 0 else '#EF4444', width=3)
        ))
        
        fig_cum.update_layout(
            title="Curva S: Consumo Acumulado do Orçamento (YTD)",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=50, b=50),
            xaxis=dict(showgrid=True, gridcolor="rgba(128, 128, 128, 0.15)"),
            yaxis=dict(title=f"Acumulado ({unidade})", showgrid=True, gridcolor="rgba(128, 128, 128, 0.15)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_cum, use_container_width=True)
        
    st.markdown("---")
    st.markdown("### 📊 Performance Trimestral (Quarter Breakdown)")
    
    df_quarter = df_filtrado.groupby('Quarter')[['Budget', 'Actual', 'Variance']].sum().reset_index()
    df_quarter['Execution_Rate'] = (df_quarter['Actual'] / df_quarter['Budget'] * 100)
    df_quarter['Variance_pct'] = (df_quarter['Variance'] / df_quarter['Budget'])
    
    col_q1, col_q2 = st.columns([1.2, 1])
    
    with col_q1:
        fig_q = px.bar(
            df_quarter,
            x='Quarter',
            y=['Budget', 'Actual'],
            barmode='group',
            title="Comparativo por Trimestre",
            labels={'value': f'Valor ({unidade})', 'variable': 'Métrica'},
            color_discrete_map={'Budget': '#3B82F6', 'Actual': '#6366F1'}
        )
        fig_q.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=50, b=50),
            yaxis=dict(showgrid=True, gridcolor="rgba(128, 128, 128, 0.15)")
        )
        st.plotly_chart(fig_q, use_container_width=True)
        
    with col_q2:
        st.markdown("#### Resumo Trimestral")
        for _, qrow in df_quarter.iterrows():
            q_color = "#10B981" if qrow['Variance'] <= 0 else "#EF4444"
            st.markdown(f"""
            <div style="border: 1px solid rgba(128,128,128,0.2); border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; font-weight: 700; font-size: 1rem;">
                    <span>Trimestre {qrow['Quarter']}</span>
                    <span style="color: {q_color};">{format_pct(qrow['Variance_pct'])}</span>
                </div>
                <div style="font-size: 0.85rem; color: #8E8EA0; margin-top: 4px;">
                    Orçado: <b>{format_moeda(qrow['Budget'])}</b> | Realizado: <b>{format_moeda(qrow['Actual'])}</b>
                </div>
                <div style="font-size: 0.85rem; margin-top: 2px;">
                    Taxa de Execução: <b>{qrow['Execution_Rate']:.1f}%</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 3: DEEP-DIVE DEPARTAMENTAL
# ------------------------------------------------------------------------------
with tab_dept:
    st.markdown("### 🏢 Análise Detalhada por Centro de Custo")
    
    depto_selecionado = st.selectbox(
        "Selecione o Departamento para Detalhamento:",
        options=departamentos_selecionados
    )
    
    df_single_dept = df_filtrado[df_filtrado['Department'] == depto_selecionado].sort_values(by='Month').reset_index(drop=True)
    
    if not df_single_dept.empty:
        d_budget = df_single_dept['Budget'].sum()
        d_actual = df_single_dept['Actual'].sum()
        d_variance = df_single_dept['Variance'].sum()
        d_var_pct = (d_variance / d_budget) if d_budget != 0 else 0
        d_share = (d_actual / total_actual * 100) if total_actual != 0 else 0
        
        # Mês de maior e menor gasto
        idx_max = df_single_dept['Actual'].idxmax()
        idx_min = df_single_dept['Actual'].idxmin()
        max_month = df_single_dept.loc[idx_max, 'Month'].strftime('%b/%Y')
        min_month = df_single_dept.loc[idx_min, 'Month'].strftime('%b/%Y')
        
        # Métricas do departamento
        dcol1, dcol2, dcol3, dcol4 = st.columns(4)
        dcol1.metric("Orçamento Total", format_moeda(d_budget))
        dcol2.metric("Gasto Realizado", format_moeda(d_actual))
        
        d_color = "normal" if d_variance <= 0 else "inverse"
        dcol3.metric("Variação (R$ / %)", format_moeda(d_variance), delta=format_pct(d_var_pct), delta_color=d_color)
        dcol4.metric("Share no OPEX Total", f"{d_share:.1f}%", f"Pico: {max_month}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gráfico Combinado: Barras (Budget/Actual) + Linha de Variação %
        fig_combo = go.Figure()
        fig_combo.add_trace(go.Bar(
            x=df_single_dept['Month'].dt.strftime('%b/%Y'),
            y=df_single_dept['Budget'] / divisor,
            name='Budget',
            marker_color='#3B82F6'
        ))
        fig_combo.add_trace(go.Bar(
            x=df_single_dept['Month'].dt.strftime('%b/%Y'),
            y=df_single_dept['Actual'] / divisor,
            name='Actual',
            marker_color='#6366F1'
        ))
        fig_combo.add_trace(go.Scatter(
            x=df_single_dept['Month'].dt.strftime('%b/%Y'),
            y=df_single_dept['Variance_pct'] * 100,
            name='% Variação',
            yaxis='y2',
            mode='lines+markers+text',
            text=[f"{v*100:.1f}%" for v in df_single_dept['Variance_pct']],
            textposition="top center",
            line=dict(color='#F59E0B', width=2.5),
            marker=dict(size=8)
        ))
        
        fig_combo.update_layout(
            title=f"Histórico Mensal: {depto_selecionado}",
            barmode='group',
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=50, b=50),
            yaxis=dict(title=f"Montante ({unidade})", showgrid=True, gridcolor="rgba(128, 128, 128, 0.15)"),
            yaxis2=dict(
                title="% Variação vs Budget",
                overlaying='y',
                side='right',
                showgrid=False,
                ticksuffix="%"
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_combo, use_container_width=True)
        
        # Tabela mensal do departamento
        st.markdown("#### Detalhamento Mês a Mês")
        df_display_dept = df_single_dept[['Month_Label', 'Quarter', 'Budget', 'Actual', 'Variance', 'Variance_pct', 'Execution_Rate_Pct', 'Criticidade']].copy()
        df_display_dept['Budget'] = df_display_dept['Budget'].apply(format_moeda)
        df_display_dept['Actual'] = df_display_dept['Actual'].apply(format_moeda)
        df_display_dept['Variance'] = df_display_dept['Variance'].apply(format_moeda)
        df_display_dept['Variance_pct'] = df_display_dept['Variance_pct'].apply(format_pct)
        df_display_dept['Execution_Rate_Pct'] = df_display_dept['Execution_Rate_Pct'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(df_display_dept, use_container_width=True, hide_index=True)

# ------------------------------------------------------------------------------
# TAB 4: MATRIZ DE RISCO & HEATMAP
# ------------------------------------------------------------------------------
with tab_matrix:
    st.markdown("### 🔥 Matriz de Calor de Desvios (Heatmap)")
    st.caption("Identifique instantaneamente anomalias, picos de estouro (vermelho) ou períodos superavitários (verde).")
    
    # Pivotando para Heatmap
    pivot_var_pct = df_filtrado.pivot_table(
        index='Department',
        columns='Month',
        values='Variance_pct',
        aggfunc='mean'
    )
    
    month_cols = [col.strftime('%b/%Y') for col in pivot_var_pct.columns]
    
    fig_heat = go.Figure(data=go.Heatmap(
        z=pivot_var_pct.values * 100,
        x=month_cols,
        y=pivot_var_pct.index,
        colorscale=[
            [0.0, '#10B981'],   # Verde escuro (Economia)
            [0.5, '#F3F4F6'],   # Cinza neutro (0% desvio)
            [1.0, '#EF4444']    # Vermelho (Estouro)
        ],
        zmid=0,
        text=[[f"{val*100:+.1f}%" if pd.notna(val) else "" for val in row] for row in pivot_var_pct.values],
        texttemplate="%{text}",
        hoverongaps=False,
        colorbar=dict(title="% Desvio", ticksuffix="%")
    ))
    
    fig_heat.update_layout(
        title="Matriz de Desvio Orçamentário (%): Departamentos x Meses",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=50),
        xaxis=dict(title="Mês"),
        yaxis=dict(title="Departamento", dtick=1)
    )
    st.plotly_chart(fig_heat, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 🎯 Matriz de Materialidade & Risco (Scatter Plot)")
    st.caption("Cruzamento entre o Tamanho do Orçamento (Materialidade) e o % de Desvio. Bolhas maiores indicam maior Gasto Real.")
    
    fig_scatter = px.scatter(
        dept_totals,
        x='Budget',
        y='Variance_pct',
        size='Actual',
        color='Variance',
        color_continuous_scale=['#10B981', '#F3F4F6', '#EF4444'],
        color_continuous_midpoint=0,
        text='Department',
        labels={'Budget': f'Orçamento Total ({unidade})', 'Variance_pct': 'Desvio Percentual (%)'},
        title="Matriz de Materialidade vs. Desvio Relativo"
    )
    
    fig_scatter.update_traces(
        textposition='top center',
        marker=dict(sizeref=2.*max(dept_totals['Actual'])/(40.**2), sizemin=8)
    )
    
    fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Budget Neutro (0%)")
    fig_scatter.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=50),
        xaxis=dict(showgrid=True, gridcolor="rgba(128, 128, 128, 0.15)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(128, 128, 128, 0.15)", tickformat=".1%")
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 5: SIMULADOR DE CENÁRIOS WHAT-IF
# ------------------------------------------------------------------------------
with tab_sim:
    st.markdown("### 🔮 Simulador de Cenários & Planejamento Orçamentário")
    st.caption("Simule o impacto de políticas de corte ou reajuste de orçamento em tempo real.")
    
    col_sim_ctrl, col_sim_res = st.columns([1, 1.5])
    
    with col_sim_ctrl:
        st.markdown("#### Parâmetros da Simulação")
        corte_global = st.slider(
            "Ajuste Linear Global no Budget (%):",
            min_value=-25.0,
            max_value=25.0,
            value=0.0,
            step=1.0,
            help="Valores negativos simulam corte de despesas; positivos simulam expansão orçamentária."
        )
        
        st.markdown("##### Ajustes Específicos por Área:")
        ajustes_especificos = {}
        for dep in departamentos_selecionados:
            ajustes_especificos[dep] = st.slider(
                f"{dep} (%):",
                min_value=-30.0,
                max_value=30.0,
                value=0.0,
                step=2.0,
                key=f"sim_{dep}"
            )
            
    with col_sim_res:
        st.markdown("#### Resultado Projetado do Cenário")
        
        df_sim = dept_totals.copy()
        df_sim['Ajuste_Pct'] = (corte_global + df_sim['Department'].map(ajustes_especificos)) / 100
        df_sim['Budget_Simulado'] = df_sim['Budget'] * (1 + df_sim['Ajuste_Pct'])
        df_sim['Variance_Simulada'] = df_sim['Actual'] - df_sim['Budget_Simulado']
        df_sim['Variance_Pct_Simulada'] = np.where(df_sim['Budget_Simulado'] != 0, df_sim['Variance_Simulada'] / df_sim['Budget_Simulado'], 0)
        
        novo_budget_total = df_sim['Budget_Simulado'].sum()
        nova_variance_total = df_sim['Variance_Simulada'].sum()
        delta_budget = novo_budget_total - total_budget
        
        scol1, scol2, scol3 = st.columns(3)
        scol1.metric("Novo Budget Total", format_moeda(novo_budget_total), delta=format_moeda(delta_budget))
        scol2.metric("Gasto Real Mantido", format_moeda(total_actual))
        scol3.metric("Nova Variação Projetada", format_moeda(nova_variance_total), delta=format_pct(nova_variance_total / novo_budget_total if novo_budget_total!=0 else 0))
        
        # Gráfico comparativo da simulação
        fig_sim = go.Figure()
        fig_sim.add_trace(go.Bar(
            x=df_sim['Department'],
            y=df_sim['Budget'] / divisor,
            name='Budget Original',
            marker_color='#94A3B8'
        ))
        fig_sim.add_trace(go.Bar(
            x=df_sim['Department'],
            y=df_sim['Budget_Simulado'] / divisor,
            name='Budget Simulado',
            marker_color='#3B82F6'
        ))
        fig_sim.add_trace(go.Bar(
            x=df_sim['Department'],
            y=df_sim['Actual'] / divisor,
            name='Actual Real',
            marker_color='#EF4444'
        ))
        
        fig_sim.update_layout(
            title="Impacto do Cenário por Departamento",
            barmode='group',
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=50, b=50),
            yaxis=dict(title=f"Montante ({unidade})", showgrid=True, gridcolor="rgba(128, 128, 128, 0.15)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_sim, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 6: BASE DE DADOS & EXPORTAÇÃO
# ------------------------------------------------------------------------------
with tab_data:
    st.markdown("### 📋 Tabela Geral de Dados & Exportações")
    st.caption("Navegue pelos dados brutos filtrados e faça o download para auditoria ou apresentações.")
    
    col_search, col_exp = st.columns([2, 1])
    with col_search:
        busca = st.text_input("🔍 Pesquisar na base:", placeholder="Digite o departamento, status...")
        
    df_view = df_filtrado.copy()
    if busca:
        df_view = df_view[
            df_view['Department'].str.contains(busca, case=False, na=False) |
            df_view['Status_Variacao'].str.contains(busca, case=False, na=False) |
            df_view['Criticidade'].str.contains(busca, case=False, na=False)
        ]
        
    # Formatação para exibição amigável
    df_view_formatted = df_view[['Department', 'Month_Label', 'Quarter', 'Budget', 'Actual', 'Variance', 'Variance_pct', 'Execution_Rate_Pct', 'Status_Variacao', 'Criticidade']].copy()
    df_view_formatted['Budget'] = df_view_formatted['Budget'].apply(format_moeda)
    df_view_formatted['Actual'] = df_view_formatted['Actual'].apply(format_moeda)
    df_view_formatted['Variance'] = df_view_formatted['Variance'].apply(format_moeda)
    df_view_formatted['Variance_pct'] = df_view_formatted['Variance_pct'].apply(format_pct)
    df_view_formatted['Execution_Rate_Pct'] = df_view_formatted['Execution_Rate_Pct'].apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(df_view_formatted, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("#### 📥 Exportar Relatórios")
    
    col_d1, col_d2 = st.columns(2)
    
    # Exportação CSV Bruto Filtrado
    csv_raw = df_filtrado.to_csv(index=False).encode('utf-8')
    col_d1.download_button(
        label="📥 Baixar Dados Filtrados (CSV)",
        data=csv_raw,
        file_name=f"fpa_consolidado_filtrado_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    # Exportação Resumo Executivo
    csv_resumo = dept_totals.to_csv(index=False).encode('utf-8')
    col_d2.download_button(
        label="📊 Baixar Resumo por Departamento (CSV)",
        data=csv_resumo,
        file_name=f"fpa_resumo_departamentos_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )