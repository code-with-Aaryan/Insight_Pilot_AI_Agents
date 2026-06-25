import os
import sqlite3
import datetime
from typing import List, Dict, Any, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "c:/Users/aryan kumar kannojia/Music/Caposton_write_2/database/insightpilot.db"):
        self.db_path = db_path
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        schema_path = "c:/Users/aryan kumar kannojia/Music/Caposton_write_2/database/schema.sql"
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Schema file not found at {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()

    def log_agent_step(self, session_id: str, agent_name: str, thought: str, action: str, observation: str, output: str, token_usage: int = 0, cost: float = 0.0):
        query = """
            INSERT INTO agent_logs (timestamp, session_id, agent_name, thought, action, observation, output, token_usage, cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        timestamp = datetime.datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(query, (timestamp, session_id, agent_name, thought, action, observation, output, token_usage, cost))
            conn.commit()

    def get_agent_logs(self, limit: int = 200) -> List[Dict[str, Any]]:
        query = "SELECT * FROM agent_logs ORDER BY id DESC LIMIT ?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def clear_agent_logs(self):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM agent_logs")
            conn.commit()

    # Customer queries
    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM customers WHERE customer_id = ?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (customer_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_customers(self, limit: int = 1000) -> List[Dict[str, Any]]:
        query = "SELECT * FROM customers LIMIT ?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def update_customer_churn(self, customer_id: str, probability: float, churn_label: int):
        query = "UPDATE customers SET churn_probability = ?, churn = ? WHERE customer_id = ?"
        with self.get_connection() as conn:
            conn.execute(query, (probability, churn_label, customer_id))
            conn.commit()

    # Transaction queries
    def get_customer_transactions(self, customer_id: str) -> List[Dict[str, Any]]:
        query = "SELECT * FROM transactions WHERE customer_id = ? ORDER BY timestamp DESC"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (customer_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_all_transactions(self, limit: int = 2000) -> List[Dict[str, Any]]:
        query = "SELECT * FROM transactions ORDER BY timestamp DESC LIMIT ?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def update_transaction_fraud(self, transaction_id: str, score: float, is_fraud: int, status: str):
        query = "UPDATE transactions SET fraud_score = ?, is_fraud = ?, status = ? WHERE transaction_id = ?"
        with self.get_connection() as conn:
            conn.execute(query, (score, is_fraud, status, transaction_id))
            conn.commit()

    # Revenue forecast queries
    def insert_revenue_forecast(self, forecast_date: str, historical_revenue: Optional[float], forecasted_revenue: Optional[float], lower_bound: Optional[float], upper_bound: Optional[float]):
        query = """
            INSERT OR REPLACE INTO revenue_forecast (forecast_date, historical_revenue, forecasted_revenue, lower_bound, upper_bound)
            VALUES (?, ?, ?, ?, ?)
        """
        with self.get_connection() as conn:
            conn.execute(query, (forecast_date, historical_revenue, forecasted_revenue, lower_bound, upper_bound))
            conn.commit()

    def get_revenue_forecasts(self) -> List[Dict[str, Any]]:
        query = "SELECT * FROM revenue_forecast ORDER BY forecast_date ASC"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
