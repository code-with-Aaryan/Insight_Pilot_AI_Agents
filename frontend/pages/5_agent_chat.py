import os
import sys
import sqlite3
import pandas as pd
import streamlit as st
import textwrap

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config import DB_PATH

from agents.orchestrator import OrchestratorAgent

st.set_page_config(page_title="Agent Chat Console | InsightPilot", page_icon="💬", layout="wide")

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
    # Compile the entire conversation content into a single HTML string
    chat_content = "<h3>💬 Conversation</h3>"
    if not st.session_state.chat_history:
        chat_content += "<div style='color: #94A3B8; font-style: italic; padding: 10px;'>No messages yet. Send a query below or select a quick prompt to start.</div>"
    else:
        for role, text in st.session_state.chat_history:
            if role == "user":
                chat_content += textwrap.dedent(f"""
                <div style="margin-bottom: 12px; padding: 10px; background: rgba(56, 189, 248, 0.05); border-radius: 8px; border-left: 3px solid #38BDF8;">
                    <div style="color: #38BDF8; font-weight: 600; font-size: 0.85rem; margin-bottom: 4px;">👤 YOU</div>
                    <div style="color: #E2E8F0; font-size: 0.95rem;">{text}</div>
                </div>
                """)
            else:
                # Basic markdown conversion (e.g. bold to <strong>, newlines to <br/>)
                import re
                formatted = text
                # Escape HTML tags first
                import html
                formatted = html.escape(formatted)
                # Convert **bold**
                formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted)
                # Convert *italic*
                formatted = re.sub(r'\*(.*?)\*', r'<em>\1</em>', formatted)
                # Convert `code`
                formatted = re.sub(r'`(.*?)`', r'<code style="background: rgba(0,0,0,0.3); padding: 2px 4px; border-radius: 4px; color: #F59E0B;">\1</code>', formatted)
                # Convert newlines to <br/>
                formatted = formatted.replace('\n', '<br/>')
                
                chat_content += textwrap.dedent(f"""
                <div style="margin-bottom: 12px; padding: 10px; background: rgba(129, 140, 248, 0.05); border-radius: 8px; border-left: 3px solid #818CF8;">
                    <div style="color: #818CF8; font-weight: 600; font-size: 0.85rem; margin-bottom: 4px;">🤖 ORCHESTRATOR</div>
                    <div style="color: #E2E8F0; font-size: 0.95rem; line-height: 1.5;">{formatted}</div>
                </div>
                """)
                
    st.markdown(textwrap.dedent(f"""
    <div class="glass-card" style="height: 520px; overflow-y: auto;">
        {chat_content}
    </div>
    """), unsafe_allow_html=True)

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
    log_content = "<h3>👁️ Live Multi-Agent Cognitive Trace</h3>"
    log_content += "<p style='color:#94A3B8; font-size:0.8rem; margin-bottom: 15px;'>Step-by-step reasoning logs (Thoughts, Actions, and Observations) recorded in SQLite database.</p>"
    
    # Fetch logs from DB for the current session
    conn = sqlite3.connect(DB_PATH)
    df_logs = pd.read_sql_query(
        "SELECT timestamp, agent_name, thought, action, observation, output, token_usage, cost FROM agent_logs WHERE session_id = ? ORDER BY id ASC", 
        conn, params=(st.session_state.session_id,)
    )
    conn.close()
    
    if df_logs.empty:
        log_content += textwrap.dedent("""
        <div style="background: rgba(15, 23, 42, 0.4); padding: 15px; border-radius: 8px; border: 1px dashed rgba(255,255,255,0.1); color: #94A3B8; text-align: center; font-size: 0.9rem;">
            No active session trace logs. Submit a query to inspect agent cognitive steps.
        </div>
        """)
    else:
        for idx, row in df_logs.iterrows():
            import html
            thought_escaped = html.escape(str(row['thought'] or ''))
            action_escaped = html.escape(str(row['action'] or ''))
            obs_escaped = html.escape(str((row['observation'] or '')[:200]))
            
            log_content += textwrap.dedent(f"""
            <div style="background: rgba(15, 23, 42, 0.7); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 12px;">
                <div style="font-family: 'Outfit', sans-serif; color: #38BDF8; font-weight: 700; margin-bottom: 5px;">🤖 {row['agent_name']}</div>
                <div style="font-size: 0.75rem; color:#94A3B8; margin-bottom:8px;">{row['timestamp']} | Tokens: {row['token_usage']} | Est. Cost: ${row['cost']:.6f}</div>
                <p style="margin-bottom: 4px;"><span style="color:#818CF8; font-weight:600;">Thought:</span><br/><code style="color:#E2E8F0; font-size:0.85rem; white-space: pre-wrap; word-break: break-all;">{thought_escaped}</code></p>
                <p style="margin-bottom: 4px;"><span style="color:#F59E0B; font-weight:600;">Action/Tool Call:</span><br/><code style="color:#F59E0B; font-size:0.85rem; white-space: pre-wrap; word-break: break-all;">{action_escaped}</code></p>
                <p style="margin-bottom: 4px;"><span style="color:#10B981; font-weight:600;">Observation:</span><br/><code style="color:#10B981; font-size:0.85rem; white-space: pre-wrap; word-break: break-all;">{obs_escaped}...</code></p>
            </div>
            """)
            
    st.markdown(textwrap.dedent(f"""
    <div class="glass-card" style="height: 600px; overflow-y: auto;">
        {log_content}
    </div>
    """), unsafe_allow_html=True)
