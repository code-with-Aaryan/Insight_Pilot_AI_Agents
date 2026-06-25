import re
from agents.base_agent import SimulatedAgent

class FraudInvestigationAgent(SimulatedAgent):
    def __init__(self):
        super().__init__(
            name="Fraud Investigation Agent",
            instruction=(
                "You are an expert Anti-Money Laundering (AML) and Financial Fraud Investigator. "
                "Your role is to scan credit card and wire transactions, calculate fraud risk scores, "
                "correlate behavioral deviations (coordinates, unusual charges, odd times), "
                "and flag or approve transactions in real-time."
            ),
            tools=["detect_fraud", "get_customer_insights"]
        )

    def run(self, prompt: str, session_id: str = "default_session") -> str:
        tx_match = re.search(r'TX-\d+', prompt, re.IGNORECASE)
        cust_match = re.search(r'CUST-\d+', prompt, re.IGNORECASE)
        
        # Scenario A: Specific Transaction ID
        if tx_match:
            tx_id = tx_match.group(0).upper()
            
            thought1 = f"Transaction ID {tx_id} requested for security evaluation. Running Random Forest fraud classifier."
            action1 = f"detect_fraud(transaction_id={tx_id})"
            obs1 = self.execute_tool("detect_fraud", {"transaction_id": tx_id})
            
            if "error" in obs1:
                output = f"Error performing fraud analysis on {tx_id}: {obs1['error']}"
                self.log_reasoning_step(session_id, thought1, action1, str(obs1), output)
                return output
                
            thought2 = f"Transaction scored with fraud score {obs1['fraud_score']}. Fetching customer details to review location patterns."
            
            # Fetch transaction details from database to find customer_id
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (tx_id,))
                tx_row = cursor.fetchone()
                
            if tx_row:
                tx_data = dict(tx_row)
                customer_id = tx_data["customer_id"]
                action2 = f"get_customer_insights(customer_id={customer_id})"
                obs2 = self.execute_tool("get_customer_insights", {"customer_id": customer_id})
                profile_name = obs2["customer_profile"]["name"] if "customer_profile" in obs2 else "Unknown Customer"
            else:
                action2 = "N/A"
                obs2 = {}
                profile_name = "Unknown"
                
            score = obs1["fraud_score"]
            status = obs1["status"]
            anomalies = "\n".join([f"- {a}" for a in obs1["anomaly_indicators"]])
            
            output = (
                f"### Security Threat Assessment: {tx_id}\n"
                f"- **Cardholder Name:** {profile_name}\n"
                f"- **Transaction Amount:** ${tx_row['amount']:.2f} | **Merchant:** {tx_row['merchant']} ({tx_row['category']})\n"
                f"- **Timestamp:** {tx_row['timestamp']}\n\n"
                f"**Risk Evaluation:**\n"
                f"- **Fraud Risk Score:** `{score * 100:.2f}%` ({'High Risk Anomaly' if score > 0.65 else 'Valid Transaction'})\n"
                f"- **Automated Routing Status:** `{status}`\n\n"
                f"**Anomaly Signals Flagged:**\n"
                f"{anomalies}\n\n"
                f"**Investigative Action Plan:**\n"
            )
            
            if status == "Declined":
                output += (
                    f"1. **Account Freeze:** Block the card/account temporarily to prevent further transaction attempts.\n"
                    f"2. **SMS Verification:** Dispatched automatic two-factor alert requesting verification from the client.\n"
                    f"3. **AML Report:** Logged entry in regulatory logs for potential suspicious activity (SAR)."
                )
            elif status == "Flagged":
                output += (
                    f"1. **Outreach:** Send a push notification query to the customer's mobile application.\n"
                    f"2. **Manual Review:** Placed transaction in queue for investigator telephone validation.\n"
                    f"3. **Pending Status:** Hold funds transfer up to 12 hours pending confirmation."
                )
            else:
                output += (
                    f"1. **Approval:** Transaction meets security criteria. Funds cleared successfully.\n"
                    f"2. **Baseline:** Pattern registered to user standard travel/shopping coordinates."
                )
                
            self.log_reasoning_step(session_id, f"{thought1}\n{thought2}", f"1. {action1}\n2. {action2}", f"Fraud details: {obs1}\nCustomer profile: {str(obs2)[:150]}...", output)
            return output
            
        # Scenario B: Specific Customer ID
        elif cust_match:
            customer_id = cust_match.group(0).upper()
            
            thought = f"Customer {customer_id} transaction audit requested. Extracting transaction listing."
            action = f"get_customer_insights(customer_id={customer_id})"
            obs = self.execute_tool("get_customer_insights", {"customer_id": customer_id})
            
            if "error" in obs:
                output = f"Could not audit customer transactions: {obs['error']}"
                self.log_reasoning_step(session_id, thought, action, str(obs), output)
                return output
                
            tx_list = obs["recent_transactions"]
            alerts_count = obs["transaction_summary"]["fraud_alerts_count"]
            
            output = (
                f"### Customer Security Audit: {customer_id} ({obs['customer_profile']['name']})\n"
                f"- **Monitored Transactions:** {len(tx_list)}\n"
                f"- **Fraud/Security Alerts:** {alerts_count}\n\n"
                f"**Recent Transactions Scanned:**\n"
            )
            
            for tx in tx_list[:5]:
                alert_flag = "⚠️ FRAUD ALERT" if tx["is_fraud"] == 1 else "✅ SAFE"
                output += f"- `{tx['transaction_id']}`: {tx['timestamp']} - **{tx['merchant']}** | ${tx['amount']:.2f} | Score: {tx['fraud_score']*100:.1f}% ({alert_flag})\n"
                
            self.log_reasoning_step(session_id, thought, action, f"Retrieved {len(tx_list)} transactions", output)
            return output
            
        # Scenario C: Global Portfolio Review
        else:
            thought = "Global transaction review requested. Compiling database aggregates."
            action = "generate_executive_report"
            obs = self.execute_tool(action, {})
            
            stats = obs["financial_fraud_kpis"]
            output = (
                f"### Financial Fraud Intelligence global Dashboard\n"
                f"- **Total Transactions Monitored:** {stats['total_monitored_transactions']}\n"
                f"- **Fraud Incidents Stopped:** {stats['fraudulent_transactions_detected']}\n"
                f"- **Financial Losses Prevented:** ${stats['financial_loss_prevented']:,.2f}\n"
                f"- **Flagged Pending Manual Reviews:** {stats['flagged_pending_investigations']}\n\n"
                f"**Risk Landscape:**\n"
                f"- The overall portfolio fraud rate is stable at `{((stats['fraudulent_transactions_detected'] or 0)/(stats['total_monitored_transactions'] or 1))*100:.2f}%`.\n"
                f"- Travel bookings and high-value financial transfers remain the primary vectors of attempted fraud."
            )
            self.log_reasoning_step(session_id, thought, action, str(obs)[:300] + "...", output)
            return output
