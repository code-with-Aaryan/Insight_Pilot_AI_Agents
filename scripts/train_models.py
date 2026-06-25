import os
import sys
import pickle
import datetime
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import Ridge
from sklearn.metrics import classification_report, roc_auc_score, mean_squared_error
from xgboost import XGBClassifier

# Add project root to sys.path to allow config import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import (
    DB_PATH, CHURN_MODEL_PATH, FRAUD_MODEL_PATH, REVENUE_MODEL_PATH,
    CHURN_DATA_PATH, FRAUD_DATA_PATH
)

# Ensure models directory exists
os.makedirs(os.path.dirname(CHURN_MODEL_PATH), exist_ok=True)

# -----------------
# 1. Churn Prediction Model (XGBoost)
# -----------------
def train_churn_model():
    print("--- Training Churn Model (XGBoost) ---")
    data_path = CHURN_DATA_PATH
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}. Please run generate_data.py first.")
        
    df = pd.read_csv(data_path)
    
    # Feature Selection & Preprocessing
    feature_cols = [
        "tenure", "monthly_charges", "total_charges", 
        "contract_type", "payment_method", "tech_support", "online_security", "paperless_billing"
    ]
    X = df[feature_cols].copy()
    y = df["churn"]
    
    # One-hot encoding for categorical variables
    categorical_cols = ["contract_type", "payment_method", "tech_support", "online_security"]
    X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    # Keep track of feature names for inference alignment
    model_features = list(X.columns)
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Model Training
    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        eval_metric="logloss"
    )
    model.fit(X_train, y_train)
    
    # Evaluation
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]
    
    print("Churn Model Evaluation:")
    print(classification_report(y_test, preds))
    print(f"ROC AUC Score: {roc_auc_score(y_test, probs):.4f}")
    
    # Explanations (SHAP Heuristic or Actual SHAP)
    shap_importances = {}
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
        # Average absolute SHAP values per feature
        mean_shap = np.abs(shap_values).mean(axis=0)
        shap_importances = dict(zip(model_features, mean_shap.tolist()))
        print("SHAP values calculated successfully.")
    except Exception as e:
        print(f"SHAP library not available or failed ({e}). Falling back to feature importances.")
        importances = model.feature_importances_
        shap_importances = dict(zip(model_features, importances.tolist()))
        
    # Save Model Artifact
    artifact = {
        "model": model,
        "features": model_features,
        "shap_explanations": shap_importances,
        "categorical_cols": categorical_cols,
        "feature_cols_raw": feature_cols
    }
    
    model_path = CHURN_MODEL_PATH
    with open(model_path, "wb") as f:
        pickle.dump(artifact, f)
    print(f"Churn model saved to {model_path}\n")

# -----------------
# 2. Fraud Detection Model (Random Forest)
# -----------------
def train_fraud_model():
    print("--- Training Fraud Model (Random Forest) ---")
    data_path = FRAUD_DATA_PATH
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}.")
        
    df = pd.read_csv(data_path)
    
    # Feature Engineering from timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    
    # Feature Selection & Preprocessing
    feature_cols = [
        "amount", "card_present", "category", "hour", "day_of_week", "location_lat", "location_lon"
    ]
    X = df[feature_cols].copy()
    y = df["is_fraud"]
    
    # Encode categories
    categorical_cols = ["category"]
    X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    model_features = list(X.columns)
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Model Training
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        random_state=42,
        class_weight="balanced"
    )
    model.fit(X_train, y_train)
    
    # Evaluation
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]
    
    print("Fraud Model Evaluation:")
    print(classification_report(y_test, preds))
    print(f"ROC AUC Score: {roc_auc_score(y_test, probs):.4f}")
    
    # Explanations
    importances = model.feature_importances_
    feat_importances = dict(zip(model_features, importances.tolist()))
    
    # Save Model Artifact
    artifact = {
        "model": model,
        "features": model_features,
        "feature_importances": feat_importances,
        "categorical_cols": categorical_cols,
        "feature_cols_raw": feature_cols
    }
    
    model_path = FRAUD_MODEL_PATH
    with open(model_path, "wb") as f:
        pickle.dump(artifact, f)
    print(f"Fraud model saved to {model_path}\n")

# -----------------
# 3. Revenue Forecasting Model (Regression)
# -----------------
def train_revenue_forecast_model():
    print("--- Training Revenue Forecasting Model ---")
    db_path = DB_PATH
    
    from database.db_manager import DatabaseManager
    db = DatabaseManager(db_path)
    
    records = db.get_revenue_forecasts()
    df = pd.DataFrame(records)
    
    if df.empty or "historical_revenue" not in df.columns:
        print("No historical revenue records found in the database. Skipping forecasting model training.")
        return
        
    df = df[df["historical_revenue"].notna()].copy()
    
    # Feature Engineering: Month index and seasonality variables
    df["forecast_date"] = pd.to_datetime(df["forecast_date"])
    df = df.sort_values("forecast_date").reset_index(drop=True)
    
    df["time_idx"] = np.arange(len(df))
    df["month"] = df["forecast_date"].dt.month
    
    # Create sine and cosine representations for annual seasonality
    df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12)
    df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12)
    
    features = ["time_idx", "sin_month", "cos_month"]
    X = df[features]
    y = df["historical_revenue"]
    
    # Fit regression
    model = Ridge(alpha=1.0)
    model.fit(X, y)
    
    # Forecast for the next 12 months
    last_row = df.iloc[-1]
    last_date = last_row["forecast_date"]
    last_time_idx = last_row["time_idx"]
    
    forecast_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=12, freq="ME")
    forecast_records = []
    
    for i, f_date in enumerate(forecast_dates):
        time_idx = last_time_idx + 1 + i
        month = f_date.month
        sin_month = np.sin(2 * np.pi * month / 12)
        cos_month = np.cos(2 * np.pi * month / 12)
        
        pred_X = pd.DataFrame([[time_idx, sin_month, cos_month]], columns=features)
        pred_val = model.predict(pred_X)[0]
        
        # Uncertainty bounds (standard error approximation)
        lower_bound = pred_val - 2000.0 - (i * 150) # increasing uncertainty over time
        upper_bound = pred_val + 2000.0 + (i * 150)
        
        forecast_records.append({
            "forecast_date": f_date.strftime("%Y-%m-%d"),
            "historical_revenue": None,
            "forecasted_revenue": round(float(pred_val), 2),
            "lower_bound": round(float(lower_bound), 2),
            "upper_bound": round(float(upper_bound), 2)
        })
        
    # Write forecasts back to database
    with db.get_connection() as conn:
        conn.executemany("""
            INSERT OR REPLACE INTO revenue_forecast (forecast_date, historical_revenue, forecasted_revenue, lower_bound, upper_bound)
            VALUES (:forecast_date, :historical_revenue, :forecasted_revenue, :lower_bound, :upper_bound)
        """, forecast_records)
        conn.commit()
        
    print(f"Revenue forecast completed. Saved {len(forecast_records)} months forecasting into SQLite.")
    
    # Save the forecasting model
    artifact = {
        "model": model,
        "features": features,
        "last_time_idx": int(last_time_idx),
        "last_date": last_date.strftime("%Y-%m-%d")
    }
    
    model_path = REVENUE_MODEL_PATH
    with open(model_path, "wb") as f:
        pickle.dump(artifact, f)
    print(f"Revenue forecast model saved to {model_path}\n")

if __name__ == "__main__":
    train_churn_model()
    train_fraud_model()
    train_revenue_forecast_model()
    print("All ML models trained and saved.")
