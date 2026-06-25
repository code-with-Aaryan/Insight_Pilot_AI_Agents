import os

# Compute the project root dynamically
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Database paths
DB_PATH = os.path.join(PROJECT_ROOT, "database", "insightpilot.db")
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "database", "schema.sql")

# Machine Learning Model paths
CHURN_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "churn_model.pkl")
FRAUD_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "fraud_model.pkl")
REVENUE_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "revenue_forecast.pkl")

# Data files paths
CHURN_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "saas_churn.csv")
FRAUD_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "financial_transactions.csv")

# PDF/Text Briefings output paths
PDF_REPORT_PATH = os.path.join(PROJECT_ROOT, "data", "executive_report.pdf")
TXT_REPORT_PATH = os.path.join(PROJECT_ROOT, "data", "executive_report.txt")
