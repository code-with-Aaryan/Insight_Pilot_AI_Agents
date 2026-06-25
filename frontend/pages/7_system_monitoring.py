import os
import sys
import sqlite3
import pandas as pd
import streamlit as st

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

st.set_page_config(page_title="System Monitoring | InsightPilot", page_icon="⚙️", layout="wide")

DB_PATH = "c:/Users/aryan kumar kannojia/Music/Caposton_write_2/database/insightpilot.db"

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
    .cost-value {
        font-family: 'Outfit', sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        color: #818CF8;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color: white;'>⚙️ System & Model Monitoring Console</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8;'>Track agent execution statistics, model performance evaluations, and cognitive API cost telemetry.</p>", unsafe_allow_html=True)

# Fetch Cost and Token Telemetry
def fetch_telemetry():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*), SUM(token_usage), SUM(cost) FROM agent_logs")
    steps, tokens, cost = cursor.fetchone()
    conn.close()
    
    return {
        "steps": steps or 0,
        "tokens": tokens or 0,
        "cost": cost or 0.0
    }

telemetry = fetch_telemetry()

# Telemetry Row
col_t1, col_t2, col_t3 = st.columns(3)

with col_t1:
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;">
        <div style="font-size:0.85rem; color:#94A3B8; text-transform:uppercase;">Cognitive Actions Traced</div>
        <div class="cost-value" style="color: #38BDF8;">{telemetry['steps']}</div>
    </div>
    """, unsafe_allow_html=True)

with col_t2:
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;">
        <div style="font-size:0.85rem; color:#94A3B8; text-transform:uppercase;">Estimated Tokens Simulated</div>
        <div class="cost-value">{telemetry['tokens']:,}</div>
    </div>
    """, unsafe_allow_html=True)

with col_t3:
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;">
        <div style="font-size:0.85rem; color:#94A3B8; text-transform:uppercase;">Simulated API Compute Cost</div>
        <div class="cost-value" style="color: #10B981;">${telemetry['cost']:.5f}</div>
    </div>
    """, unsafe_allow_html=True)

# Model Performance Cards
st.markdown("<h2>📊 Machine Learning Performance Logs</h2>", unsafe_allow_html=True)

m_left, m_mid, m_right = st.columns(3)

with m_left:
    st.markdown("""
    <div class="glass-card">
        <h4 style="color:#38BDF8;">SaaS Churn Model (XGBoost)</h4>
        <hr style="border-color:rgba(255,255,255,0.05);"/>
        <p><strong>Accuracy:</strong> 83.00%</p>
        <p><strong>ROC AUC Score:</strong> 0.9016</p>
        <p><strong>F1-Score (Churned):</strong> 0.85</p>
        <p><strong>F1-Score (Active):</strong> 0.81</p>
        <span style="font-size:0.75rem; color:#94A3B8;">Status: Active & Calibrated</span>
    </div>
    """, unsafe_allow_html=True)

with m_mid:
    st.markdown("""
    <div class="glass-card">
        <h4 style="color:#38BDF8;">Transaction Fraud Model (RF)</h4>
        <hr style="border-color:rgba(255,255,255,0.05);"/>
        <p><strong>Accuracy:</strong> 100.00%</p>
        <p><strong>ROC AUC Score:</strong> 1.0000</p>
        <p><strong>Precision (Fraud):</strong> 100.00%</p>
        <p><strong>Recall (Fraud):</strong> 100.00%</p>
        <span style="font-size:0.75rem; color:#94A3B8;">Status: Active & Calibrated</span>
    </div>
    """, unsafe_allow_html=True)

with m_right:
    st.markdown("""
    <div class="glass-card">
        <h4 style="color:#38BDF8;">FP&A Forecast Model (Ridge)</h4>
        <hr style="border-color:rgba(255,255,255,0.05);"/>
        <p><strong>Model Class:</strong> Ridge Linear Regression</p>
        <p><strong>Fitted Seasonality:</strong> 12-Month Sine/Cosine</p>
        <p><strong>Mean Squared Error:</strong> ~1.43e+06</p>
        <p><strong>Trend Coefficient:</strong> +$1,200/month</p>
        <span style="font-size:0.75rem; color:#94A3B8;">Status: Active & Projecting</span>
    </div>
    """, unsafe_allow_html=True)

# Full log view
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown("<h3>📋 Database Cognitive Logs Table</h3>", unsafe_allow_html=True)

conn = sqlite3.connect(DB_PATH)
df_logs = pd.read_sql_query("SELECT id, timestamp, session_id, agent_name, token_usage, cost FROM agent_logs ORDER BY id DESC LIMIT 20", conn)
conn.close()

if df_logs.empty:
    st.info("No logs present in the database.")
else:
    st.dataframe(df_logs, use_container_width=True)

# Database Administration Console
st.markdown("<h3>🔧 Database Administration</h3>", unsafe_allow_html=True)
if st.button("Reset & Clear Agent Cognitive Logs"):
    try:
        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        db.clear_agent_logs()
        st.success("Cognitive logs successfully cleared from database.")
        st.rerun()
    except Exception as e:
        st.error(f"Reset failed: {e}")
        
st.markdown("</div>", unsafe_allow_html=True)
