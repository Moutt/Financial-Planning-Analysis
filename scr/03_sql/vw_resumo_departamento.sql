-- ====================================================================
-- View / Consulta Principal FP&A: Resumo por Departamento e Período
-- Fonte de dados: data/processed/df_consolidade.csv
-- Engine: DuckDB
-- ====================================================================

SELECT 
    Department,
    CAST(Month AS DATE) AS Month,
    strftime(CAST(Month AS DATE), '%b/%Y') AS Month_Label,
    'Q' || CAST(quarter(CAST(Month AS DATE)) AS VARCHAR) AS Quarter,
    year(CAST(Month AS DATE)) AS Year,
    month(CAST(Month AS DATE)) AS Month_Num,
    Budget,
    Actual,
    Variance,
    Variance_pct,
    -- Taxa de Execução Orçamentária (% Burn Rate)
    ROUND((Actual / NULLIF(Budget, 0)) * 100, 2) AS Execution_Rate_Pct,
    -- Status analítico de desvio para OPEX
    CASE 
        WHEN Variance > 0 THEN 'Overrun'
        WHEN Variance < 0 THEN 'Saving'
        ELSE 'On Budget'
    END AS Status_Variacao,
    -- Faixa de severidade / criticidade do desvio
    CASE 
        WHEN Variance_pct > 0.10 THEN 'Alto Risco (Overrun > 10%)'
        WHEN Variance_pct > 0 THEN 'Alerta (Overrun <= 10%)'
        WHEN Variance_pct = 0 THEN 'No Alvo (0%)'
        WHEN Variance_pct >= -0.10 THEN 'Favorável (Saving <= 10%)'
        ELSE 'Superavitário (Saving > 10%)'
    END AS Criticidade
FROM read_csv_auto('data/processed/df_consolidade.csv')
ORDER BY Department, Month;
