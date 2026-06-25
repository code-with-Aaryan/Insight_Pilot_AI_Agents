import os
import sys
import pickle
import sqlite3
import base64
import datetime
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Add project root to sys.path to allow config import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import (
    DB_PATH, CHURN_MODEL_PATH, FRAUD_MODEL_PATH, REVENUE_MODEL_PATH,
    PDF_REPORT_PATH, TXT_REPORT_PATH
)

app = FastAPI(
    title="InsightPilot Model Context Protocol (MCP) Server",
    description="Offline BI Tools and Machine Learning Inference API for SaaS Customer Churn, Transaction Fraud, and Revenue Forecasts.",
    version="1.0.0"
)

# Constants (imported from config.py)


# Helper for Database connection
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Helper to load models
def load_pickle(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)

# Request / Response Schemas
class CustomerQuery(BaseModel):
    customer_id: str

class ChurnPredictionInput(BaseModel):
    customer_id: str

class FraudPredictionInput(BaseModel):
    transaction_id: str

class RevenueForecastInput(BaseModel):
    months: int = Field(default=6, ge=1, le=12)

class PDFReportInput(BaseModel):
    title: str
    summary: str
    churn_analysis: str
    fraud_analysis: str
    revenue_analysis: str

# -----------------
# 1. get_customer_insights
# -----------------
@app.post("/tools/get_customer_insights")
def get_customer_insights(query: CustomerQuery):
    """Retrieve detailed database profile and transaction history for a specific customer."""
    try:
        with get_db() as conn:
            # Get customer details
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (query.customer_id,))
            cust_row = cursor.fetchone()
            
            if not cust_row:
                raise HTTPException(status_code=404, detail=f"Customer {query.customer_id} not found.")
                
            customer_info = dict(cust_row)
            
            # Get customer transactions
            cursor.execute("SELECT * FROM transactions WHERE customer_id = ? ORDER BY timestamp DESC LIMIT 20", (query.customer_id,))
            tx_rows = cursor.fetchall()
            transactions = [dict(r) for r in tx_rows]
            
            # Aggregate stats
            total_spent = sum(t["amount"] for t in transactions)
            fraud_alerts = sum(1 for t in transactions if t["is_fraud"] == 1)
            
            return {
                "customer_profile": customer_info,
                "transaction_summary": {
                    "recent_transactions_count": len(transactions),
                    "total_amount_recent": round(total_spent, 2),
                    "fraud_alerts_count": fraud_alerts
                },
                "recent_transactions": transactions
            }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# -----------------
# 2. predict_churn
# -----------------
@app.post("/tools/predict_churn")
def predict_churn(input_data: ChurnPredictionInput):
    """Run model inference on a customer to calculate their churn probability and explain risk factors."""
    try:
        # Load model artifact
        churn_artifact = load_pickle(CHURN_MODEL_PATH)
        if not churn_artifact:
            raise HTTPException(status_code=500, detail="Churn model artifact not found. Please run model training.")
            
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (input_data.customer_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Customer {input_data.customer_id} not found.")
            cust_data = dict(row)
            
        # Preprocess features
        raw_cols = churn_artifact["feature_cols_raw"]
        categorical_cols = churn_artifact["categorical_cols"]
        model_features = churn_artifact["features"]
        model = churn_artifact["model"]
        
        # Prepare matching row dictionary
        input_dict = {}
        for col in raw_cols:
            if col in cust_data:
                input_dict[col] = cust_data[col]
                
        # Build DataFrame with the single row
        df_inst = pd.DataFrame([input_dict])
        
        # Convert categoricals to dummy variables
        df_encoded = pd.get_dummies(df_inst, columns=categorical_cols, drop_first=True)
        
        # Align with training features (fill missing dummies with 0)
        for col in model_features:
            if col not in df_encoded.columns:
                df_encoded[col] = 0
                
        df_encoded = df_encoded[model_features]
        
        # Predict probability
        prob = float(model.predict_proba(df_encoded)[0, 1])
        label = 1 if prob >= 0.5 else 0
        
        # Save prediction back to database
        with get_db() as conn:
            conn.execute("UPDATE customers SET churn_probability = ?, churn = ? WHERE customer_id = ?", (prob, label, input_data.customer_id))
            conn.commit()
            
        # Explanations using model feature importances / SHAP
        shap_exp = churn_artifact["shap_explanations"]
        sorted_risks = sorted(shap_exp.items(), key=lambda x: x[1], reverse=True)
        
        # Heuristic assessment based on customer parameters
        risk_reasons = []
        if cust_data["contract_type"] == "Month-to-month":
            risk_reasons.append("Month-to-month contracts are highly correlated with churn risk.")
        if cust_data["tech_support"] == "No":
            risk_reasons.append("Lack of technical support is a key indicator of customer dissatisfaction.")
        if cust_data["tenure"] < 6:
            risk_reasons.append("New customers in their first 6 months have a high statistical churn rate.")
        if cust_data["monthly_charges"] > 80.0:
            risk_reasons.append(f"High monthly service charge (${cust_data['monthly_charges']}) increases price sensitivity.")
            
        return {
            "customer_id": input_data.customer_id,
            "churn_probability": round(prob, 4),
            "churn_risk_level": "High" if prob > 0.6 else "Medium" if prob > 0.3 else "Low",
            "feature_importance_explanations": sorted_risks[:5],
            "key_risk_reasons": risk_reasons if prob > 0.3 else ["No significant risks identified. Customer is stable."]
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# -----------------
# 3. detect_fraud
# -----------------
@app.post("/tools/detect_fraud")
def detect_fraud(input_data: FraudPredictionInput):
    """Run model inference to score a transaction for fraud risk and return anomaly metrics."""
    try:
        fraud_artifact = load_pickle(FRAUD_MODEL_PATH)
        if not fraud_artifact:
            raise HTTPException(status_code=500, detail="Fraud model artifact not found. Please train models.")
            
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (input_data.transaction_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Transaction {input_data.transaction_id} not found.")
            tx_data = dict(row)
            
            # Fetch customer details for base geolocation
            cursor.execute("SELECT tenure, monthly_charges, contract_type FROM customers WHERE customer_id = ?", (tx_data["customer_id"],))
            cust_row = cursor.fetchone()
            
        # Parse transaction time
        tx_dt = datetime.datetime.fromisoformat(tx_data["timestamp"])
        hour = tx_dt.hour
        day_of_week = tx_dt.weekday()
        
        # Build feature DataFrame
        inst_dict = {
            "amount": tx_data["amount"],
            "card_present": tx_data["card_present"],
            "hour": hour,
            "day_of_week": day_of_week,
            "location_lat": tx_data["location_lat"],
            "location_lon": tx_data["location_lon"],
            "category": tx_data["category"]
        }
        
        df_inst = pd.DataFrame([inst_dict])
        
        categorical_cols = fraud_artifact["categorical_cols"]
        model_features = fraud_artifact["features"]
        model = fraud_artifact["model"]
        
        df_encoded = pd.get_dummies(df_inst, columns=categorical_cols, drop_first=True)
        
        for col in model_features:
            if col not in df_encoded.columns:
                df_encoded[col] = 0
                
        df_encoded = df_encoded[model_features]
        
        # Run prediction
        prob = float(model.predict_proba(df_encoded)[0, 1])
        is_fraud = 1 if prob >= 0.5 else 0
        
        status = "Declined" if prob > 0.8 else "Flagged" if prob > 0.5 else "Approved"
        
        # Update database
        with get_db() as conn:
            conn.execute("UPDATE transactions SET fraud_score = ?, is_fraud = ?, status = ? WHERE transaction_id = ?", (prob, is_fraud, status, input_data.transaction_id))
            conn.commit()
            
        # Feature contributing factors
        anomalies = []
        if tx_data["amount"] > 500.0:
            anomalies.append(f"Unusually large payment transaction size: ${tx_data['amount']}")
        if hour in [1, 2, 3, 4]:
            anomalies.append(f"Suspicious activity hour: {hour}:00 AM (expected daytime/evening)")
        if tx_data["card_present"] == 0 and tx_data["amount"] > 200.0:
            anomalies.append("Card-Not-Present transaction exceeds high-risk dollar threshold.")
            
        return {
            "transaction_id": input_data.transaction_id,
            "fraud_score": round(prob, 4),
            "status": status,
            "is_fraud": is_fraud,
            "anomaly_indicators": anomalies if len(anomalies) > 0 else ["No significant anomalies detected."]
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# -----------------
# 4. forecast_revenue
# -----------------
@app.post("/tools/forecast_revenue")
def forecast_revenue(input_data: RevenueForecastInput):
    """Retrieve financial forecasting predictions for a specified number of future months."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            # Fetch historical and forecasted rows
            cursor.execute("SELECT * FROM revenue_forecast ORDER BY forecast_date ASC")
            rows = cursor.fetchall()
            all_records = [dict(r) for r in rows]
            
        historical = [r for r in all_records if r["historical_revenue"] is not None]
        forecasts = [r for r in all_records if r["forecasted_revenue"] is not None]
        
        # Slice forecasts to requested number of months
        sliced_forecasts = forecasts[:input_data.months]
        
        # Calculate key metrics
        last_hist_rev = historical[-1]["historical_revenue"] if historical else 0
        end_forecast_rev = sliced_forecasts[-1]["forecasted_revenue"] if sliced_forecasts else 0
        growth_rate = ((end_forecast_rev - last_hist_rev) / last_hist_rev) * 100 if last_hist_rev else 0.0
        
        return {
            "requested_months": input_data.months,
            "historical_months_count": len(historical),
            "growth_rate_pct": round(growth_rate, 2),
            "latest_historical_revenue": last_hist_rev,
            "end_forecasted_revenue": end_forecast_rev,
            "historical_records": historical[-12:], # last 12 months for dashboard
            "forecast_records": sliced_forecasts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------
# 5. generate_executive_report
# -----------------
@app.get("/tools/generate_executive_report")
def generate_executive_report():
    """Aggregate insights across customer churn, transaction fraud, and revenue models to compile a business health report."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Churn aggregates
            cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN churn_probability > 0.5 THEN 1 ELSE 0 END) as high_risk, AVG(churn_probability) as avg_prob, SUM(CASE WHEN churn_probability > 0.5 THEN monthly_charges ELSE 0.0 END) as value_at_risk FROM customers")
            churn_stats = dict(cursor.fetchone())
            
            # Fraud aggregates
            cursor.execute("SELECT COUNT(*) as total, SUM(is_fraud) as fraud_count, SUM(CASE WHEN is_fraud=1 THEN amount ELSE 0.0 END) as fraud_amount, SUM(CASE WHEN status='Flagged' THEN 1 ELSE 0 END) as flagged_count FROM transactions")
            fraud_stats = dict(cursor.fetchone())
            
            # Historical Revenue
            cursor.execute("SELECT AVG(historical_revenue) as avg_rev FROM revenue_forecast WHERE historical_revenue IS NOT NULL")
            rev_stats = dict(cursor.fetchone())
            
        # Forecast growth metrics (next 6 months)
        forecast_res = forecast_revenue(RevenueForecastInput(months=6))
        
        # Assemble aggregated corporate KPIs
        return {
            "report_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "customer_churn_kpis": {
                "total_monitored_subscribers": churn_stats["total"],
                "high_risk_subscribers": churn_stats["high_risk"] or 0,
                "average_churn_probability": round(churn_stats["avg_prob"] or 0.0, 4),
                "monthly_revenue_at_risk": round(churn_stats["value_at_risk"] or 0.0, 2)
            },
            "financial_fraud_kpis": {
                "total_monitored_transactions": fraud_stats["total"],
                "fraudulent_transactions_detected": fraud_stats["fraud_count"] or 0,
                "financial_loss_prevented": round(fraud_stats["fraud_amount"] or 0.0, 2),
                "flagged_pending_investigations": fraud_stats["flagged_count"] or 0
            },
            "revenue_performance_kpis": {
                "historical_monthly_average": round(rev_stats["avg_rev"] or 0.0, 2),
                "current_monthly_baseline": forecast_res["latest_historical_revenue"],
                "projected_6month_revenue": forecast_res["end_forecasted_revenue"],
                "growth_outlook_pct": forecast_res["growth_rate_pct"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------
# 6. create_pdf_report
# -----------------
@app.post("/tools/create_pdf_report")
def create_pdf_report(report: PDFReportInput):
    """Generate a publication-quality PDF executive report using ReportLab and return a base64 encoded string."""
    try:
        # ReportLab generation code (with safe importing)
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            
            pdf_filename = PDF_REPORT_PATH
            os.makedirs(os.path.dirname(pdf_filename), exist_ok=True)
            
            doc = SimpleDocTemplate(pdf_filename, pagesize=letter,
                                    rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            
            styles = getSampleStyleSheet()
            
            # Custom styled palette (Sleek Professional Teal/Dark Navy)
            primary_color = colors.HexColor("#0D3B66")
            secondary_color = colors.HexColor("#00A896")
            text_color = colors.HexColor("#333333")
            
            title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontSize=24,
                leading=28,
                textColor=primary_color,
                spaceAfter=15
            )
            
            section_style = ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading2'],
                fontSize=14,
                leading=18,
                textColor=secondary_color,
                spaceBefore=15,
                spaceAfter=8
            )
            
            body_style = ParagraphStyle(
                'ReportBody',
                parent=styles['BodyText'],
                fontSize=10.5,
                leading=15,
                textColor=text_color,
                spaceAfter=10
            )
            
            story = []
            
            # Header
            story.append(Paragraph(report.title, title_style))
            story.append(Paragraph(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Platform: InsightPilot Offline", styles['Italic']))
            story.append(Spacer(1, 15))
            
            # Summary Section
            story.append(Paragraph("1. Executive Summary", section_style))
            story.append(Paragraph(report.summary, body_style))
            story.append(Spacer(1, 10))
            
            # Churn Section
            story.append(Paragraph("2. Customer Churn Intelligence", section_style))
            story.append(Paragraph(report.churn_analysis, body_style))
            story.append(Spacer(1, 10))
            
            # Fraud Section
            story.append(Paragraph("3. Transaction Fraud Investigation", section_style))
            story.append(Paragraph(report.fraud_analysis, body_style))
            story.append(Spacer(1, 10))
            
            # Revenue Section
            story.append(Paragraph("4. Revenue Forecasting & Growth Outlook", section_style))
            story.append(Paragraph(report.revenue_analysis, body_style))
            
            doc.build(story)
            
            # Read and encode to base64
            with open(pdf_filename, "rb") as f:
                pdf_bytes = f.read()
                pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                
            return {
                "message": "PDF Report generated successfully.",
                "file_path": pdf_filename,
                "pdf_base64": pdf_base64
            }
            
        except ImportError:
            # Fallback when reportlab is not installed
            fallback_filename = TXT_REPORT_PATH
            os.makedirs(os.path.dirname(fallback_filename), exist_ok=True)
            
            text_content = f"""
===================================================
{report.title}
Generated: {datetime.datetime.now().isoformat()}
===================================================

1. EXECUTIVE SUMMARY:
{report.summary}

2. CUSTOMER CHURN INTELLIGENCE:
{report.churn_analysis}

3. TRANSACTION FRAUD INVESTIGATION:
{report.fraud_analysis}

4. REVENUE FORECASTING & GROWTH OUTLOOK:
{report.revenue_analysis}
===================================================
            """
            with open(fallback_filename, "w") as f:
                f.write(text_content)
                
            txt_base64 = base64.b64encode(text_content.encode('utf-8')).decode('utf-8')
            
            return {
                "message": "ReportLab not installed. Fallback Text Report generated.",
                "file_path": fallback_filename,
                "pdf_base64": txt_base64
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------
# Model Context Protocol Compliant JSON Schema Info
# -----------------
@app.get("/mcp/list_tools")
def mcp_list_tools():
    """List available MCP tools for multi-agent capability discovery."""
    return {
        "tools": [
            {
                "name": "get_customer_insights",
                "description": "Retrieve detailed database profile and transaction history for a specific customer.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string", "description": "Unique identifier of the customer (e.g. CUST-10000)"}
                    },
                    "required": ["customer_id"]
                }
            },
            {
                "name": "predict_churn",
                "description": "Inference on customer data to calculate churn probability and risk reasons.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string", "description": "Unique customer ID"}
                    },
                    "required": ["customer_id"]
                }
            },
            {
                "name": "detect_fraud",
                "description": "Scans and scores a specific transaction record for fraudulent indicators.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "transaction_id": {"type": "string", "description": "Unique transaction ID (e.g. TX-100000)"}
                    },
                    "required": ["transaction_id"]
                }
            },
            {
                "name": "forecast_revenue",
                "description": "Retrieves revenue forecasting regression results for standard monthly intervals.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "months": {"type": "integer", "description": "Number of future months (1-12)"}
                    },
                    "required": ["months"]
                }
            },
            {
                "name": "generate_executive_report",
                "description": "Calculates platform-wide aggregated KPIs across churn, fraud, and financial models.",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "create_pdf_report",
                "description": "Constructs and saves an executive PDF report utilizing text analyses.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "summary": {"type": "string"},
                        "churn_analysis": {"type": "string"},
                        "fraud_analysis": {"type": "string"},
                        "revenue_analysis": {"type": "string"}
                    },
                    "required": ["title", "summary", "churn_analysis", "fraud_analysis", "revenue_analysis"]
                }
            }
        ]
    }

@app.post("/mcp/call_tool")
def mcp_call_tool(tool_name: str = Body(...), arguments: Dict[str, Any] = Body(...)):
    """Call a discovered tool by name with arguments following the MCP protocol structure."""
    if tool_name == "get_customer_insights":
        return get_customer_insights(CustomerQuery(**arguments))
    elif tool_name == "predict_churn":
        return predict_churn(ChurnPredictionInput(**arguments))
    elif tool_name == "detect_fraud":
        return detect_fraud(FraudPredictionInput(**arguments))
    elif tool_name == "forecast_revenue":
        return forecast_revenue(RevenueForecastInput(**arguments))
    elif tool_name == "generate_executive_report":
        return generate_executive_report()
    elif tool_name == "create_pdf_report":
        return create_pdf_report(PDFReportInput(**arguments))
    else:
        raise HTTPException(status_code=400, detail=f"Tool {tool_name} not supported by this server.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
