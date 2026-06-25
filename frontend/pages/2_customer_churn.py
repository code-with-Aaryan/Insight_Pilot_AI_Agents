import os
import sys
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config import DB_PATH, CHURN_MODEL_PATH

from agents.churn_agent import ChurnIntelligenceAgent

# Configuration
st.set_page_config(page_title="Customer Churn Analytics | InsightPilot", page_icon="📈", layout="wide")

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

st.markdown("<h1 style='color: white;'>📈 SaaS Customer Churn Analytics</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8;'>Explainable XGBoost predictions and churn risk factors analysis per subscriber.</p>", unsafe_allow_html=True)

# Search interface
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown("<h3>🔍 Inspect Subscriber Account</h3>", unsafe_allow_html=True)

search_col, button_col = st.columns([3, 1])
with search_col:
    search_id = st.text_input("Enter Customer ID (e.g., CUST-10005, CUST-10012, etc.):", value="CUST-10005").strip()

with button_col:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    analyze_btn = st.button("Trigger Agent Analysis")

st.markdown("</div>", unsafe_allow_html=True)

# Fetch customer details
conn = sqlite3.connect(DB_PATH)
df_cust = pd.read_sql_query("SELECT * FROM customers WHERE customer_id = ?", conn, params=(search_id,))
conn.close()

if df_cust.empty:
    st.warning(f"Subscriber '{search_id}' not found in database. Enter a valid customer ID.")
else:
    cust = df_cust.iloc[0]
    
    col_info, col_gauge = st.columns([2, 1])
    
    with col_info:
        st.markdown(f"""
        <div class="glass-card">
            <h3>👤 Subscriber Profile: {cust['name']}</h3>
            <p><strong>Email:</strong> {cust['email']}</p>
            <hr style="border-color: rgba(255,255,255,0.05);"/>
            <div style="display:flex; justify-content:space-between; margin-bottom: 8px;">
                <span>Tenure:</span>
                <strong>{cust['tenure']} Months</strong>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom: 8px;">
                <span>Contract Type:</span>
                <strong>{cust['contract_type']}</strong>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom: 8px;">
                <span>Monthly Recurring Charges:</span>
                <strong>${cust['monthly_charges']:.2f}</strong>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom: 8px;">
                <span>Payment Billing Method:</span>
                <strong>{cust['payment_method']}</strong>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom: 8px;">
                <span>Technical Support Package:</span>
                <strong>{cust['tech_support']}</strong>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span>Online Security Package:</span>
                <strong>{cust['online_security']}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_gauge:
        st.markdown("<div class='glass-card' style='height: 310px;'>", unsafe_allow_html=True)
        prob = cust['churn_probability']
        
        # Color coding risk dial
        dial_color = "#10B981" if prob < 0.3 else "#F59E0B" if prob < 0.6 else "#EF4444"
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = prob * 100,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "<b>Churn Probability</b>", 'font': {'color': '#E2E8F0', 'size': 16}},
            number = {'suffix': "%", 'font': {'color': '#FFFFFF', 'size': 36}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94A3B8"},
                'bar': {'color': dial_color},
                'bgcolor': "rgba(15, 23, 42, 0.6)",
                'borderwidth': 1,
                'bordercolor': "rgba(255,255,255,0.05)",
                'steps': [
                    {'range': [0, 30], 'color': 'rgba(16, 185, 129, 0.1)'},
                    {'range': [30, 60], 'color': 'rgba(245, 158, 11, 0.1)'},
                    {'range': [60, 100], 'color': 'rgba(239, 68, 68, 0.1)'}
                ],
            }
        ))
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20),
            height=260
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Actionable Agent Insights
    if analyze_btn:
        st.markdown("<h3>🤖 Simulated Agent Analysis Trace</h3>", unsafe_allow_html=True)
        with st.spinner("Agent running cognitive ReAct loop offline..."):
            agent = ChurnIntelligenceAgent()
            report = agent.run(f"Evaluate churn risk for customer {search_id}")
            
            # Show agent steps from DB
            conn = sqlite3.connect(DB_PATH)
            df_logs = pd.read_sql_query("SELECT thought, action, observation FROM agent_logs ORDER BY id DESC LIMIT 1", conn)
            conn.close()
            
            if not df_logs.empty:
                step = df_logs.iloc[0]
                with st.expander("👁️ View Agent Inner Cognitive Steps (Thought-Action-Observation)"):
                    st.markdown(f"**Thought:**\n`{step['thought']}`")
                    st.markdown(f"**Action Executed:**\n`{step['action']}`")
                    st.markdown(f"**Observation Result:**\n`{step['observation']}`")
            
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown(report)
            st.markdown("</div>", unsafe_allow_html=True)

    # SHAP Explanations Chart
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>📊 Explainable AI - Feature Importance Weights (SHAP)</h3>", unsafe_allow_html=True)
    
    # Load feature importances from pickled model
    import pickle
    import os
    if os.path.exists(CHURN_MODEL_PATH):
        with open(CHURN_MODEL_PATH, 'rb') as f:
            artifact = pickle.load(f)
        shap_data = artifact.get("shap_explanations", {})
        
        # Sort and plot
        df_shap = pd.DataFrame(list(shap_data.items()), columns=["Feature", "Impact Strength"])
        df_shap = df_shap.sort_values(by="Impact Strength", ascending=True)
        
        fig_shap = px.bar(
            df_shap, y="Feature", x="Impact Strength",
            orientation='h',
            color="Impact Strength",
            color_continuous_scale=px.colors.sequential.Tealgrn
        )
        fig_shap.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#E2E8F0"),
            xaxis=dict(gridcolor="#1E293B"),
            yaxis=dict(gridcolor="#1E293B"),
            margin=dict(l=40, r=40, t=10, b=40),
            height=300
        )
        st.plotly_chart(fig_shap, use_container_width=True)
    else:
        st.info("No trained churn model pickle found to extract feature importances.")
    st.markdown("</div>", unsafe_allow_html=True)

# Bulk High Risk Table
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown("<h3>📋 Flagged High Churn Risk SaaS Accounts</h3>", unsafe_allow_html=True)
conn = sqlite3.connect(DB_PATH)
df_high_risk = pd.read_sql_query("""
    SELECT customer_id, name, tenure, contract_type, monthly_charges, churn_probability
    FROM customers 
    WHERE churn_probability > 0.5
    ORDER BY churn_probability DESC LIMIT 10
""", conn)
conn.close()

if df_high_risk.empty:
    st.success("No subscribers with high risk (>50%) currently recorded.")
else:
    st.dataframe(df_high_risk, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)
