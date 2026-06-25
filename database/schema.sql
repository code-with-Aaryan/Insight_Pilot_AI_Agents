-- SQLite Database Schema for InsightPilot

-- Customers table: Stores subscriber details, churn status and churn model predictions
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    tenure INTEGER NOT NULL, -- in months
    monthly_charges REAL NOT NULL,
    total_charges REAL NOT NULL,
    contract_type TEXT NOT NULL, -- 'Month-to-month', 'One year', 'Two year'
    payment_method TEXT NOT NULL, -- 'Electronic check', 'Mailed check', 'Bank transfer', 'Credit card'
    paperless_billing INTEGER NOT NULL, -- 0 or 1
    tech_support TEXT NOT NULL, -- 'Yes', 'No', 'No internet service'
    online_security TEXT NOT NULL, -- 'Yes', 'No', 'No internet service'
    churn_probability REAL DEFAULT 0.0, -- predicted probability from XGBoost
    churn INTEGER NOT NULL DEFAULT 0, -- 0 = Active, 1 = Churned
    location_lat REAL, -- home latitude coordinate
    location_lon REAL  -- home longitude coordinate
);

-- Transactions table: Stores payment logs, merchant category, geolocation and fraud scoring
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    amount REAL NOT NULL,
    merchant TEXT NOT NULL,
    category TEXT NOT NULL, -- 'Retail', 'Travel', 'Food', 'Entertainment', 'Utilities', 'Financial'
    location_lat REAL NOT NULL,
    location_lon REAL NOT NULL,
    card_present INTEGER NOT NULL, -- 0 = No, 1 = Yes
    is_fraud INTEGER NOT NULL DEFAULT 0, -- 0 = Valid, 1 = Fraud
    fraud_score REAL DEFAULT 0.0, -- predicted score from Random Forest
    status TEXT NOT NULL DEFAULT 'Approved', -- 'Approved', 'Flagged', 'Declined'
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);

-- Revenue Forecast table: Stores aggregated monthly financial records and model forecasts
CREATE TABLE IF NOT EXISTS revenue_forecast (
    forecast_date TEXT PRIMARY KEY, -- 'YYYY-MM-DD' (monthly aggregations)
    historical_revenue REAL,
    forecasted_revenue REAL,
    lower_bound REAL,
    upper_bound REAL
);

-- Agent Logs table: Stores full trace audit of agent thoughts, decisions, actions, and outputs
CREATE TABLE IF NOT EXISTS agent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    session_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    thought TEXT,
    action TEXT,
    observation TEXT,
    output TEXT,
    token_usage INTEGER DEFAULT 0,
    cost REAL DEFAULT 0.0
);
