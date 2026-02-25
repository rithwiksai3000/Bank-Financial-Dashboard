import streamlit as st
import pandas as pd



from src.transform import (
    detect_sections,
    extract_pl,
    extract_quarters,
    extract_balance_sheet,
    extract_cash_flow
)









st.title("Bank Financial Analytics App")

uploaded = st.file_uploader("Upload Screener Excel File", type=["xlsx"])

if uploaded is None:
    st.stop()

# Read all sheets
sheets = pd.read_excel(uploaded, sheet_name=None)

if "Data Sheet" not in sheets:
    st.error("Data Sheet not found in uploaded file.")
    st.stop()

# Extract Data Sheet
data_sheet = sheets["Data Sheet"]

st.subheader("Data Sheet Preview")
st.dataframe(data_sheet.head())

# Detect Sections
sections = detect_sections(data_sheet)

st.subheader("Detected Sections")
st.write(sections)




























st.divider()

st.subheader("Quarterly Extraction")

q = extract_quarters(data_sheet, sections)

st.write("Shape:", q.shape)

st.write("Sample periods:")
st.write(sorted(q["period"].unique())[:8])

st.dataframe(q.head(20), use_container_width=True)










st.divider()

st.subheader("Balance Sheet Extraction")

bs = extract_balance_sheet(data_sheet, sections)

st.write("Shape:", bs.shape)

years_clean = sorted([int(y) for y in bs["year"].unique()])
st.write("Years detected:")
st.write(years_clean)

st.dataframe(bs.head(20), use_container_width=True)








st.subheader("Cash Flow Extraction")

cf = extract_cash_flow(data_sheet, sections)

st.write("Shape:", cf.shape)

years_clean = sorted(int(y) for y in cf["year"].unique())
st.write("Years detected:")
st.write(years_clean)

st.dataframe(cf.head(20), use_container_width=True)
















# PL EXTRACT


from src.transform import detect_sections, extract_pl

pl = extract_pl(data_sheet, sections)

st.subheader("Profit & Loss (Extracted)")

st.write("Shape:", pl.shape)

st.write("Years detected:")
years_clean = sorted([int(y) for y in pl["year"].unique()])
st.write(years_clean)

st.write("Unique metrics count:")
st.write(pl["metric"].nunique())

st.write("Full Extracted Table")
st.dataframe(pl, use_container_width=True)







#PL Visualization


# Chart 1 PL


st.divider()
st.header("📊 Profit & Loss Analytics")

# Pivot P&L to wide format
pl_wide = pl.pivot_table(
    index="metric",
    columns="year",
    values="value",
    aggfunc="first"
)

# Ensure proper ordering of years
pl_wide = pl_wide.sort_index(axis=1)

# ---- Growth Calculations ----
sales_growth = pl_wide.loc["Sales"].pct_change() * 100
profit_growth = pl_wide.loc["Net profit"].pct_change() * 100

# ---- Margin Calculations ----
net_margin = (pl_wide.loc["Net profit"] / pl_wide.loc["Sales"]) * 100
pretax_margin = (pl_wide.loc["Profit before tax"] / pl_wide.loc["Sales"]) * 100

operating_exp = (
    pl_wide.loc["Other Mfr. Exp"] +
    pl_wide.loc["Employee Cost"] +
    pl_wide.loc["Selling and admin"] +
    pl_wide.loc["Other Expenses"]
)

cost_to_income = (operating_exp / pl_wide.loc["Sales"]) * 100

# ---- Proper Interest Coverage Ratio ----
# EBIT = Profit Before Tax + Interest
ebit = pl_wide.loc["Profit before tax"] + pl_wide.loc["Interest"]

icr = ebit / pl_wide.loc["Interest"]  # This is a multiple (x)

# ---- Combine Into Analytics Table ----
pl_analytics = pd.DataFrame({
    "Revenue Growth (%)": sales_growth,
    "Net Profit Growth (%)": profit_growth,
    "Net Profit Margin (%)": net_margin,
    "Pre-Tax Margin (%)": pretax_margin,
    "Cost to Income (%)": cost_to_income,
    "Interest Coverage Ratio (x)": icr
}).round(2)

pl_analytics.index = pl_analytics.index.astype(int)















# Chart 1 PL

import matplotlib.pyplot as plt
import plotly.graph_objects as go

st.subheader("📊 Profitability Trend (Interactive)")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=pl_analytics.index,
    y=pl_analytics["Net Profit Margin (%)"],
    mode='lines+markers',
    name='Net Profit Margin'
))

fig.add_trace(go.Scatter(
    x=pl_analytics.index,
    y=pl_analytics["Pre-Tax Margin (%)"],
    mode='lines+markers',
    name='Pre-Tax Margin'
))

fig.update_layout(
    title="HDFC Bank – Profitability Trend (2016–2025)",
    xaxis_title="Year",
    yaxis_title="Margin (%)",
    hovermode="x unified",
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)






# Chart 2 PL

st.subheader("📈 Growth Trend")

fig_growth = go.Figure()

fig_growth.add_trace(go.Scatter(
    x=pl_analytics.index,
    y=pl_analytics["Revenue Growth (%)"],
    mode='lines+markers',
    name='Revenue Growth'
))

fig_growth.add_trace(go.Scatter(
    x=pl_analytics.index,
    y=pl_analytics["Net Profit Growth (%)"],
    mode='lines+markers',
    name='Net Profit Growth'
))

fig_growth.update_layout(
    title="HDFC Bank – Revenue vs Profit Growth",
    xaxis_title="Year",
    yaxis_title="Growth (%)",
    hovermode="x unified",
    template="plotly_dark"
)

st.plotly_chart(fig_growth, use_container_width=True)











# Chart 3 PL

import plotly.graph_objects as go
import numpy as np

st.subheader("🏦 Cost Structure & Solvency Strength")

# ----------------------------
# 1️⃣ Dynamic Year Filter
# ----------------------------

years = pl_analytics.index.tolist()

selected_years = st.slider(
    "Select Year Range",
    min_value=min(years),
    max_value=max(years),
    value=(min(years), max(years))
)

filtered = pl_analytics.loc[
    (pl_analytics.index >= selected_years[0]) &
    (pl_analytics.index <= selected_years[1])
]

# ----------------------------
# 2️⃣ Build Chart
# ----------------------------

fig_cost = go.Figure()

# Cost to Income (Left Axis)
fig_cost.add_trace(go.Scatter(
    x=filtered.index,
    y=filtered["Cost to Income (%)"],
    mode='lines+markers',
    name='Cost to Income (%)',
    yaxis='y1'
))

# Interest Coverage (Right Axis)
fig_cost.add_trace(go.Scatter(
    x=filtered.index,
    y=filtered["Interest Coverage Ratio (x)"],
    mode='lines+markers',
    name='Interest Coverage (x)',
    yaxis='y2'
))



# ----------------------------
# Cost Spike Annotation (Below Point)
# ----------------------------

max_cost_year = filtered["Cost to Income (%)"].idxmax()
max_cost_value = filtered["Cost to Income (%)"].max()

fig_cost.add_annotation(
    x=max_cost_year,
    y=max_cost_value - 3,  # Push text below the spike
    text=f"Cost Spike ({max_cost_year})",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=1.5,
    arrowcolor="white",
    font=dict(color="white"),
    bgcolor="rgba(0,0,0,0.6)"
)
# ----------------------------
# Layout Settings
# ----------------------------

fig_cost.update_layout(
    title="HDFC Bank – Efficiency & Interest Coverage",
    xaxis=dict(title="Year"),
    yaxis=dict(
        title="Cost to Income (%)"
    ),
    yaxis2=dict(
        title="Interest Coverage (x)",
        overlaying='y',
        side='right'
    ),
    hovermode="x unified",
    template="plotly_dark"
)

st.plotly_chart(fig_cost, use_container_width=True)









