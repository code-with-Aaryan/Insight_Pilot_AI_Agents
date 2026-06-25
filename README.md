# InsightPilot – Multi-Agent Business Intelligence (BI) Platform

InsightPilot is a production-ready, fully-offline Multi-Agent Business Intelligence platform built for the **Kaggle AI Agents Capstone (Agents for Business track)**. 

The platform orchestrates a team of specialized cognitive agents (Orchestrator, Churn Success, Fraud compliance, and FP&A forecasting) to query relational databases, execute machine learning classifiers, and compile executive PDF briefings—all running entirely on local CPU resources with **zero external API key requirements**.

---

## 1. Project Overview & Business Impact

Modern enterprises suffer from siloed data and slow analytical response cycles. InsightPilot solves this by creating a collaborative team of specialized AI agents that interact with data lakes through standardized **Model Context Protocol (MCP)** tool APIs:

*   **SaaS Customer Success (Churn Agent):** Utilizes XGBoost models to calculate subscription churn risk and details key risk drivers (e.g., tenure, pricing, contract terms) using explainable SHAP values.
*   **Compliance & Risk Operations (Fraud Agent):** Analyzes transaction records using a Random Forest model, detecting coordinate-based geolocation deviations, anomalous spending, and nocturnal wire attempts.
*   **Corporate Forecasting (FP&A Revenue Agent):** Fits regression trends with 12-month cyclical Fourier features to project future monthly recurring revenue (MRR) along with 95% confidence intervals.
*   **Executive Leadership (Executive Agent):** Gathers cross-domain statistics and compiles publication-quality PDF corporate briefing documents using ReportLab.

---

## 2. Platform Architecture

InsightPilot's offline agent framework operates using a modular ReAct (Reasoning and Acting) execution pattern:

```mermaid
graph TD
    User([User Request]) --> Orch[Orchestrator Agent]
    
    Orch -->|Route Intent| ChurnA[Churn Intelligence Agent]
    Orch -->|Route Intent| FraudA[Fraud Investigation Agent]
    Orch -->|Route Intent| RevA[Revenue Forecast Agent]
    Orch -->|Route Intent| ExecA[Executive Report Agent]
    
    ChurnA -->|Call Tool| MCP[FastAPI MCP Tool Server]
    FraudA -->|Call Tool| MCP
    RevA -->|Call Tool| MCP
    ExecA -->|Call Tool| MCP
    
    MCP -->|Query| DB[(SQLite Database)]
    MCP -->|Predict| ML[ML Model Pickles]
    ExecA -->|Compile| PDF[ReportLab PDF Artifact]
    
    MCP -->|Observations| Agents[Specialized Agents]
    Agents -->|Formulate Reports| Orch
    Orch -->|Aggregate Output| User
```

---

## 3. Directory Layout

The project follows a clean, production-grade folder structure:

```
├── config/
│   └── settings.py              # Environment configuration loader
├── database/
│   ├── db_manager.py            # SQLite database helper and agent logs auditor
│   ├── schema.sql               # SQLite database schemas
│   └── insightpilot.db          # SQLite Database file (auto-generated)
├── data/
│   ├── saas_churn.csv           # Raw generated SaaS subscriber profiles
│   ├── financial_transactions.csv# Raw generated credit transactions
│   └── executive_report.pdf     # Generated PDF briefing (auto-generated)
├── scripts/
│   ├── generate_data.py         # Synthetic customer and transaction data generator
│   └── train_models.py          # Preprocessing, ML training, and pickle exporter
├── models/
│   ├── churn_model.pkl          # Trained XGBoost churn classifier
│   ├── fraud_model.pkl          # Trained Random Forest fraud classifier
│   └── revenue_forecast.pkl     # Trained Ridge MRR forecaster
├── agents/
│   ├── __init__.py
│   ├── base_agent.py            # Custom SimulatedAgent class with cognitive logs
│   ├── orchestrator.py          # Dynamic coordinator and query router
│   ├── churn_agent.py           # Subscriber churn success analyst
│   ├── fraud_agent.py           # Transaction fraud investigator
│   ├── revenue_agent.py         # Revenue forecaster (FP&A)
│   └── executive_agent.py       # Corporate executive reporter
├── mcp_server/
│   ├── __init__.py
│   └── main.py                  # FastAPI implementation of MCP tool endpoints
├── frontend/
│   ├── app.py                   # Streamlit main entrypoint
│   └── pages/                   # Multi-page dashboard layouts
│       ├── 1_executive_overview.py
│       ├── 2_customer_churn.py
│       ├── 3_fraud_intelligence.py
│       ├── 4_revenue_forecasting.py
│       ├── 5_agent_chat.py
│       ├── 6_pdf_report.py
│       └── 7_system_monitoring.py
├── deployment/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 4. Installation & Setup (Offline Local Run)

### Prerequisite
*   Python 3.10 or 3.11

### Step 1: Clone and Create Virtual Environment
```bash
git clone https://github.com/your-repo/InsightPilot.git
cd InsightPilot
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Packages
```bash
pip install -r requirements.txt
```

### Step 3: Seed Database and Train ML Models
Run the data generator to create synthetic datasets and populate the SQLite database, then train the models:
```bash
python scripts/generate_data.py
python scripts/train_models.py
```

### Step 4: Run Streamlit Frontend & MCP server
You can start uvicorn to host the MCP server, and launch the Streamlit frontend.
To run the Streamlit frontend:
```bash
streamlit run frontend/app.py
```
To run the FastAPI MCP server separately (Optional, since the frontend runs all tool logic directly via Python functions for convenience):
```bash
uvicorn mcp_server.main:app --host 127.0.0.1 --port 8000
```

---

## 5. Security & Verification Features

1.  **State Audit Logs:** Every single cognitive step (Thought, Action, Observation, Output) executed by any agent is logged in the SQLite `agent_logs` table. This provides complete audit trails of AI agent operations.
2.  **Deterministic Route Planning:** The `OrchestratorAgent` uses strict intent checks to route analysis to the appropriate sub-agent, preventing unexpected executions.
3.  **Local Isolation:** Since no external model API calls are made, no corporate database details or customer identities ever leave the local network.

---

## 6. Future Work
*   **Local LLM Integration:** Bind simulated agent behaviors to local LLMs (e.g., Llama-3 or Gemma-2 via Ollama).
*   **Graph Database Integration:** Incorporate graph neural networks (GNNs) for transaction relation modeling.
