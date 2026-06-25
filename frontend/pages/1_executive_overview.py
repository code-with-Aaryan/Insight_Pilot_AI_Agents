import os
import sys
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config import DB_PATH

# Setup page layout
st.set_page_config(page_title="Executive Overview | InsightPilot", page_icon="📊", layout="wide")

# Apply global dark styling
st.markdown("""
    <style>
    .main { background-color: #0A0E1A; color: #E2E8F0; }
    .glass-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(16px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 24px;
        margin-bottom: 20px;
    }
    .metric-value {
        font-family: 'Outfit', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        color: #38BDF8;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color: white;'>📊 Executive Corporate Overview</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8;'>Aggregated business metrics across subscription profiles, financial transactions, and models.</p>", unsafe_allow_html=True)

# Fetch Aggregates
def fetch_kpis():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Churn
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN churn_probability > 0.5 THEN 1 ELSE 0 END), SUM(CASE WHEN churn_probability > 0.5 THEN monthly_charges ELSE 0 END) FROM customers")
    total_cust, high_risk_cust, revenue_at_risk = cursor.fetchone()
    
    # Fraud
    cursor.execute("SELECT COUNT(*), SUM(is_fraud), SUM(CASE WHEN is_fraud=1 THEN amount ELSE 0 END) FROM transactions")
    total_tx, fraud_cnt, fraud_amount = cursor.fetchone()
    
    # Revenue
    cursor.execute("SELECT historical_revenue FROM revenue_forecast WHERE historical_revenue IS NOT NULL ORDER BY forecast_date DESC LIMIT 1")
    curr_mrr = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_cust": total_cust,
        "high_risk_cust": high_risk_cust or 0,
        "revenue_at_risk": revenue_at_risk or 0,
        "total_tx": total_tx,
        "fraud_cnt": fraud_cnt or 0,
        "fraud_amount": fraud_amount or 0,
        "curr_mrr": curr_mrr
    }

try:
    kpi = fetch_kpis()
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

# Metric Row
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.markdown(f"""
    <div class="glass-card" style="text-align: center;">
        <div class="metric-label">Monthly Recurring Revenue</div>
        <div class="metric-value" style="color: #10B981;">${kpi['curr_mrr']:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with m_col2:
    st.markdown(f"""
    <div class="glass-card" style="text-align: center;">
        <div class="metric-label">Active Subscribers</div>
        <div class="metric-value">{kpi['total_cust']:,}</div>
    </div>
    """, unsafe_allow_html=True)

with m_col3:
    st.markdown(f"""
    <div class="glass-card" style="text-align: center;">
        <div class="metric-label">Subscribers At Churn Risk</div>
        <div class="metric-value" style="color: #F59E0B;">{kpi['high_risk_cust']} <span style='font-size:1.1rem; font-weight:400; color:#94A3B8;'>(${kpi['revenue_at_risk']:,.0f}/mo)</span></div>
    </div>
    """, unsafe_allow_html=True)

with m_col4:
    st.markdown(f"""
    <div class="glass-card" style="text-align: center;">
        <div class="metric-label">Fraud Incidents Intercepted</div>
        <div class="metric-value" style="color: #EF4444;">{kpi['fraud_cnt']} <span style='font-size:1.1rem; font-weight:400; color:#94A3B8;'>(${kpi['fraud_amount']:,.0f})</span></div>
    </div>
    """, unsafe_allow_html=True)

# Visual Charts
st.markdown("<h2 style='margin-top: 20px;'>📈 Executive Analytical Charts</h2>", unsafe_allow_html=True)
col_left, col_right = st.columns(2)

# Load data for charts
conn = sqlite3.connect(DB_PATH)
df_cust = pd.read_sql_query("SELECT contract_type, churn_probability FROM customers", conn)
df_tx = pd.read_sql_query("SELECT category, is_fraud, amount FROM transactions", conn)
df_rev = pd.read_sql_query("SELECT forecast_date, historical_revenue, forecasted_revenue FROM revenue_forecast ORDER BY forecast_date ASC", conn)
conn.close()

with col_left:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    # Chart 1: Revenue forecasting timeline
    fig_rev = go.Figure()
    
    # Filter historical vs forecast
    hist_df = df_rev[df_rev["historical_revenue"].notna()]
    fore_df = df_rev[df_rev["forecasted_revenue"].notna()]
    
    # We append the last historical row to forecasted to draw a continuous line
    if not hist_df.empty and not fore_df.empty:
        last_hist = hist_df.iloc[-1]
        conn_row = pd.DataFrame([{
            "forecast_date": last_hist["forecast_date"],
            "historical_revenue": None,
            "forecasted_revenue": last_hist["historical_revenue"]
        }])
        fore_df = pd.concat([conn_row, fore_df]).reset_index(drop=True)
        
    fig_rev.add_trace(go.Scatter(
        x=hist_df["forecast_date"], y=hist_df["historical_revenue"],
        mode='lines+markers', name='Historical Revenue',
        line=dict(color='#10B981', width=3),
        marker=dict(size=6)
    ))
    
    fig_rev.add_trace(go.Scatter(
        x=fore_df["forecast_date"], y=fore_df["forecasted_revenue"],
        mode='lines+markers', name='Projected Forecast',
        line=dict(color='#38BDF8', width=3, dash='dash'),
        marker=dict(size=6)
    ))
    
    fig_rev.update_layout(
        title="<b>SaaS Revenue Trajectory (Historical vs projected)</b>",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#E2E8F0"),
        xaxis=dict(gridcolor="#1E293B"),
        yaxis=dict(gridcolor="#1E293B"),
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=40, r=40, t=50, b=40)
    )
    st.plotly_chart(fig_rev, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    # Chart 2: Churn risk distribution per contract type
    df_cust["Risk Group"] = df_cust["churn_probability"].apply(lambda p: "High (>50%)" if p > 0.5 else "Medium (30-50%)" if p > 0.3 else "Low (<30%)")
    fig_churn = px.histogram(
        df_cust, x="contract_type", color="Risk Group",
        barmode="group",
        color_discrete_map={"High (>50%)": "#EF4444", "Medium (30-50%)": "#F59E0B", "Low (<30%)": "#10B981"},
        labels={"contract_type": "Subscription Contract Type", "count": "Subscribers Count"}
    )
    fig_churn.update_layout(
        title="<b>Customer Churn Risk by Contract Agreement</b>",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#E2E8F0"),
        xaxis=dict(gridcolor="#1E293B"),
        yaxis=dict(gridcolor="#1E293B"),
        margin=dict(l=40, r=40, t=50, b=40)
    )
    st.plotly_chart(fig_churn, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Secondary details
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown("<h3>🛡️ Recent High-Score Security Alerts</h3>", unsafe_allow_html=True)
# Fetch top recent fraudulent/flagged transactions
conn = sqlite3.connect(DB_PATH)
df_alerts = pd.read_sql_query("""
    SELECT t.transaction_id, t.customer_id, c.name, t.amount, t.merchant, t.timestamp, t.fraud_score, t.status 
    FROM transactions t
    JOIN customers c ON t.customer_id = c.customer_id
    WHERE t.status IN ('Declined', 'Flagged')
    ORDER BY t.timestamp DESC LIMIT 5
""", conn)
conn.close()

if df_alerts.empty:
    st.info("No active high-risk security alerts recorded.")
else:
    st.table(df_alerts)
st.markdown("</div>", unsafe_allow_html=True)
