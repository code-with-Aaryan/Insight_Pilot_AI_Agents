import os
import sys
import sqlite3
import pandas as pd
import streamlit as st

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.orchestrator import OrchestratorAgent

st.set_page_config(page_title="Agent Chat Console | InsightPilot", page_icon="💬", layout="wide")

DB_PATH = "c:/Users/aryan kumar kannojia/Music/Caposton_write_2/database/insightpilot.db"

st.markdown("""
    <style>
    .main { background-color: #0A0E1A; color: #E2E8F0; }
    .glass-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(16px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 20px;
        margin-bottom: 15px;
    }
    .agent-header {
        font-family: 'Outfit', sans-serif;
        color: #38BDF8;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .thought-label { color: #818CF8; font-weight: 600; }
    .action-label { color: #F59E0B; font-weight: 600; }
    .obs-label { color: #10B981; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color: white;'>💬 Multi-Agent Cognitive Chat Console</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8;'>Interact with the Orchestrator Agent to run real-time audits on churn, fraud, and financials.</p>", unsafe_allow_html=True)

# Chat Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = f"chat-sess-{uuid.uuid4().hex[:8]}"

# Sidebar with quick action prompts
st.sidebar.markdown("### 💡 Quick Analytics Prompts")
prompts = [
    "Verify SaaS customer CUST-10005 churn risk features.",
    "Evaluate fraud anomaly logs for transaction TX-100015.",
    "Perform a 6-month SaaS revenue growth forecast.",
    "Generate corporate executive briefing report PDF.",
    "Show available platform tools listing."
]

for p in prompts:
    if st.sidebar.button(p, use_container_width=True):
        st.session_state.temp_prompt = p

# Main layout split: Left is Chat, Right is Live Cognitive Logs
chat_col, log_col = st.columns([3, 2])

with chat_col:
    st.markdown("<div class='glass-card' style='height: 520px; overflow-y: auto;'>", unsafe_allow_html=True)
    st.markdown("<h3>💬 Conversation</h3>", unsafe_allow_html=True)
    
    # Display previous history
    for role, text in st.session_state.chat_history:
        if role == "user":
            st.markdown(f"**👤 You:** {text}")
        else:
            st.markdown(f"**🤖 Orchestrator:**")
            st.markdown(text)
        st.markdown("<hr style='border-color:rgba(255,255,255,0.02); margin:8px 0;'/>", unsafe_allow_html=True)
        
    st.markdown("</div>", unsafe_allow_html=True)

    # Input Box
    user_input = ""
    if "temp_prompt" in st.session_state:
        user_input = st.session_state.temp_prompt
        del st.session_state.temp_prompt
        
    with st.form("chat_form", clear_on_submit=True):
        input_text = st.text_input("Ask a business question:", value=user_input, placeholder="e.g. Is CUST-10012 going to churn?")
        submit_chat = st.form_submit_value = st.form_submit_button("Send Query")
        
    if submit_chat and input_text:
        st.session_state.chat_history.append(("user", input_text))
        
        with st.spinner("Orchestrating agent workflows offline..."):
            orchestrator = OrchestratorAgent()
            response = orchestrator.run(input_text, session_id=st.session_state.session_id)
            st.session_state.chat_history.append(("assistant", response))
            
        # Rerun to update chat interface
        st.rerun()

with log_col:
    st.markdown("<div class='glass-card' style='height: 600px; overflow-y: auto;'>", unsafe_allow_html=True)
    st.markdown("<h3>👁️ Live Multi-Agent Cognitive Trace</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94A3B8; font-size:0.8rem;'>Step-by-step reasoning logs (Thoughts, Actions, and Observations) recorded in SQLite database.</p>", unsafe_allow_html=True)
    
    # Fetch logs from DB for the current session
    conn = sqlite3.connect(DB_PATH)
    df_logs = pd.read_sql_query(
        "SELECT timestamp, agent_name, thought, action, observation, output, token_usage, cost FROM agent_logs WHERE session_id = ? ORDER BY id ASC", 
        conn, params=(st.session_state.session_id,)
    )
    conn.close()
    
    if df_logs.empty:
        st.info("No active session trace logs. Submit a query to inspect agent cognitive steps.")
    else:
        for idx, row in df_logs.iterrows():
            st.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.7); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 12px;">
                <div class="agent-header">🤖 {row['agent_name']}</div>
                <div style="font-size: 0.75rem; color:#94A3B8; margin-bottom:8px;">{row['timestamp']} | Tokens: {row['token_usage']} | Est. Cost: ${row['cost']:.6f}</div>
                <p><span class="thought-label">Thought:</span><br/><code style="color:#E2E8F0;">{row['thought']}</code></p>
                <p><span class="action-label">Action/Tool Call:</span><br/><code style="color:#F59E0B;">{row['action']}</code></p>
                <p><span class="obs-label">Observation:</span><br/><code style="color:#10B981;">{row['observation'][:200]}...</code></p>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("</div>", unsafe_allow_html=True)
