# Kaggle AI Agents Capstone Writeup: InsightPilot
**Track:** Agents for Business  
**Submission Title:** InsightPilot: An Offline Multi-Agent Business Intelligence Platform with Explainable ML and MCP Tool Binding

---

## 1. Project Overview & Executive Summary

InsightPilot is an offline, multi-agent business intelligence (BI) platform engineered to address the operational and cognitive bottlenecks of modern corporate data analytics. Standard BI pipelines rely on manual data extraction, disparate ML scripts, and slow visualization rendering. InsightPilot transforms this paradigm by establishing a team of collaborative AI agents that autonomously query corporate databases, execute complex machine learning classifiers, trace reasoning steps using the ReAct (Reasoning and Acting) loop, and compile publication-quality PDF briefings.

To make the system viable for secure corporate environments, InsightPilot is designed to run 100% locally and offline on CPU resources. It uses an offline Agent Simulation Engine that executes predictions and aggregates insights. The agents interact with databases and ML models via FastAPI-based **Model Context Protocol (MCP)** tool specifications. By combining local machine learning models (XGBoost for SaaS subscription churn, Random Forest for transaction fraud detection, and Ridge regression for monthly financial forecasts) with a robust multi-agent orchestration architecture, InsightPilot provides a secure and explainable intelligence ecosystem for business decision-makers.

---

## 2. The Business Problem & Operational Bottlenecks

Data-driven enterprises face three core problems in their BI workflows:
1.  **Analytical Latency:** Business leaders often wait hours or days for data engineering teams to write SQL queries and compile reports.
2.  **Lack of Security in Cloud AI:** Deploying cloud-based Large Language Models (LLMs) poses compliance risks due to the transmission of sensitive personally identifiable information (PII) and financial logs to external servers.
3.  **Black-Box ML Predictions:** Standard ML systems spit out risk scores without explaining the underlying risk drivers, leading to lack of trust from decision-makers.

SaaS organizations need a secure, immediate, and explainable interface to monitor customer subscription health, mitigate transaction fraud, and forecast monthly recurring revenue (MRR).

---

## 3. Why AI Agents?

Traditional dashboard systems are passive; they display metrics but do not investigate or recommend strategies. Multi-agent systems introduce autonomous reasoning:
*   **Contextual Delegation:** An orchestrator agent parses user queries, splits them into structured tasks, and delegates them to specialized domains.
*   **ReAct Cognitive Loops:** Agents reason through problems step-by-step. They state their **Thought** processes, take **Actions** (such as querying tables or running models), observe results (**Observations**), and refine their final **Outputs**.
*   **Cooperative Specialization:** Instead of relying on a single general model, the system divides labor among domain-specific agents (Customer Success, Fraud Compliance, and Finance), maximizing precision.

---

## 4. Multi-Agent System Design

InsightPilot utilizes a hierarchical multi-agent structure managed by an Orchestrator:

```
              ┌───────────────────────────┐
              │    User Prompt Query      │
              └─────────────┬─────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │    Orchestrator Agent     │
              └─────────────┬─────────────┘
                            │
            ┌───────────────┼───────────────┬───────────────┐
            │               │               │               │
            ▼               ▼               ▼               ▼
      ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
      │   Churn   │   │   Fraud   │   │  Revenue  │   │ Executive │
      │  Agent    │   │  Agent    │   │  Agent    │   │  Agent    │
      └─────┬─────┘   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
            │               │               │               │
            └───────────────┼───────────────┴───────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │  MCP Server Tool Bindings │
              └─────────────┬─────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
     ┌─────────────┐                 ┌─────────────┐
     │ SQLite DB   │                 │ ML Pickles  │
     └─────────────┘                 └─────────────┘
```

1.  **Orchestrator Agent:** Acts as the gateway router. It parses intent (e.g. searching for a customer ID, a transaction ID, or requesting a revenue report) and routes execution to the correct agent.
2.  **Churn Intelligence Agent:** Equipped with tools to retrieve customer info and score subscription churn. It interprets the model's SHAP values and suggests contract changes or success rep calls.
3.  **Fraud Investigation Agent:** Audits transaction details. It checks geographic coordinates, spending patterns, and times, automatically flagging anomalies and formulating freeze or verification actions.
4.  **Revenue Forecast Agent:** Accesses forecasting pipelines to output monthly growth projections and visual tables with confidence intervals.
5.  **Executive Report Agent:** Consolidates outputs from the other agents and writes a markdown briefing, then calls ReportLab tools to compile a printable corporate PDF.

---

## 5. Model Context Protocol (MCP) Integration

Rather than coupling agent logic directly to databases, InsightPilot uses the **Model Context Protocol (MCP)**. This separates the agent's reasoning from the underlying data schemas:
*   The MCP Server is implemented in `mcp_server/main.py` using FastAPI.
*   It exposes standard tools: `get_customer_insights`, `predict_churn`, `detect_fraud`, `forecast_revenue`, `generate_executive_report`, and `create_pdf_report`.
*   Agents discover tools via the `/mcp/list_tools` endpoint, which returns standard JSON schema descriptions of inputs.
*   Tools are invoked via the `/mcp/call_tool` endpoint, ensuring that data access and ML inference remain modular and easily swappable without modifying agent code.

---

## 6. Machine Learning Components & Explainability

InsightPilot trains three specialized local models:
1.  **XGBoost Churn Classifier:** Fits features (tenure, charges, billing method, contract) to predict churn probability.
2.  **Random Forest Fraud Classifier:** Analyzes transaction sizes, times, geolocations, and category features to detect anomalies.
3.  **Ridge Regression Revenue Forecaster:** Predicts future MRR. It models linear growth trends along with sine and cosine monthly seasonal variables to handle annual fluctuations.

### Explainability (SHAP & Anomaly Signalling)
*   **Churn Explanations:** The Churn Agent extracts SHAP feature importances from `churn_model.pkl`. It translates these importances into human-readable narratives (e.g., identifying that month-to-month contracts and high monthly charges are the primary drivers of customer risk).
*   **Fraud Anomaly Scoring:** The Fraud Agent isolates specific transactional attributes (e.g., spending at 3:00 AM, spending far from a customer's registered coordinates) and logs them as distinct anomaly indicators.

---

## 7. Security Features

*   **100% Offline Local Inference:** The system operates without internet connectivity. No data is sent to external APIs, preserving commercial confidentiality.
*   **Cognitive Audit Logs:** All agent steps are logged in the SQLite `agent_logs` table. This allows security and system administrators to inspect the system's reasoning at any time.
*   **State Isolation:** Multi-agent sessions are structured with unique session IDs, isolating transaction audits from success planning data.

---

## 8. Results & Validation

During evaluation testing, the system demonstrated excellent technical performance:
*   **Churn Classifier:** Achieved **83.00% accuracy** and an **AUC ROC of 0.9016** on the test dataset.
*   **Fraud Classifier:** Achieved **100.00% accuracy** and **1.0000 AUC ROC** on synthetic anomalous transactions.
*   **Revenue Forecasting:** Captured linear expansion trends (+1200/month) and cyclical winter peaks, storing 12 months of future projections.
*   **End-to-End Orchestration:** The multi-agent workflow successfully routed customer profiles (e.g. CUST-10005) to Churn Intelligence, flagged risks, recommended actions, and updated database tables in a single run.

---

## 9. Business Value & ROI

InsightPilot delivers immediate value:
1.  **Churn Mitigation:** By flagging high-risk subscribers, customer success teams can target accounts at risk, directly saving monthly subscription revenue.
2.  **Fraud Prevention:** Intercepting fraudulent wire transactions prevents direct capital loss and reduces payment disputes.
3.  **Automated FP&A:** Financial managers can generate revenue reports instantly, reducing reporting times from days to seconds.

---

## 10. Future Improvements

*   **Local LLM Integration:** Bind the base agent class to local GGUF models via Ollama to transition from templates to fully open-ended local reasoning.
*   **Graph Network Expansion:** Integrate graph databases to detect complex money laundering patterns across customer networks.
