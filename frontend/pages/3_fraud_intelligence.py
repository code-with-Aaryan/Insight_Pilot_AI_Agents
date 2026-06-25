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

from agents.fraud_agent import FraudInvestigationAgent

st.set_page_config(page_title="Fraud Intelligence | InsightPilot", page_icon="🛡️", layout="wide")

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

st.markdown("<h1 style='color: white;'>🛡️ Financial Transaction Fraud Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8;'>Screen transactions, evaluate geolocations, and track Random Forest anomaly scoring.</p>", unsafe_allow_html=True)

# Search box
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown("<h3>🔍 Inspect Transaction Record</h3>", unsafe_allow_html=True)

search_col, button_col = st.columns([3, 1])
with search_col:
    search_id = st.text_input("Enter Transaction ID (e.g., TX-100000, TX-100015, etc.):", value="TX-100000").strip()

with button_col:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    analyze_btn = st.button("Trigger Security Audit")

st.markdown("</div>", unsafe_allow_html=True)

# Query details
conn = sqlite3.connect(DB_PATH)
df_tx = pd.read_sql_query("SELECT * FROM transactions WHERE transaction_id = ?", conn, params=(search_id,))
conn.close()

if df_tx.empty:
    st.warning(f"Transaction ID '{search_id}' not found. Enter a valid ID.")
else:
    tx = df_tx.iloc[0]
    
    # Fetch customer home base location
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, location_lat, location_lon FROM customers WHERE customer_id = (SELECT customer_id FROM transactions WHERE transaction_id = ?)", (search_id,))
    cust_row = cursor.fetchone()
    conn.close()
    
    cust_name = cust_row[0] if cust_row else "Unknown Customer"
    home_lat = cust_row[1] if cust_row else 37.7749
    home_lon = cust_row[2] if cust_row else -122.4194
    
    col_details, col_map = st.columns([2, 1])
    
    with col_details:
        st.markdown(f"""
        <div class="glass-card">
            <h3>💳 Transaction: {tx['transaction_id']}</h3>
            <p><strong>Cardholder:</strong> {cust_name} ({tx['customer_id']})</p>
            <hr style="border-color: rgba(255,255,255,0.05);"/>
            <div style="display:flex; justify-content:space-between; margin-bottom: 8px;">
                <span>Merchant:</span>
                <strong>{tx['merchant']} ({tx['category']})</strong>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom: 8px;">
                <span>Amount:</span>
                <strong>${tx['amount']:.2f}</strong>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom: 8px;">
                <span>Timestamp:</span>
                <strong>{tx['timestamp']}</strong>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom: 8px;">
                <span>Card Present:</span>
                <strong>{'Yes' if tx['card_present'] == 1 else 'No'}</strong>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom: 8px;">
                <span>Model Fraud Score:</span>
                <strong style="color: {'#EF4444' if tx['fraud_score'] > 0.65 else '#10B981'};">{tx['fraud_score']*100:.2f}%</strong>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span>Compliance Status:</span>
                <strong style="text-transform: uppercase;">{tx['status']}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_map:
        st.markdown("<div class='glass-card' style='height: 310px;'>", unsafe_allow_html=True)
        # 2D Coordinate Deviation Plot
        fig_map = go.Figure()
        
        # Plot home coordinates
        fig_map.add_trace(go.Scatter(
            x=[home_lon], y=[home_lat],
            mode='markers', name='Cardholder Home',
            marker=dict(color='#10B981', size=14, symbol='star')
        ))
        
        # Plot transaction coordinates
        fig_map.add_trace(go.Scatter(
            x=[tx['location_lon']], y=[tx['location_lat']],
            mode='markers', name='Tx Merchant Location',
            marker=dict(color='#EF4444', size=14, symbol='x')
        ))
        
        # Line connecting them
        fig_map.add_trace(go.Scatter(
            x=[home_lon, tx['location_lon']], y=[home_lat, tx['location_lat']],
            mode='lines', name='Distance Delta',
            line=dict(color='rgba(255,255,255,0.2)', width=2, dash='dot')
        ))
        
        fig_map.update_layout(
            title="<b>Location Spacing Deviation Analysis</b>",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#E2E8F0"),
            xaxis=dict(gridcolor="#1E293B", showticklabels=False),
            yaxis=dict(gridcolor="#1E293B", showticklabels=False),
            margin=dict(l=20, r=20, t=40, b=20),
            height=260,
            showlegend=False
        )
        st.plotly_chart(fig_map, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Agent Audit
    if analyze_btn:
        st.markdown("<h3>🕵️ Simulated Investigator Agent Log</h3>", unsafe_allow_html=True)
        with st.spinner("Agent auditing compliance factors..."):
            agent = FraudInvestigationAgent()
            report = agent.run(f"Evaluate security scan for transaction {search_id}")
            
            # Show agent steps from DB
            conn = sqlite3.connect(DB_PATH)
            df_logs = pd.read_sql_query("SELECT thought, action, observation FROM agent_logs ORDER BY id DESC LIMIT 1", conn)
            conn.close()
            
            if not df_logs.empty:
                step = df_logs.iloc[0]
                with st.expander("👁️ View Agent Cognitive Sequence (Thoughts-Actions-Observations)"):
                    st.markdown(f"**Thought:**\n`{step['thought']}`")
                    st.markdown(f"**Action Executed:**\n`{step['action']}`")
                    st.markdown(f"**Observation Result:**\n`{step['observation']}`")
                    
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown(report)
            st.markdown("</div>", unsafe_allow_html=True)

# Grid of flagged transactions
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown("<h3>📋 Flagged & Declined Wire/Card Transactions Queue</h3>", unsafe_allow_html=True)
conn = sqlite3.connect(DB_PATH)
df_flagged = pd.read_sql_query("""
    SELECT transaction_id, customer_id, timestamp, amount, merchant, category, fraud_score, status 
    FROM transactions 
    WHERE status IN ('Declined', 'Flagged')
    ORDER BY timestamp DESC LIMIT 10
""", conn)
conn.close()

if df_flagged.empty:
    st.success("Clean Queue: No fraudulent or flagged transactions detected.")
else:
    st.dataframe(df_flagged, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)
