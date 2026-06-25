from agents.base_agent import SimulatedAgent

class ExecutiveReportAgent(SimulatedAgent):
    def __init__(self):
        super().__init__(
            name="Executive Report Agent",
            instruction=(
                "You are an expert Corporate Chief Operating Officer (COO) and Chief Financial Officer (CFO) Advisor. "
                "Your role is to aggregate inputs from customer success, risk/compliance, and financial forecasting, "
                "synthesize corporate performance reports, and produce PDF briefings."
            ),
            tools=["generate_executive_report", "create_pdf_report"]
        )

    def run(self, prompt: str, session_id: str = "default_session") -> str:
        # Step 1: Generate corporate aggregates
        thought1 = "Aggregating global KPIs from corporate data systems."
        action1 = "generate_executive_report()"
        obs1 = self.execute_tool("generate_executive_report", {})
        
        if "error" in obs1:
            output = f"Could not compile executive report: {obs1['error']}"
            self.log_reasoning_step(session_id, thought1, action1, str(obs1), output)
            return output
            
        churn = obs1["customer_churn_kpis"]
        fraud = obs1["financial_fraud_kpis"]
        rev = obs1["revenue_performance_kpis"]
        
        # Format subsections
        summary_text = (
            f"InsightPilot platform aggregates show steady financial progression with a monthly recurring revenue growth outlook "
            f"of {rev['growth_outlook_pct']:+.2f}% over the next six months. However, there is a customer revenue risk of "
            f"${churn['monthly_revenue_at_risk']:,.2f}/month due to {churn['high_risk_subscribers']} high-risk subscribers. "
            f"Security compliance has successfully blocked {fraud['fraudulent_transactions_detected']} fraud attempts, preventing "
            f"${fraud['financial_loss_prevented']:,.2f} in losses."
        )
        
        churn_text = (
            f"The customer portfolio has {churn['total_monitored_subscribers']} active accounts, with {churn['high_risk_subscribers']} "
            f"accounts flagged with churn probability exceeding 50%. The average churn probability sits at "
            f"{churn['average_churn_probability']*100:.2f}%. We recommend targeted campaigns to transition month-to-month contracts "
            f"to yearly terms."
        )
        
        fraud_text = (
            f"Out of {fraud['total_monitored_transactions']} transactions, we intercepted {fraud['fraudulent_transactions_detected']} "
            f"cases of credit/wire fraud. Placed {fraud['flagged_pending_investigations']} transactions on hold for verification. "
            f"Total financial losses prevented: ${fraud['financial_loss_prevented']:,.2f}."
        )
        
        rev_text = (
            f"Historical monthly recurring revenue averaged ${rev['historical_monthly_average']:,.2f}. Current MRR stands at "
            f"${rev['current_monthly_baseline']:,.2f}, and is forecasted to hit ${rev['projected_6month_revenue']:,.2f} in 6 months, "
            f"representing a positive growth forecast of {rev['growth_outlook_pct']:+.2f}%."
        )
        
        # Step 2: Compile PDF Executive Report
        thought2 = "Compiling visual PDF corporate briefing document."
        pdf_args = {
            "title": "InsightPilot Corporate Performance Executive Briefing",
            "summary": summary_text,
            "churn_analysis": churn_text,
            "fraud_analysis": fraud_text,
            "revenue_analysis": rev_text
        }
        action2 = f"create_pdf_report(title='InsightPilot...', ...)"
        obs2 = self.execute_tool("create_pdf_report", pdf_args)
        
        pdf_status = obs2.get("message", "PDF generation failed.")
        file_path = obs2.get("file_path", "N/A")
        
        output = (
            f"## INSIGHTPILOT EXECUTIVE STRATEGIC BRIEFING\n"
            f"*Compiled by Executive Report Agent | Status: {pdf_status}*\n\n"
            f"### 1. Executive Summary\n"
            f"{summary_text}\n\n"
            f"### 2. Subscription Churn & Success Metrics\n"
            f"{churn_text}\n\n"
            f"### 3. Compliance & Security Operations\n"
            f"{fraud_text}\n\n"
            f"### 4. Financial FP&A Outlook\n"
            f"{rev_text}\n\n"
            f"---\n"
            f"#### PDF Generation Artifact Details:\n"
            f"- **Storage Path:** `{file_path}`\n"
            f"- **Download Status:** Ready for client download via the reports panel.\n"
        )
        
        self.log_reasoning_step(session_id, f"{thought1}\n{thought2}", f"1. {action1}\n2. {action2}", f"Aggregates: {obs1}\nPDF result: {obs2}", output)
        return output
