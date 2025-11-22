"""Evaluation system comparing different approaches to claims processing."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
import json
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import config
from agent import InsuranceClaimsAgent
from tools import PolicyLookupTool, RiskScoringTool
from langchain_openai import ChatOpenAI
from logger import ClaimsLogger


class RuleBasedSystem:
    """Baseline rule-based claims processing system."""
    
    def __init__(self):
        self.policy_tool = PolicyLookupTool()
        self.risk_tool = RiskScoringTool()
    
    def process_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Process claim using hard-coded rules."""
        # Get policy info
        policy_info = self.policy_tool.lookup(claim["policy_id"])
        
        # Calculate risk score
        try:
            incident_date = datetime.strptime(claim["incident_date"], "%Y-%m-%d")
            report_date = datetime.strptime(claim["report_date"], "%Y-%m-%d")
            incident_to_report_days = (report_date - incident_date).days
        except:
            incident_to_report_days = 0
        
        risk_result = self.risk_tool.calculate_risk_score(
            claim_amount=claim["claim_amount"],
            prior_claims=claim["prior_claims"],
            policy_tenure_years=claim["policy_tenure_years"],
            incident_to_report_days=incident_to_report_days,
            coverage_limit=policy_info.get("coverage_limit"),
            claimant_age=claim["claimant_age"],
            location=claim["location"]
        )
        
        risk_score = risk_result["risk_score"]
        
        # Rule-based decision logic
        claim_amount = claim["claim_amount"]
        prior_claims = claim["prior_claims"]
        
        # Determine severity
        if claim_amount < 5000:
            severity = "low"
        elif claim_amount < 25000:
            severity = "medium"
        elif claim_amount < 75000:
            severity = "high"
        else:
            severity = "critical"
        
        # Determine action
        if severity == "low" and risk_score < 0.3 and prior_claims < 2:
            action = "approve"
        elif severity == "critical" or risk_score >= 0.7:
            action = "escalate"
        elif risk_score >= 0.4 or prior_claims >= 3:
            action = "investigate"
        elif severity == "medium" and risk_score < 0.4:
            action = "approve"
        else:
            action = "investigate"
        
        rationale = f"Rule-based decision: Severity={severity} based on amount ${claim_amount:,.2f}. Risk score={risk_score:.3f}. Prior claims={prior_claims}."
        
        return {
            "claim_id": claim["claim_id"],
            "severity": severity,
            "action": action,
            "rationale": rationale,
            "risk_score": risk_score
        }


class OneShotLLMSystem:
    """One-shot LLM system without tools."""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.LLM_MODEL
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=config.LLM_TEMPERATURE,
            openai_api_key=config.OPENAI_API_KEY
        )
    
    def process_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Process claim with single LLM call, no tools."""
        
        prompt = f"""You are an insurance claims adjuster. Analyze the following claim and provide:
1. Severity level (low/medium/high/critical)
2. Recommended action (approve/investigate/deny/escalate)
3. Brief rationale

Claim Details:
- Claim ID: {claim['claim_id']}
- Type: {claim['claim_type']}
- Amount: ${claim['claim_amount']:,.2f}
- Prior Claims: {claim['prior_claims']}
- Policy Tenure: {claim['policy_tenure_years']} years
- Claimant Age: {claim['claimant_age']}
- Location: {claim['location']}

Narrative: {claim['narrative']}

Guidelines:
- LOW severity: < $5,000
- MEDIUM severity: $5,000-$25,000
- HIGH severity: $25,000-$75,000
- CRITICAL severity: > $75,000

Respond in this format:
SEVERITY: [level]
ACTION: [action]
RATIONALE: [explanation]"""

        try:
            response = self.llm.invoke(prompt)
            output = response.content
            
            # Parse response
            severity, action = self._parse_response(output)
            
            return {
                "claim_id": claim["claim_id"],
                "severity": severity,
                "action": action,
                "rationale": output
            }
        except Exception as e:
            return {
                "claim_id": claim["claim_id"],
                "severity": "medium",
                "action": "investigate",
                "rationale": f"Error: {str(e)}"
            }
    
    def _parse_response(self, output: str) -> tuple:
        """Parse severity and action from LLM output."""
        output_lower = output.lower()
        
        # Extract severity
        severity = "medium"
        for sev in config.SEVERITY_LEVELS:
            if sev in output_lower:
                severity = sev
                break
        
        # Extract action
        action = "investigate"
        for act in config.ACTIONS:
            if act in output_lower:
                action = act
                break
        
        return severity, action


class EvaluationSystem:
    """System to evaluate and compare different approaches."""
    
    def __init__(self):
        self.logger = ClaimsLogger()
        self.systems = {
            "rule_based": RuleBasedSystem(),
            "one_shot_llm": OneShotLLMSystem(),
            "agentic": InsuranceClaimsAgent()
        }
    
    def evaluate_all_systems(self, test_claims: pd.DataFrame) -> Dict[str, Any]:
        """Evaluate all systems on test claims."""
        results = {}
        
        print("\n" + "="*80)
        print("EVALUATING INSURANCE CLAIMS SYSTEMS")
        print("="*80)
        
        for system_name, system in self.systems.items():
            print(f"\n[{system_name.upper()}]")
            print("-" * 80)
            
            system_results = self.evaluate_system(system, test_claims, system_name)
            results[system_name] = system_results
            
            # Print summary
            print(f"\nResults for {system_name}:")
            print(f"  Severity Accuracy: {system_results['severity_accuracy']:.2%}")
            print(f"  Action Accuracy: {system_results['action_accuracy']:.2%}")
            print(f"  Processing Time: {system_results['avg_processing_time']:.2f}s")
            
            # Log results
            self.logger.log_evaluation_result(system_name, system_results)
        
        # Compare systems
        comparison = self.compare_systems(results)
        
        print("\n" + "="*80)
        print("COMPARISON SUMMARY")
        print("="*80)
        self._print_comparison(comparison)
        
        # Save results
        self._save_results(results, comparison)
        
        return {
            "individual_results": results,
            "comparison": comparison
        }
    
    def evaluate_system(
        self,
        system: Any,
        test_claims: pd.DataFrame,
        system_name: str
    ) -> Dict[str, Any]:
        """Evaluate a single system."""
        predictions = []
        processing_times = []
        
        for idx, claim in test_claims.iterrows():
            claim_dict = claim.to_dict()
            
            start_time = datetime.now()
            try:
                result = system.process_claim(claim_dict)
                processing_time = (datetime.now() - start_time).total_seconds()
                
                predictions.append({
                    "claim_id": claim_dict["claim_id"],
                    "predicted_severity": result["severity"],
                    "predicted_action": result["action"],
                    "true_severity": claim_dict["ground_truth_severity"],
                    "true_action": claim_dict["ground_truth_action"],
                    "processing_time": processing_time
                })
                processing_times.append(processing_time)
                
            except Exception as e:
                print(f"  Error processing {claim_dict['claim_id']}: {str(e)}")
                predictions.append({
                    "claim_id": claim_dict["claim_id"],
                    "predicted_severity": "unknown",
                    "predicted_action": "escalate",
                    "true_severity": claim_dict["ground_truth_severity"],
                    "true_action": claim_dict["ground_truth_action"],
                    "processing_time": 0
                })
            
            # Progress indicator
            if (idx + 1) % 10 == 0:
                print(f"  Processed {idx + 1}/{len(test_claims)} claims...")
        
        # Calculate metrics
        metrics = self._calculate_metrics(predictions)
        metrics["avg_processing_time"] = np.mean(processing_times) if processing_times else 0
        metrics["predictions"] = predictions
        
        return metrics
    
    def _calculate_metrics(self, predictions: List[Dict]) -> Dict[str, Any]:
        """Calculate evaluation metrics."""
        # Extract predictions and ground truth
        pred_severities = [p["predicted_severity"] for p in predictions]
        true_severities = [p["true_severity"] for p in predictions]
        pred_actions = [p["predicted_action"] for p in predictions]
        true_actions = [p["true_action"] for p in predictions]
        
        # Severity metrics
        severity_accuracy = accuracy_score(true_severities, pred_severities)
        severity_precision, severity_recall, severity_f1, _ = precision_recall_fscore_support(
            true_severities, pred_severities, average="weighted", zero_division=0
        )
        
        # Action metrics
        action_accuracy = accuracy_score(true_actions, pred_actions)
        action_precision, action_recall, action_f1, _ = precision_recall_fscore_support(
            true_actions, pred_actions, average="weighted", zero_division=0
        )
        
        # Confusion matrices
        severity_cm = confusion_matrix(true_severities, pred_severities, labels=config.SEVERITY_LEVELS)
        action_cm = confusion_matrix(true_actions, pred_actions, labels=config.ACTIONS)
        
        return {
            "severity_accuracy": severity_accuracy,
            "severity_precision": severity_precision,
            "severity_recall": severity_recall,
            "severity_f1": severity_f1,
            "action_accuracy": action_accuracy,
            "action_precision": action_precision,
            "action_recall": action_recall,
            "action_f1": action_f1,
            "severity_confusion_matrix": severity_cm.tolist(),
            "action_confusion_matrix": action_cm.tolist()
        }
    
    def compare_systems(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """Compare systems and identify best performer."""
        comparison = {
            "severity_accuracy": {},
            "action_accuracy": {},
            "processing_time": {},
            "overall_score": {}
        }
        
        for system_name, system_results in results.items():
            comparison["severity_accuracy"][system_name] = system_results["severity_accuracy"]
            comparison["action_accuracy"][system_name] = system_results["action_accuracy"]
            comparison["processing_time"][system_name] = system_results["avg_processing_time"]
            
            # Calculate overall score (weighted combination)
            overall = (
                0.4 * system_results["severity_accuracy"] +
                0.4 * system_results["action_accuracy"] +
                0.1 * system_results["severity_f1"] +
                0.1 * system_results["action_f1"]
            )
            comparison["overall_score"][system_name] = overall
        
        # Identify best system
        best_system = max(comparison["overall_score"], key=comparison["overall_score"].get)
        comparison["best_system"] = best_system
        
        return comparison
    
    def _print_comparison(self, comparison: Dict[str, Any]):
        """Print comparison results."""
        print("\nSeverity Accuracy:")
        for system, acc in comparison["severity_accuracy"].items():
            print(f"  {system:20s}: {acc:.2%}")
        
        print("\nAction Accuracy:")
        for system, acc in comparison["action_accuracy"].items():
            print(f"  {system:20s}: {acc:.2%}")
        
        print("\nProcessing Time:")
        for system, time in comparison["processing_time"].items():
            print(f"  {system:20s}: {time:.2f}s")
        
        print("\nOverall Score:")
        for system, score in comparison["overall_score"].items():
            marker = " ⭐ BEST" if system == comparison["best_system"] else ""
            print(f"  {system:20s}: {score:.2%}{marker}")
    
    def _save_results(self, results: Dict, comparison: Dict):
        """Save evaluation results to file."""
        output = {
            "timestamp": datetime.now().isoformat(),
            "individual_results": {
                system: {k: v for k, v in res.items() if k != "predictions"}
                for system, res in results.items()
            },
            "comparison": comparison
        }
        
        output_file = config.DATA_DIR / "evaluation_results.json"
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\n✓ Results saved to {output_file}")
        
        # Save logger
        self.logger.save_log()


def run_evaluation(num_test_claims: int = 50):
    """Run full evaluation on test claims."""
    # Load claims data
    claims_df = pd.read_csv(config.CLAIMS_DATA_PATH)
    
    # Select test claims
    test_claims = claims_df.head(num_test_claims)
    
    print(f"\nRunning evaluation on {len(test_claims)} test claims...")
    
    # Run evaluation
    evaluator = EvaluationSystem()
    results = evaluator.evaluate_all_systems(test_claims)
    
    return results


if __name__ == "__main__":
    run_evaluation(num_test_claims=30)

