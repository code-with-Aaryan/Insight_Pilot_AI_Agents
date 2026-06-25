import os
import sys
import sqlite3
import streamlit as st

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import DB_PATH

# Configure page parameters
st.set_page_config(
    page_title="InsightPilot | Multi-Agent Business Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Glassmorphism UI)
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;500;700&display=swap');
        
        /* General layout settings */
        .main {
            background-color: #0A0E1A;
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #E2E8F0;
        }
        
        h1, h2, h3 {
            font-family: 'Outfit', sans-serif;
            color: #FFFFFF;
            font-weight: 800;
        }
        
        /* Vibrant gradient headings */
        .gradient-text {
            background: linear-gradient(135deg, #38BDF8 0%, #3B82F6 50%, #818CF8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }
        
        /* Glassmorphic Cards */
        .glass-card {
            background: rgba(30, 41, 59, 0.45);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .glass-card:hover {
            border-color: rgba(56, 189, 248, 0.4);
            transform: translateY(-2px);
            box-shadow: 0 12px 40px 0 rgba(56, 189, 248, 0.15);
        }
        
        /* Metric KPI style adjustments */
        .kpi-container {
            display: flex;
            justify-content: space-between;
            gap: 15px;
        }
        .kpi-card {
            flex: 1;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
        }
        .kpi-value {
            font-family: 'Outfit', sans-serif;
            font-size: 2rem;
            font-weight: 800;
            color: #38BDF8;
            margin-top: 4px;
        }
        .kpi-label {
            font-size: 0.85rem;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* Sidebar styling override */
        section[data-testid="stSidebar"] {
            background-color: #0F172A !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
        }
        
        /* Custom buttons styling */
        .stButton>button {
            background: linear-gradient(135deg, #3B82F6 0%, #818CF8 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 10px 24px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 15px 0 rgba(59, 130, 246, 0.3) !important;
            transition: all 0.2s ease !important;
        }
        .stButton>button:hover {
            transform: scale(1.02) !important;
            box-shadow: 0 6px 20px 0 rgba(129, 140, 248, 0.4) !important;
        }
        
        /* Custom logs container */
        .logs-box {
            font-family: 'Courier New', Courier, monospace;
            background-color: #020617;
            border: 1px solid #1E293B;
            border-radius: 8px;
            padding: 15px;
            color: #10B981;
            font-size: 0.9rem;
            overflow-y: scroll;
            height: 350px;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# Sidebar Telemetry information
st.sidebar.markdown("<h2 style='text-align:center;'>InsightPilot Telemetry</h2>", unsafe_allow_html=True)
st.sidebar.image("https://img.icons8.com/nolan/128/artificial-intelligence.png", width=100)

# Fetch DB Stats safely (DB_PATH is imported from config)
if os.path.exists(DB_PATH):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        cust_cnt = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transactions")
        tx_cnt = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM agent_logs")
        logs_cnt = cursor.fetchone()[0]
        
        conn.close()
    except Exception:
        cust_cnt, tx_cnt, logs_cnt = 0, 0, 0
else:
    cust_cnt, tx_cnt, logs_cnt = 0, 0, 0

st.sidebar.markdown(f"""
<div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); margin-top: 10px;">
    <p style="margin: 0; font-size: 0.85rem; color: #94A3B8;">DATALAKE METRICS</p>
    <div style="display:flex; justify-content:space-between; margin-top: 8px;">
        <span style="color:#E2E8F0;">Subscribers:</span>
        <strong style="color:#38BDF8;">{cust_cnt:,}</strong>
    </div>
    <div style="display:flex; justify-content:space-between; margin-top: 4px;">
        <span style="color:#E2E8F0;">Transactions:</span>
        <strong style="color:#38BDF8;">{tx_cnt:,}</strong>
    </div>
    <div style="display:flex; justify-content:space-between; margin-top: 4px;">
        <span style="color:#E2E8F0;">Cognitive Logs:</span>
        <strong style="color:#818CF8;">{logs_cnt:,}</strong>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="background: rgba(56,189,248,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(56,189,248,0.2); margin-top: 15px;">
    <p style="margin: 0; font-size: 0.85rem; color: #38BDF8; font-weight:600;">ACTIVE COGNITIVE AGENTS</p>
    <ul style="margin: 5px 0 0 0; padding-left: 15px; font-size: 0.85rem; color:#E2E8F0;">
        <li>🤖 Orchestrator Agent</li>
        <li>📈 Churn Intelligence</li>
        <li>🛡️ Fraud Investigation</li>
        <li>📊 Revenue Forecaster</li>
        <li>📝 Executive Reporter</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Main Page Layout
st.markdown("<h1 class='gradient-text' style='font-size: 3rem;'>INSIGHTPILOT BI PLATFORM</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size:1.2rem; color:#94A3B8;'>Enterprise-grade Multi-Agent System orchestrating predictions, risk analysis, and corporate forecasts offline.</p>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="glass-card">
        <h3>🤖 Cognitive Agent Chat Integration</h3>
        <p style="color:#94A3B8; font-size:0.95rem;">
            Interact directly with our Orchestrator Agent to run automated customer churn audits, transaction fraud inspections, and future corporate growth forecasts in real-time.
        </p>
        <p style="color: #38BDF8; font-weight:600; margin-top: 15px;">Key Features:</p>
        <ul style="color:#E2E8F0; font-size:0.9rem; padding-left: 20px;">
            <li>Dynamic natural language query parsing</li>
            <li>Multi-step task delegation between agents</li>
            <li>Step-by-step cognitive tracing (Thoughts/Actions/Observations)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
with col2:
    st.markdown("""
    <div class="glass-card">
        <h3>📊 Model Context Protocol (MCP) Tools</h3>
        <p style="color:#94A3B8; font-size:0.95rem;">
            InsightPilot operates with a local MCP server that hosts core database interfaces and machine learning pipelines as standard callable tools.
        </p>
        <p style="color: #38BDF8; font-weight:600; margin-top: 15px;">Active ML Pipelines:</p>
        <ul style="color:#E2E8F0; font-size:0.9rem; padding-left: 20px;">
            <li>SaaS Customer Churn Predictor (XGBoost Classifier)</li>
            <li>Transaction Anomaly & Fraud Score (Random Forest)</li>
            <li>Revenue Growth forecaster (Seasonality + Trend Ridge Regression)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="glass-card" style="text-align: center; padding: 40px 20px;">
    <h2>🚀 Start Exploring the BI Dashboard</h2>
    <p style="color:#94A3B8; max-width: 700px; margin: 0 auto 20px auto;">
        Use the sidebar navigation to visit individual data pages (Executive Overview, Churn, Fraud, Revenue), interact with the Agent Chat console, download compiled PDF reports, or monitor background model metrics.
    </p>
</div>
""", unsafe_allow_html=True)
