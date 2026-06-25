import os
import sys
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config import DB_PATH

from agents.revenue_agent import RevenueForecastAgent

st.set_page_config(page_title="Revenue Forecasting | InsightPilot", page_icon="📊", layout="wide")

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
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color: white;'>📊 Corporate Revenue Forecasting (FP&A)</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8;'>Aggregated subscription monthly recurring revenue (MRR) historical metrics and ML projections.</p>", unsafe_allow_html=True)

# Select months
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown("<h3>⚙️ Forecast Period Selection</h3>", unsafe_allow_html=True)
fc_months = st.slider("Select Forecast Horizon (Months Ahead):", min_value=1, max_value=12, value=6)
st.markdown("</div>", unsafe_allow_html=True)

# Fetch revenue data
conn = sqlite3.connect(DB_PATH)
df_all = pd.read_sql_query("SELECT * FROM revenue_forecast ORDER BY forecast_date ASC", conn)
conn.close()

if df_all.empty:
    st.info("No revenue forecast records found in database. Please run model training.")
else:
    df_hist = df_all[df_all["historical_revenue"].notna()].copy()
    df_fore = df_all[df_all["forecasted_revenue"].notna()].copy().head(fc_months)
    
    # KPIs calculations
    latest_hist = df_hist.iloc[-1]["historical_revenue"] if not df_hist.empty else 0.0
    end_fore = df_fore.iloc[-1]["forecasted_revenue"] if not df_fore.empty else 0.0
    growth = ((end_fore - latest_hist) / latest_hist * 100) if latest_hist else 0.0
    
    # KPI Row
    col_k1, col_k2, col_k3 = st.columns(3)
    
    with col_k1:
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:0.85rem; color:#94A3B8; text-transform:uppercase;">Latest Month MRR</div>
            <div style="font-size:2.2rem; font-weight:800; color:#10B981; margin-top:4px;">${latest_hist:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_k2:
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:0.85rem; color:#94A3B8; text-transform:uppercase;">Projected Month {fc_months} MRR</div>
            <div style="font-size:2.2rem; font-weight:800; color:#38BDF8; margin-top:4px;">${end_fore:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_k3:
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:0.85rem; color:#94A3B8; text-transform:uppercase;">Forecast Growth Rate</div>
            <div style="font-size:2.2rem; font-weight:800; color:#818CF8; margin-top:4px;">{growth:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    # Shaded confidence band Plotly Line Chart
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    
    fig = go.Figure()
    
    # Historical trace
    fig.add_trace(go.Scatter(
        x=df_hist["forecast_date"], y=df_hist["historical_revenue"],
        mode='lines+markers', name='Historical Revenue',
        line=dict(color='#10B981', width=3),
        marker=dict(size=6)
    ))
    
    # Build continuous forecast trace (conn historical to forecast)
    if not df_hist.empty and not df_fore.empty:
        last_hist_row = df_hist.iloc[-1]
        conn_row = pd.DataFrame([{
            "forecast_date": last_hist_row["forecast_date"],
            "historical_revenue": None,
            "forecasted_revenue": last_hist_row["historical_revenue"],
            "lower_bound": last_hist_row["historical_revenue"],
            "upper_bound": last_hist_row["historical_revenue"]
        }])
        df_fore_conn = pd.concat([conn_row, df_fore]).reset_index(drop=True)
    else:
        df_fore_conn = df_fore
        
    # Projected trace
    fig.add_trace(go.Scatter(
        x=df_fore_conn["forecast_date"], y=df_fore_conn["forecasted_revenue"],
        mode='lines+markers', name='Projected Forecast',
        line=dict(color='#38BDF8', width=3, dash='dash'),
        marker=dict(size=6)
    ))
    
    # Confidence Intervals (shaded region)
    if not df_fore_conn.empty:
        # Shading lower bound and upper bound
        fig.add_trace(go.Scatter(
            x=df_fore_conn["forecast_date"].tolist() + df_fore_conn["forecast_date"].tolist()[::-1],
            y=df_fore_conn["upper_bound"].tolist() + df_fore_conn["lower_bound"].tolist()[::-1],
            fill='toself',
            fillcolor='rgba(56, 189, 248, 0.08)',
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            showlegend=True,
            name="95% Confidence Interval"
        ))
        
    fig.update_layout(
        title="<b>SaaS Monthly Recurring Revenue Trends & Projections</b>",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#E2E8F0"),
        xaxis=dict(gridcolor="#1E293B"),
        yaxis=dict(gridcolor="#1E293B"),
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=40, r=40, t=50, b=40),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # FP&A Agent Report
    st.markdown("<h3>🤖 Simulated FP&A Specialist Agent Report</h3>", unsafe_allow_html=True)
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    
    if st.button("Generate Strategic Analysis"):
        with st.spinner("Agent running mathematical curve analysis..."):
            agent = RevenueForecastAgent()
            report = agent.run(f"Forecast revenue performance for the next {fc_months} months")
            st.markdown(report)
    else:
        st.info("Click the button to invoke the FP&A Revenue forecasting agent for this forecast period.")
        
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Forecast raw table
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>📋 Raw Monthly Forecasting Values</h3>", unsafe_allow_html=True)
    st.dataframe(df_fore[["forecast_date", "forecasted_revenue", "lower_bound", "upper_bound"]], use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
