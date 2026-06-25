import re
from agents.base_agent import SimulatedAgent

class ChurnIntelligenceAgent(SimulatedAgent):
    def __init__(self):
        super().__init__(
            name="Churn Intelligence Agent",
            instruction=(
                "You are an expert SaaS Customer Success and Retention Analyst. "
                "Your role is to assess customer churn risk, analyze subscription tenure, "
                "billing patterns, and technical support cases, and design preventative "
                "engagement campaigns to retain customers at risk."
            ),
            tools=["get_customer_insights", "predict_churn"]
        )

    def run(self, prompt: str, session_id: str = "default_session") -> str:
        # Extract Customer ID using regex
        match = re.search(r'CUST-\d+', prompt, re.IGNORECASE)
        
        if not match:
            # Fallback if no specific customer is requested
            thought = "The user has not specified a customer ID. I will aggregate global churn statistics from the database."
            action = "generate_executive_report"
            observation = self.execute_tool(action, {})
            
            total = observation["customer_churn_kpis"]["total_monitored_subscribers"]
            high_risk = observation["customer_churn_kpis"]["high_risk_subscribers"]
            avg_prob = observation["customer_churn_kpis"]["average_churn_probability"]
            val_at_risk = observation["customer_churn_kpis"]["monthly_revenue_at_risk"]
            
            output = (
                f"### Churn Intelligence Global Portfolio Review\n"
                f"- **Monitored SaaS Subscribers:** {total}\n"
                f"- **Subscribers with High Churn Risk (Prob > 50%):** {high_risk} ({(high_risk/total)*100:.1f}%)\n"
                f"- **Average Churn Probability:** {avg_prob * 100:.2f}%\n"
                f"- **Monthly Subscription Value at Risk:** ${val_at_risk:,.2f}\n\n"
                f"**Recommendations:**\n"
                f"1. Target high-risk month-to-month contracts with conversion offers to annual billing.\n"
                f"2. Initiate automated email onboarding sequences for new accounts (tenure < 6 months).\n"
                f"3. Increase online security bundle visibility for accounts experiencing tech support cases."
            )
            
            self.log_reasoning_step(session_id, thought, f"{action}()", str(observation)[:300] + "...", output)
            return output
            
        customer_id = match.group(0).upper()
        
        # Step 1: Gather Profile & History
        thought1 = f"Retrieving database profile and transaction history for customer {customer_id} to build feature context."
        action1 = f"get_customer_insights(customer_id={customer_id})"
        obs1 = self.execute_tool("get_customer_insights", {"customer_id": customer_id})
        
        if "error" in obs1:
            output = f"Could not analyze customer {customer_id}: {obs1['error']}"
            self.log_reasoning_step(session_id, thought1, action1, str(obs1), output)
            return output
            
        # Step 2: Predict Churn Probability using ML Model
        thought2 = f"Invoking XGBoost Churn Model on customer features for {customer_id} to evaluate risk probability."
        action2 = f"predict_churn(customer_id={customer_id})"
        obs2 = self.execute_tool("predict_churn", {"customer_id": customer_id})
        
        # Step 3: Synthesis and Output formatting
        profile = obs1["customer_profile"]
        prob = obs2["churn_probability"]
        risk_level = obs2["churn_risk_level"]
        key_reasons = "\n".join([f"- {r}" for r in obs2["key_risk_reasons"]])
        
        thought3 = f"Customer {customer_id} has a {risk_level} churn risk ({prob*100:.1f}%). Compiling personalized retention recommendations."
        
        output = (
            f"### Churn Risk Intelligence: {customer_id} ({profile['name']})\n"
            f"**Customer Profile Summary:**\n"
            f"- **Tenure:** {profile['tenure']} months\n"
            f"- **Contract Type:** {profile['contract_type']}\n"
            f"- **Monthly Charges:** ${profile['monthly_charges']:.2f}\n"
            f"- **Payment Method:** {profile['payment_method']}\n"
            f"- **Tech Support:** {profile['tech_support']} | **Online Security:** {profile['online_security']}\n\n"
            f"**Model Assessment:**\n"
            f"- **Churn Probability:** `{prob * 100:.2f}%` ({risk_level} Risk)\n\n"
            f"**Key Risk Drivers Identified:**\n"
            f"{key_reasons}\n\n"
            f"**Prescriptive Retention Actions:**\n"
        )
        
        if risk_level == "High":
            output += (
                f"1. **Contract Incentive:** Dispatch an immediate discount offer (e.g., 20% off) conditioned on transitioning to an annual contract.\n"
                f"2. **Support Touchpoint:** Assign a Dedicated Success Representative to reach out and resolve any pending support/onboarding friction.\n"
                f"3. **Complimentary Feature:** Activate 3-months of free Online Security/Tech Support add-ons to improve customer engagement."
            )
        elif risk_level == "Medium":
            output += (
                f"1. **Upsell Engagement:** Offer a bundle discount on Security + Tech Support tools to increase product value.\n"
                f"2. **Feedback Loop:** Trigger an automated customer satisfaction poll to capture product sentiment.\n"
                f"3. **Billing Transition:** Encourage switching to credit card / bank transfer payment to prevent accidental billing failures."
            )
        else:
            output += (
                f"1. **Nurture:** Customer is highly satisfied. Maintain standard newsletter and release communications.\n"
                f"2. **Referral Program:** Invite to advocate program and offer rewards for successful SaaS referrals."
            )
            
        # Log consolidated multi-step trace into database
        self.log_reasoning_step(session_id, f"{thought1}\n{thought2}\n{thought3}", f"1. {action1}\n2. {action2}", f"Profile: {str(obs1)[:150]}...\nPrediction: {str(obs2)[:150]}...", output)
        
        return output
