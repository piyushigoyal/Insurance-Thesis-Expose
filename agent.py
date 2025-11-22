"""Insurance claims processing agent using LangChain."""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import Tool
import config
from tools import PolicyLookupTool, RiskScoringTool, TriageLoggerTool
from logger import ClaimsLogger


class InsuranceClaimsAgent:
    """Orchestrator agent for processing insurance claims."""
    
    def __init__(self, model_name: str = None, temperature: float = None):
        self.model_name = model_name or config.LLM_MODEL
        self.temperature = temperature or config.LLM_TEMPERATURE
        
        # Initialize tools
        self.policy_tool = PolicyLookupTool()
        self.risk_tool = RiskScoringTool()
        self.triage_tool = TriageLoggerTool()
        self.logger = ClaimsLogger()
        
        # Initialize LLM and agent (LangChain v1 API)
        # init_chat_model reads OPENAI_API_KEY from env or accepts api_key kwarg
        self.llm = init_chat_model(
            f"openai:{self.model_name}",
            temperature=self.temperature,
            api_key=config.OPENAI_API_KEY,
        )

        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools from our tool classes."""
        
        def policy_lookup_wrapper(policy_id: str) -> str:
            """Look up policy information."""
            result = self.policy_tool.lookup(policy_id)
            self.logger.log_tool_call("policy_lookup", {"policy_id": policy_id}, result)
            return str(result)
        
        def risk_scoring_wrapper(params: str) -> str:
            """
            Calculate risk score. Expects JSON string with parameters:
            {"claim_amount": float, "prior_claims": int, "policy_tenure_years": int, 
             "incident_to_report_days": int, "coverage_limit": float, "claimant_age": int, "location": str}
            """
            import json
            try:
                params_dict = json.loads(params)
                result = self.risk_tool.calculate_risk_score(**params_dict)
                self.logger.log_tool_call("risk_scoring", params_dict, result)
                return str(result)
            except Exception as e:
                return f"Error calculating risk score: {str(e)}"
        
        def triage_logger_wrapper(params: str) -> str:
            """
            Log triage decision. Expects JSON string with parameters:
            {"claim_id": str, "severity": str, "action": str, "rationale": str, 
             "risk_score": float, "policy_info": dict}
            """
            import json
            try:
                params_dict = json.loads(params)
                result = self.triage_tool.log_decision(**params_dict)
                self.logger.log_tool_call("triage_logger", params_dict, result)
                return str(result)
            except Exception as e:
                return f"Error logging decision: {str(e)}"
        
        return [
            Tool(
                name="policy_lookup",
                func=policy_lookup_wrapper,
                description="Look up policy information by policy ID. Input should be a policy ID string like 'POL-1234'."
            ),
            Tool(
                name="risk_scoring",
                func=risk_scoring_wrapper,
                description="""Calculate fraud/risk score for a claim. Input should be a JSON string with keys:
                claim_amount (float), prior_claims (int), policy_tenure_years (int), 
                incident_to_report_days (int), coverage_limit (float, optional), 
                claimant_age (int, optional), location (str, optional).
                Returns risk score (0-1), risk level, and contributing factors."""
            ),
            Tool(
                name="triage_logger",
                func=triage_logger_wrapper,
                description="""Log the triage decision for a claim. Input should be a JSON string with keys:
                claim_id (str), severity (str: low/medium/high/critical), action (str: approve/investigate/deny/escalate),
                rationale (str), risk_score (float), policy_info (dict).
                Use this tool to record the final decision."""
            )
        ]
    
    def _create_agent(self):
        """Create the LangChain v1 agent with tools."""

        system_message = """You are an expert insurance claims adjuster AI agent working for Zurich Insurance. Your role is to assess insurance claims and make informed decisions about their processing in accordance with Zurich's standards of excellence and customer care.

For each claim, you should:
1. Look up the policy information using the policy_lookup tool
2. Calculate the risk score using the risk_scoring tool
3. Analyze the claim narrative, amount, and all available information
4. Determine the appropriate severity level (low, medium, high, critical)
5. Decide on the recommended action (approve, investigate, deny, escalate)
6. Provide clear rationale for your decision
7. Log your decision using the triage_logger tool

Severity Guidelines:
- LOW: Minor claims < $5,000 with low risk
- MEDIUM: Claims $5,000-$25,000 with moderate risk
- HIGH: Claims $25,000-$75,000 or concerning risk factors
- CRITICAL: Claims > $75,000 or multiple high-risk factors

Action Guidelines:
- APPROVE: Low-risk claims within policy limits from good-standing customers
- INVESTIGATE: Medium-high risk claims or unusual circumstances
- DENY: Claims outside policy coverage or clear fraud indicators
- ESCALATE: Critical claims or complex cases requiring human expertise

Always provide a detailed rationale explaining your reasoning based on the claim details, policy information, and risk assessment. Maintain Zurich's commitment to fair, efficient, and customer-focused claims processing."""

        # LangChain v1: create_agent returns a Runnable agent loop
        return create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_message,
        )
    
    def process_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single insurance claim.
        
        Args:
            claim: Dictionary containing claim information
            
        Returns:
            Dictionary with decision, severity, action, and rationale
        """
        # Log the claim processing start
        self.logger.log_agent_step("claim_received", claim)
        
        # Calculate days between incident and report
        try:
            incident_date = datetime.strptime(claim["incident_date"], "%Y-%m-%d")
            report_date = datetime.strptime(claim["report_date"], "%Y-%m-%d")
            incident_to_report_days = (report_date - incident_date).days
        except:
            incident_to_report_days = 0
        
        # Prepare input for agent
        input_text = f"""
Process the following insurance claim:

Claim ID: {claim['claim_id']}
Policy ID: {claim['policy_id']}
Claim Type: {claim['claim_type']}
Claim Amount: ${claim['claim_amount']:,.2f}
Incident Date: {claim['incident_date']}
Report Date: {claim['report_date']}
Days to Report: {incident_to_report_days}
Location: {claim['location']}
Claimant Age: {claim['claimant_age']}
Prior Claims: {claim['prior_claims']}
Policy Tenure: {claim['policy_tenure_years']} years

Claim Narrative:
{claim['narrative']}

Please assess this claim and provide:
1. Severity level (low/medium/high/critical)
2. Recommended action (approve/investigate/deny/escalate)
3. Detailed rationale for your decision

Use the available tools to gather information and make an informed decision.
"""
        
        try:
            # Run the agent (LangChain v1 expects messages)
            result = self.agent.invoke({
                "messages": [
                    {"role": "user", "content": input_text}
                ]
            })
            
            # LangChain v1 create_agent returns a dict with a messages list.
            # Messages are BaseMessage objects (AIMessage, HumanMessage, etc.)
            messages = result.get("messages", []) if isinstance(result, dict) else []
            
            if messages:
                # Get the last message (should be AIMessage from the agent)
                last_msg = messages[-1]
                # Access content attribute directly (not using .get() since it's an object)
                output = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
            else:
                output = result.get("output", str(result)) if isinstance(result, dict) else str(result)

            # Extract severity and action from output
            severity, action = self._parse_decision(output)
            
            # Log completion
            self.logger.log_agent_step("claim_processed", {
                "claim_id": claim["claim_id"],
                "severity": severity,
                "action": action,
                "steps": len(messages)
            })
            
            return {
                "claim_id": claim["claim_id"],
                "severity": severity,
                "action": action,
                "rationale": output,
                # In v1, tool calls are embedded in the returned messages.
                "intermediate_steps": messages,
                "success": True
            }
            
        except Exception as e:
            self.logger.log_agent_step("claim_error", {
                "claim_id": claim["claim_id"],
                "error": str(e)
            })
            
            return {
                "claim_id": claim["claim_id"],
                "severity": "unknown",
                "action": "escalate",
                "rationale": f"Error processing claim: {str(e)}",
                "success": False
            }
    
    def _parse_decision(self, output: str) -> tuple:
        """Parse severity and action from agent output."""
        output_lower = output.lower()
        
        # Extract severity
        severity = "medium"  # default
        for sev in config.SEVERITY_LEVELS:
            if sev in output_lower:
                severity = sev
                break
        
        # Extract action
        action = "investigate"  # default
        for act in config.ACTIONS:
            if act in output_lower:
                action = act
                break
        
        return severity, action


def test_agent():
    """Test the agent with a sample claim."""
    # Load a sample claim
    claims_df = pd.read_csv(config.CLAIMS_DATA_PATH)
    sample_claim = claims_df.iloc[0].to_dict()
    
    print("Testing Insurance Claims Agent")
    print("=" * 60)
    print(f"\nProcessing Claim: {sample_claim['claim_id']}")
    print(f"Type: {sample_claim['claim_type']}")
    print(f"Amount: ${sample_claim['claim_amount']:,.2f}")
    print(f"\nNarrative: {sample_claim['narrative']}")
    print("\n" + "=" * 60)
    
    # Create and run agent
    agent = InsuranceClaimsAgent()
    result = agent.process_claim(sample_claim)
    
    print("\n" + "=" * 60)
    print("AGENT DECISION")
    print("=" * 60)
    print(f"Severity: {result['severity'].upper()}")
    print(f"Action: {result['action'].upper()}")
    print(f"\nRationale:")
    print(result['rationale'])
    print("=" * 60)


if __name__ == "__main__":
    test_agent()
