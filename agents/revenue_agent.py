import re
from agents.base_agent import SimulatedAgent

class RevenueForecastAgent(SimulatedAgent):
    def __init__(self):
        super().__init__(
            name="Revenue Forecast Agent",
            instruction=(
                "You are an expert Corporate Financial Planning & Analysis (FP&A) Analyst. "
                "Your role is to evaluate historical monthly recurring revenue (MRR), "
                "fit forecasting models (trends, cyclical indices), and write financial outlook reports."
            ),
            tools=["forecast_revenue"]
        )

    def run(self, prompt: str, session_id: str = "default_session") -> str:
        # Extract forecast period using regex, default to 6 months
        months = 6
        match = re.search(r'(\d+)\s*month', prompt, re.IGNORECASE)
        if match:
            months = min(int(match.group(1)), 12) # capped at 12
            
        thought = f"Requested financial forecast for next {months} months. Invoking forecasting pipeline tool."
        action = f"forecast_revenue(months={months})"
        obs = self.execute_tool("forecast_revenue", {"months": months})
        
        if "error" in obs:
            output = f"Could not perform revenue forecasting: {obs['error']}"
            self.log_reasoning_step(session_id, thought, action, str(obs), output)
            return output
            
        growth = obs["growth_rate_pct"]
        latest_hist = obs["latest_historical_revenue"]
        end_forecast = obs["end_forecasted_revenue"]
        forecast_list = obs["forecast_records"]
        
        output = (
            f"### SaaS Revenue Projection & Financial Forecast ({months} Months)\n"
            f"- **Latest Month MRR:** ${latest_hist:,.2f}\n"
            f"- **Projected Month {months} MRR:** ${end_forecast:,.2f}\n"
            f"- **Expected Growth Rate:** `{growth:+.2f}%` over the forecast interval\n\n"
            f"**Month-by-Month Projection Details:**\n\n"
            f"| Forecast Date | Predicted Revenue | Lower Bound (95%) | Upper Bound (95%) |\n"
            f"| :--- | :--- | :--- | :--- |\n"
        )
        
        for r in forecast_list:
            output += f"| {r['forecast_date']} | **${r['forecasted_revenue']:,.2f}** | ${r['lower_bound']:,.2f} | ${r['upper_bound']:,.2f} |\n"
            
        output += (
            f"\n**Strategic Analysis:**\n"
            f"- **Growth Drivers:** The model indicates a steady upward trend driven by customer cohort expansion. "
            f"Seasonality parameters predict a cyclical surge during winter quarters.\n"
            f"- **Risks:** Revenue is highly sensitive to customer churn. A 1% increase in churn rate could compress month-end revenue to the lower confidence boundaries."
        )
        
        self.log_reasoning_step(session_id, thought, action, f"Forecasted {len(forecast_list)} periods successfully", output)
        return output
