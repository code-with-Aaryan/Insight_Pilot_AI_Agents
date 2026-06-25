# InsightPilot: 5-Minute YouTube Demo Video Script

**Title:** Building a Secure, Offline Multi-Agent BI Platform for Business (Kaggle AI Agents Capstone)
**Visual Style:** Screen recording of the Streamlit dashboard, code structure, and agent console with standard facecam overlay.
**Length:** ~5 Minutes

---

## 1. The Hook (0:00 - 0:30)

**[Visual]**
Presenter on camera. Cut to a screen recording showing the main page of the InsightPilot Streamlit dashboard with a dark glassmorphic UI.

**[Audio]**
"Data is the new oil—but in business, extracting actionable decisions from massive databases is still slow and manual. Business leaders wait days for custom reports, while cloud-based AI tools risk exposing sensitive company data to the public web. 

What if a team of specialized AI agents could securely audit your databases, analyze churn and fraud models, and write reports locally on your laptop without any API keys?

Introducing **InsightPilot**—a Multi-Agent Business Intelligence platform built for the Kaggle AI Agents Capstone."

---

## 2. The Problem & Solution (0:30 - 1:15)

**[Visual]**
Bullet points showing the three pillars: Churn Risk, Transaction Fraud, and Revenue Forecasts.

**[Audio]**
"We targeted two critical enterprise datasets: SaaS subscription metrics and financial credit transactions. 

Rather than sending this data to external clouds, we built a fully offline Multi-Agent system. InsightPilot uses local machine learning models (XGBoost, Random Forest, and Ridge regression) and orchestrates specialized cognitive agents using the Model Context Protocol (or MCP).

Let’s take a look at the system architecture."

---

## 3. System Architecture & MCP (1:15 - 2:00)

**[Visual]**
Display the Mermaid architecture diagram from the README. Use zoom-in on the Orchestrator and FastAPI MCP server.

**[Audio]**
"At the center of InsightPilot is the **Orchestrator Agent**. When a business question is submitted, the Orchestrator analyzes query intent and delegates tasks to our specialized agents. 

To keep the system modular and secure, we implemented a local FastAPI **Model Context Protocol (MCP)** server. The agents interact with databases and run ML models by calling standardized tool APIs. 

Every single thought, action, and observation is logged in a local SQLite database, creating a complete audit trail of the AI's reasoning."

---

## 4. Live Agent Chat & Cognitive Logs Demo (2:00 - 3:15)

**[Visual]**
Screen recording showing the **Agent Chat Console** page. Typing the prompt: `Verify SaaS customer CUST-10005 churn risk features.` Show the Orchestrator delegating the task and the Churn Agent outputting the profile, model assessments, and risk drivers.

**[Audio]**
"Let’s see the system in action. 

In our Agent Chat Console, we submit a query to evaluate customer `CUST-10005`. The Orchestrator automatically detects the customer prefix and routes the task to the Churn Intelligence Agent.

On the right side of the screen, we can inspect the live cognitive trace. We see the Churn Agent's Thoughts, the local MCP tool calls it executed, its Observations from the database, and the final output. The agent didn't just spit out a probability; it explained that month-to-month contracts and high monthly charges are the risk drivers, and wrote a customized customer retention plan."

---

## 5. Dashboard Visualizations & ML Pipelines (3:15 - 4:15)

**[Visual]**
Click through the pages:
- **Executive Overview:** Displaying metric cards and Plotly charts.
- **Customer Churn:** Showing the gauge dial and the SHAP feature importance bar chart.
- **Fraud Intelligence:** Showing the 2D coordinate distance deviation plot.
- **Revenue Forecasting:** Showing the revenue line chart with shaded confidence intervals.

**[Audio]**
"For business analysts, we built a complete Streamlit frontend dashboard. 

On the Churn Analytics page, we see the model's SHAP values plotted in an interactive bar chart, showing the impact weights of each feature. 

On the Fraud page, we inspect transaction `TX-100000`. The dashboard plots a spatial location map, displaying the physical distance deviation between the cardholder’s home base and the merchant. If it's too far or happens at an odd hour, the Random Forest model flags it.

Our Revenue page projects future monthly recurring revenue using Ridge regression, visualizing the growth trend along with shaded confidence intervals."

---

## 6. PDF Report Compilation & Results (4:15 - 4:45)

**[Visual]**
Navigate to the **PDF Report Generator** page. Click 'Compile Executive PDF Report', show the markdown preview, and download the PDF. Open the PDF to show the clean styled layout with headers and section descriptions.

**[Audio]**
"Finally, the Executive Agent can compile a corporate briefing report. With one click, it gathers metrics from the other agents, formats sections, and uses ReportLab to compile a print-ready PDF executive briefing, ready to be downloaded."

---

## 7. Vision & Closing (4:45 - 5:00)

**[Visual]**
Presenter on camera.

**[Audio]**
"InsightPilot demonstrates that multi-agent systems do not require complex cloud integrations or expensive API keys to deliver business value. By running locally, it ensures complete data privacy while providing explainable, actionable insights.

Thank you for watching, and check out our Kaggle writeup for the complete implementation details!"
