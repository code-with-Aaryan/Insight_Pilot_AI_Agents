import os
import sys
import base64
import sqlite3
import streamlit as st

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config import DB_PATH, PDF_REPORT_PATH, TXT_REPORT_PATH

from agents.executive_agent import ExecutiveReportAgent

st.set_page_config(page_title="PDF Report Generator | InsightPilot", page_icon="📝", layout="wide")

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

st.markdown("<h1 style='color: white;'>📝 Executive PDF Report Generator</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8;'>Compile cross-domain executive insights into printable PDF reports using ReportLab.</p>", unsafe_allow_html=True)

st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown("<h3>📋 Generate Document</h3>", unsafe_allow_html=True)
st.markdown("<p style='color:#94A3B8;'>Click below to run the Executive Agent. The agent will fetch database metrics, formulate the briefing structure, and build the document artifact.</p>", unsafe_allow_html=True)

gen_btn = st.button("Compile Executive PDF Report")
st.markdown("</div>", unsafe_allow_html=True)

if gen_btn:
    with st.spinner("Executive Agent gathering metrics and compiling PDF..."):
        agent = ExecutiveReportAgent()
        # Run report compilation
        report_md = agent.run("Compile corporate executive report")
        
        st.success("Report Compiled Successfully!")
        
        # Display the Markdown preview
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(report_md)
        st.markdown("</div>", unsafe_allow_html=True)
        
        pdf_path = PDF_REPORT_PATH
        txt_path = TXT_REPORT_PATH
        
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
            
            st.markdown("<h3>📥 Download Corporate Briefing</h3>", unsafe_allow_html=True)
            st.markdown(f'<a href="data:application/pdf;base64,{b64_pdf}" download="executive_report.pdf" style="text-decoration:none; padding:10px 24px; background:#10B981; color:white; font-weight:600; border-radius:10px; box-shadow:0 4px 15px rgba(16,185,129,0.3);">Download printable PDF Briefing</a>', unsafe_allow_html=True)
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            
        elif os.path.exists(txt_path):
            with open(txt_path, "r") as f:
                txt_data = f.read()
            b64_txt = base64.b64encode(txt_data.encode('utf-8')).decode('utf-8')
            
            st.warning("ReportLab not found in system. Downloaded fallback Text briefing.")
            st.markdown(f'<a href="data:text/plain;base64,{b64_txt}" download="executive_report.txt" style="text-decoration:none; padding:10px 24px; background:#F59E0B; color:white; font-weight:600; border-radius:10px;">Download Text Briefing</a>', unsafe_allow_html=True)
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        else:
            st.error("No report files found on disk.")
