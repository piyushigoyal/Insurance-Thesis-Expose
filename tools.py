"""Agent tools for insurance claims processing."""

import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any, Optional
import config


class PolicyLookupTool:
    """Tool for looking up policy information."""
    
    def __init__(self):
        self.policies_df = self._load_policies()
    
    def _load_policies(self) -> pd.DataFrame:
        """Load policies data."""
        try:
            return pd.read_csv(config.POLICIES_DATA_PATH)
        except FileNotFoundError:
            return pd.DataFrame()
    
    def lookup(self, policy_id: str) -> Dict[str, Any]:
        """
        Look up policy information by policy ID.
        
        Args:
            policy_id: The policy ID to look up
            
        Returns:
            Dictionary containing policy information
        """
        if self.policies_df.empty:
            return {"error": "Policy database not available"}
        
        policy = self.policies_df[self.policies_df["policy_id"] == policy_id]
        
        if policy.empty:
            return {"error": f"Policy {policy_id} not found"}
        
        policy_dict = policy.iloc[0].to_dict()
        
        return {
            "policy_id": policy_dict["policy_id"],
            "policy_type": policy_dict["policy_type"],
            "coverage_limit": policy_dict["coverage_limit"],
            "deductible": policy_dict["deductible"],
            "customer_name": policy_dict["customer_name"],
            "policy_start_date": policy_dict["policy_start_date"],
            "claims_history_count": policy_dict["claims_history_count"],
            "is_active": policy_dict["is_active"]
        }


class RiskScoringTool:
    """Tool for calculating fraud/risk scores."""
    
    def __init__(self):
        self.risk_factors = {
            "high_amount": 0.3,
            "multiple_claims": 0.25,
            "new_policy": 0.15,
            "late_reporting": 0.15,
            "high_age_risk": 0.10,
            "location_risk": 0.05
        }
    
    def calculate_risk_score(
        self,
        claim_amount: float,
        prior_claims: int,
        policy_tenure_years: int,
        incident_to_report_days: int,
        coverage_limit: Optional[float] = None,
        claimant_age: Optional[int] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate risk score based on claim characteristics.
        
        Args:
            claim_amount: The claim amount
            prior_claims: Number of prior claims
            policy_tenure_years: Years the policy has been active
            incident_to_report_days: Days between incident and reporting
            coverage_limit: Policy coverage limit
            claimant_age: Age of claimant
            location: Claim location
            
        Returns:
            Dictionary with risk score and contributing factors
        """
        risk_score = 0.0
        risk_factors = []
        
        # Check high amount (compared to typical claims)
        if claim_amount > 50000:
            risk_score += self.risk_factors["high_amount"]
            risk_factors.append("high_claim_amount")
        
        # Check multiple prior claims
        if prior_claims >= 3:
            risk_score += self.risk_factors["multiple_claims"]
            risk_factors.append("multiple_prior_claims")
        
        # Check new policy (less than 1 year)
        if policy_tenure_years < 1:
            risk_score += self.risk_factors["new_policy"]
            risk_factors.append("new_policy")
        
        # Check late reporting (more than 30 days)
        if incident_to_report_days > 30:
            risk_score += self.risk_factors["late_reporting"]
            risk_factors.append("late_reporting")
        
        # Check if claim amount is close to coverage limit
        if coverage_limit and claim_amount > coverage_limit * 0.8:
            risk_score += 0.2
            risk_factors.append("claim_near_coverage_limit")
        
        # Age-based risk (very young or very old claimants)
        if claimant_age:
            if claimant_age < 25 or claimant_age > 75:
                risk_score += self.risk_factors["high_age_risk"]
                risk_factors.append("age_risk_factor")
        
        # High-risk locations (simplified)
        high_risk_locations = ["New York, NY", "Los Angeles, CA", "Chicago, IL"]
        if location and location in high_risk_locations:
            risk_score += self.risk_factors["location_risk"]
            risk_factors.append("high_risk_location")
        
        # Normalize to 0-1 scale
        risk_score = min(risk_score, 1.0)
        
        # Determine risk level
        if risk_score >= config.RISK_THRESHOLD_HIGH:
            risk_level = "high"
        elif risk_score >= config.RISK_THRESHOLD_MEDIUM:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "explanation": self._generate_explanation(risk_level, risk_factors)
        }
    
    def _generate_explanation(self, risk_level: str, factors: list) -> str:
        """Generate human-readable explanation of risk assessment."""
        if not factors:
            return f"Risk level is {risk_level}. No significant risk factors identified."
        
        factors_str = ", ".join(factors)
        return f"Risk level is {risk_level}. Contributing factors: {factors_str}."


class TriageLoggerTool:
    """Tool for logging triage decisions and actions."""
    
    def __init__(self):
        self.log_file = config.DECISIONS_LOG_PATH
        self._initialize_log()
    
    def _initialize_log(self):
        """Initialize the log file if it doesn't exist."""
        if not self.log_file.exists():
            with open(self.log_file, 'w') as f:
                json.dump([], f)
    
    def log_decision(
        self,
        claim_id: str,
        severity: str,
        action: str,
        rationale: str,
        risk_score: float,
        policy_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Log a triage decision.
        
        Args:
            claim_id: The claim ID
            severity: Assessed severity level
            action: Recommended action
            rationale: Explanation for the decision
            risk_score: Calculated risk score
            policy_info: Policy information
            metadata: Additional metadata
            
        Returns:
            Confirmation of logging
        """
        decision_entry = {
            "claim_id": claim_id,
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "action": action,
            "rationale": rationale,
            "risk_score": risk_score,
            "policy_id": policy_info.get("policy_id"),
            "metadata": metadata or {}
        }
        
        # Read existing log
        try:
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            log_data = []
        
        # Append new entry
        log_data.append(decision_entry)
        
        # Write back
        with open(self.log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        return {
            "status": "logged",
            "message": f"Decision for claim {claim_id} logged successfully"
        }
    
    def get_decision_history(self, claim_id: Optional[str] = None) -> list:
        """Get decision history, optionally filtered by claim ID."""
        try:
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
            
            if claim_id:
                return [entry for entry in log_data if entry["claim_id"] == claim_id]
            return log_data
        except (FileNotFoundError, json.JSONDecodeError):
            return []

