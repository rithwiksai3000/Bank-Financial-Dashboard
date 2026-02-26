# Analytics Computing ROE and ROCE


import pandas as pd
from sqlalchemy import create_engine

# Use same connection string you use in app.py
engine = create_engine("mysql+pymysql://root:Bank1234@localhost/bank_analytics")

def compute_roe_roa(bank_name):
    
    query = f"""
        SELECT metric, year, value
        FROM profit_loss
        WHERE bank = '{bank_name}' AND metric = 'Net profit'
        
        UNION ALL
        
        SELECT metric, year, value
        FROM balance_sheet
        WHERE bank = '{bank_name}'
        AND metric IN ('Equity Share Capital', 'Reserves', 'Total Assets')
    """
    
    df = pd.read_sql(query, engine)
    
    if df.empty:
        return None
    
    df_wide = df.pivot(index="year", columns="metric", values="value")
    
    # Create Equity column
    df_wide["Equity"] = df_wide["Equity Share Capital"] + df_wide["Reserves"]
    
    # Simplified ROE & ROA
    df_wide["ROE"] = df_wide["Net profit"] / df_wide["Equity"]
    df_wide["ROA"] = df_wide["Net profit"] / df_wide["Total Assets"]
    
    return df_wide.reset_index()





# CAGR Calculation


def compute_cagr(bank_name):

    query = f"""
        SELECT metric, year, value
        FROM profit_loss
        WHERE bank = '{bank_name}'
        AND metric IN ('Sales', 'Net profit')
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        return None

    df_wide = df.pivot(index="year", columns="metric", values="value")
    df_wide = df_wide.sort_index()

    def calculate_cagr(series, years):
        if len(series) < years + 1:
            return None

        start_value = series.iloc[-(years+1)]
        end_value = series.iloc[-1]

        if start_value <= 0:
            return None

        return ((end_value / start_value) ** (1/years) - 1)

    sales_series = df_wide["Sales"]
    profit_series = df_wide["Net profit"]

    result = {
        "Sales CAGR 3Y": calculate_cagr(sales_series, 3),
        "Sales CAGR 5Y": calculate_cagr(sales_series, 5),
        "Profit CAGR 3Y": calculate_cagr(profit_series, 3),
        "Profit CAGR 5Y": calculate_cagr(profit_series, 5),
    }

    return result

