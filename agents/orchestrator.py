import re
import uuid
from typing import Dict, Any
from agents.base_agent import SimulatedAgent
from agents.churn_agent import ChurnIntelligenceAgent
from agents.fraud_agent import FraudInvestigationAgent
from agents.revenue_agent import RevenueForecastAgent
from agents.executive_agent import ExecutiveReportAgent

class OrchestratorAgent(SimulatedAgent):
    def __init__(self):
        super().__init__(
            name="Orchestrator Agent",
            instruction=(
                "You are the central coordinator and router for InsightPilot. "
                "Your role is to interpret incoming business intelligence queries, "
                "delegate them to the appropriate specialized intelligence agents, "
                "monitor execution, and compile the unified final response."
            )
        )
        self.agents = {
            "churn": ChurnIntelligenceAgent(),
            "fraud": FraudInvestigationAgent(),
            "revenue": RevenueForecastAgent(),
            "executive": ExecutiveReportAgent()
        }

    def route_query(self, query: str) -> str:
        """Analyze query syntax and match keywords to route to the correct agent."""
        query_lower = query.lower()
        
        # Check customer/transaction codes first
        if re.search(r'cust-\d+', query_lower):
            if any(k in query_lower for k in ["fraud", "transaction", "payment", "spend", "charge"]):
                return "fraud"
            return "churn"
            
        if re.search(r'tx-\d+', query_lower):
            return "fraud"
            
        # Match keywords
        if any(k in query_lower for k in ["churn", "subscriber", "retention", "contract", "customer success"]):
            return "churn"
            
        if any(k in query_lower for k in ["fraud", "suspicious", "compliance", "anomaly", "decline", "flagged"]):
            return "fraud"
            
        if any(k in query_lower for k in ["forecast", "revenue", "mrr", "projection", "financial"]):
            return "revenue"
            
        if any(k in query_lower for k in ["report", "executive", "briefing", "pdf", "overview", "corporate"]):
            return "executive"
            
        return "general"

    def run(self, prompt: str, session_id: str = None) -> str:
        if not session_id:
            session_id = f"session-{uuid.uuid4().hex[:8]}"
            
        agent_type = self.route_query(prompt)
        
        thought = f"Received prompt: '{prompt}'. Routing analysis indicates destination: '{agent_type}' agent."
        
        if agent_type == "general":
            action = "N/A"
            observation = "Interactive Help Guide triggered."
            output = (
                f"### Welcome to InsightPilot Multi-Agent Business Intelligence Console\n"
                f"I am the **Orchestrator Agent**, and I coordinate four specialized analytics agents. "
                f"To begin, you can ask questions like:\n\n"
                f"1. **Customer Success:**\n"
                f"   - *'What is the churn risk for customer CUST-10045?'*\n"
                f"   - *'Analyze customer retention risk and billing methods.'*\n"
                f"2. **Risk & Security:**\n"
                f"   - *'Perform a security scan on transaction TX-100234.'*\n"
                f"   - *'Get global fraud dashboard logs.'*\n"
                f"3. **FP&A Forecasting:**\n"
                f"   - *'Forecast company revenue for the next 6 months.'*\n"
                f"   - *'Show monthly recurring revenue trend analysis.'*\n"
                f"4. **Executive Operations:**\n"
                f"   - *'Generate a corporate executive report and compile the PDF.'*\n"
                f"   - *'Compile the quarterly operations overview.'*\n"
            )
            self.log_reasoning_step(session_id, thought, action, observation, output)
            return output
            
        # Delegate to specialized agent
        agent = self.agents[agent_type]
        action = f"Delegating query to {agent.name}."
        
        print(f"[Orchestrator] Routing task to {agent.name}...")
        
        # Run sub-agent execution
        agent_response = agent.run(prompt, session_id)
        
        observation = f"Completed subtask. Received output from {agent.name}."
        
        # Formulate consolidated orchestrator report
        output = (
            f"### InsightPilot Multi-Agent Orchestration Log\n"
            f"- **Delegated Agent:** `{agent.name}`\n"
            f"- **Session Audit ID:** `{session_id}`\n\n"
            f"{agent_response}"
        )
        
        self.log_reasoning_step(session_id, thought, action, observation, output)
        return output

if __name__ == "__main__":
    import sys
    sys.path.append("c:/Users/aryan kumar kannojia/Music/Caposton_write_2")
    orchestrator = OrchestratorAgent()
    print(orchestrator.run("What is the churn risk for customer CUST-10005?"))
