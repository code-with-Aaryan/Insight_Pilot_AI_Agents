import os
import sys
import csv
import random
import sqlite3
import datetime
import pandas as pd
import numpy as np

# Add project root to sys.path to allow config import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import DB_PATH, CHURN_DATA_PATH, FRAUD_DATA_PATH

# Ensure data directory exists
os.makedirs(os.path.dirname(CHURN_DATA_PATH), exist_ok=True)

# Set random seeds for reproducibility
random.seed(42)
np.random.seed(42)

def generate_saas_churn_data(n_customers=1000):
    print(f"Generating {n_customers} customer profiles...")
    customers = []
    
    first_names = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
                   "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

    contract_types = ["Month-to-month", "One year", "Two year"]
    payment_methods = ["Electronic check", "Mailed check", "Bank transfer", "Credit card"]
    tech_supports = ["Yes", "No", "No internet service"]
    online_securities = ["Yes", "No", "No internet service"]
    
    base_date = datetime.datetime(2024, 6, 23)
    base_lat, base_lon = 37.7749, -122.4194

    for i in range(n_customers):
        customer_id = f"CUST-{10000 + i}"
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        email = f"{name.lower().replace(' ', '.')}@example.com"
        
        # Demographic & behavior correlation
        contract = random.choices(contract_types, weights=[0.5, 0.3, 0.2])[0]
        
        if contract == "Month-to-month":
            tenure = int(random.triangular(1, 24, 6)) # skewed to shorter tenure
            tech_support = random.choices(tech_supports, weights=[0.3, 0.6, 0.1])[0]
            online_security = random.choices(online_securities, weights=[0.3, 0.6, 0.1])[0]
        else:
            tenure = int(random.triangular(12, 72, 36)) # longer tenure
            tech_support = random.choices(tech_supports, weights=[0.6, 0.3, 0.1])[0]
            online_security = random.choices(online_securities, weights=[0.6, 0.3, 0.1])[0]
            
        monthly_charges = round(random.uniform(20.0, 120.0), 2)
        total_charges = round(monthly_charges * tenure, 2)
        payment_method = random.choice(payment_methods)
        paperless_billing = random.choices([1, 0], weights=[0.6, 0.4])[0]
        
        # Calculate churn probability using a heuristic logit
        # Churn risk increases with high monthly charges, low tenure, month-to-month contracts, and no tech support
        logit = -1.0
        logit += (monthly_charges / 50.0)
        logit -= (tenure / 15.0)
        if contract == "Month-to-month":
            logit += 1.5
        if tech_support == "No":
            logit += 0.8
        if online_security == "No":
            logit += 0.5
            
        prob = 1 / (1 + np.exp(-logit))
        churn = 1 if random.random() < prob else 0
        
        lat = round(base_lat + random.uniform(-0.15, 0.15), 5)
        lon = round(base_lon + random.uniform(-0.15, 0.15), 5)
        
        customers.append({
            "customer_id": customer_id,
            "name": name,
            "email": email,
            "tenure": tenure,
            "monthly_charges": monthly_charges,
            "total_charges": total_charges,
            "contract_type": contract,
            "payment_method": payment_method,
            "paperless_billing": paperless_billing,
            "tech_support": tech_support,
            "online_security": online_security,
            "churn_probability": round(float(prob), 4),
            "churn": churn,
            "location_lat": lat,
            "location_lon": lon
        })
        
    df = pd.DataFrame(customers)
    df.to_csv(CHURN_DATA_PATH, index=False)
    print("SaaS customer churn data generated.")
    return customers

def generate_transaction_data(customers, n_transactions=5000):
    print(f"Generating {n_transactions} transactions...")
    transactions = []
    
    merchants = {
        "Retail": ["Amazon", "Walmart", "Target", "BestBuy", "HomeDepot"],
        "Travel": ["Delta Air Lines", "Uber", "Airbnb", "Marriott", "Expedia"],
        "Food": ["Starbucks", "McDonalds", "UberEats", "Dominos", "Subway"],
        "Entertainment": ["Netflix", "Spotify", "Steam", "Ticketmaster", "AMC"],
        "Utilities": ["Comcast", "PG&E", "Verizon", "StateFarm", "WasteManagement"],
        "Financial": ["Chase Transfer", "Venmo", "ATM Cash Out", "Coinbase", "Brokerage"]
    }
    
    categories = list(merchants.keys())
    cust_ids = [c["customer_id"] for c in customers]
    
    # Base location (San Francisco center coordinates)
    base_lat, base_lon = 37.7749, -122.4194
    
    # Pre-generate standard geolocations for each customer (e.g. home coordinates)
    cust_homes = {
        c["customer_id"]: (
            c["location_lat"],
            c["location_lon"]
        ) for c in customers
    }
    
    start_date = datetime.datetime.now() - datetime.timedelta(days=90)
    
    for i in range(n_transactions):
        tx_id = f"TX-{100000 + i}"
        customer_id = random.choice(cust_ids)
        home_lat, home_lon = cust_homes[customer_id]
        
        category = random.choices(categories, weights=[0.4, 0.1, 0.2, 0.1, 0.15, 0.05])[0]
        merchant = random.choice(merchants[category])
        
        # Timestamp distribution
        tx_time = start_date + datetime.timedelta(
            seconds=random.randint(0, 90 * 24 * 3600)
        )
        
        # Fraud triggers
        # 1. Unusually large amount
        # 2. Travel category card_present with coordinates far from home
        # 3. Financial transaction at odd hour
        
        is_fraud_scenario = False
        fraud_trigger = random.random()
        
        card_present = 1 if category not in ["Travel", "Utilities", "Financial"] else 0
        if category in ["Food", "Retail"]:
            card_present = random.choices([1, 0], weights=[0.8, 0.2])[0]
            
        amount = round(np.random.exponential(scale=25.0) + 2.0, 2)
        
        # Force fraud scenarios for synthetic training labels
        if fraud_trigger < 0.03: # 3% base fraud rate
            is_fraud_scenario = True
            if random.random() < 0.5:
                # Scenario A: Massive amount
                amount = round(random.uniform(800.0, 3000.0), 2)
                category = "Financial"
                merchant = "ATM Cash Out" if random.random() < 0.5 else "Chase Transfer"
            else:
                # Scenario B: Travel transaction far away
                amount = round(random.uniform(200.0, 1500.0), 2)
                category = "Travel"
                merchant = "Marriott" if random.random() < 0.5 else "Delta Air Lines"
                card_present = 1
                
        # Geolocation selection
        if is_fraud_scenario and category == "Travel":
            # Coordinates far away (e.g. Europe/Asia distance offset)
            lat = home_lat + random.uniform(20.0, 50.0)
            lon = home_lon + random.uniform(40.0, 80.0)
        else:
            # Regular local transaction coordinates
            lat = home_lat + random.uniform(-0.02, 0.02)
            lon = home_lon + random.uniform(-0.02, 0.02)
            
        # Refined amount for normal tx
        if not is_fraud_scenario:
            if category == "Utilities":
                amount = round(random.uniform(50.0, 250.0), 2)
            elif category == "Travel":
                amount = round(random.uniform(100.0, 600.0), 2)
            elif category == "Food":
                amount = round(random.uniform(5.0, 45.0), 2)
                
        # Fraud heuristic score based on feature values
        score = 0.05
        if amount > 500.0:
            score += 0.3
        if amount > 1500.0:
            score += 0.4
        
        # Calculate distance
        distance = np.sqrt((lat - home_lat)**2 + (lon - home_lon)**2)
        if distance > 1.0:
            score += 0.4
        if tx_time.hour in [1, 2, 3, 4]:
            score += 0.15
        if card_present == 1 and distance > 5.0:
            score += 0.35
            
        score = min(score + random.uniform(-0.05, 0.05), 1.0)
        score = max(score, 0.0)
        
        # Determine actual label
        is_fraud = 1 if (is_fraud_scenario or score > 0.65) else 0
        if is_fraud:
            status = "Declined" if amount > 1000.0 else "Flagged"
            score = max(score, 0.7)
        else:
            status = "Approved"
            
        transactions.append({
            "transaction_id": tx_id,
            "customer_id": customer_id,
            "timestamp": tx_time.isoformat(),
            "amount": amount,
            "merchant": merchant,
            "category": category,
            "location_lat": round(lat, 5),
            "location_lon": round(lon, 5),
            "card_present": card_present,
            "is_fraud": is_fraud,
            "fraud_score": round(score, 4),
            "status": status
        })
        
    df = pd.DataFrame(transactions)
    df.to_csv(FRAUD_DATA_PATH, index=False)
    print("Financial transactions generated.")
    return transactions

def generate_revenue_forecast_history():
    print("Generating revenue forecasting history...")
    dates = pd.date_range(start="2024-06-01", periods=24, freq="ME")
    records = []
    
    # Baseline revenue starts around $50,000/month with linear growth and seasonality
    base_rev = 50000.0
    growth_rate = 1200.0 # Monthly average increase
    
    for i, dt in enumerate(dates):
        month_idx = dt.month
        # Introduce seasonal variations (higher in Dec/Nov, dip in Jan)
        seasonality = 1.0 + 0.08 * np.sin(2 * np.pi * month_idx / 12)
        noise = random.uniform(-1500.0, 1500.0)
        
        historical_revenue = round((base_rev + i * growth_rate) * seasonality + noise, 2)
        records.append({
            "forecast_date": dt.strftime("%Y-%m-%d"),
            "historical_revenue": historical_revenue,
            "forecasted_revenue": None,
            "lower_bound": None,
            "upper_bound": None
        })
        
    print("Revenue history generated.")
    return records

def seed_database():
    print("Seeding database...")
    db_path = DB_PATH
    
    # Load database manager
    from database.db_manager import DatabaseManager
    db = DatabaseManager(db_path)
    
    # Clean tables first
    with db.get_connection() as conn:
        conn.execute("DELETE FROM customers")
        conn.execute("DELETE FROM transactions")
        conn.execute("DELETE FROM revenue_forecast")
        conn.execute("DELETE FROM agent_logs")
        conn.commit()
        
    # Generate datasets
    customers = generate_saas_churn_data(1000)
    transactions = generate_transaction_data(customers, 5000)
    revenue = generate_revenue_forecast_history()
    
    # Insert Customers
    with db.get_connection() as conn:
        conn.executemany("""
            INSERT INTO customers (customer_id, name, email, tenure, monthly_charges, total_charges, contract_type, payment_method, paperless_billing, tech_support, online_security, churn_probability, churn, location_lat, location_lon)
            VALUES (:customer_id, :name, :email, :tenure, :monthly_charges, :total_charges, :contract_type, :payment_method, :paperless_billing, :tech_support, :online_security, :churn_probability, :churn, :location_lat, :location_lon)
        """, customers)
        
        # Insert Transactions
        conn.executemany("""
            INSERT INTO transactions (transaction_id, customer_id, timestamp, amount, merchant, category, location_lat, location_lon, card_present, is_fraud, fraud_score, status)
            VALUES (:transaction_id, :customer_id, :timestamp, :amount, :merchant, :category, :location_lat, :location_lon, :card_present, :is_fraud, :fraud_score, :status)
        """, transactions)
        
        # Insert Revenue
        conn.executemany("""
            INSERT INTO revenue_forecast (forecast_date, historical_revenue, forecasted_revenue, lower_bound, upper_bound)
            VALUES (:forecast_date, :historical_revenue, :forecasted_revenue, :lower_bound, :upper_bound)
        """, revenue)
        conn.commit()
        
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_database()
