"""Logging and observability for the insurance claims agent."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import config


class ClaimsLogger:
    """Comprehensive logger for agent operations and decisions."""
    
    def __init__(self, log_level: str = "INFO"):
        self.log_dir = config.LOGS_DIR
        self.log_file = self.log_dir / f"agent_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.log_entries = []
        
        # Setup standard logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("InsuranceAgent")
    
    def log_tool_call(self, tool_name: str, inputs: Dict[str, Any], output: Any):
        """Log a tool invocation."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "tool_call",
            "tool_name": tool_name,
            "inputs": inputs,
            "output": output
        }
        self._add_entry(entry)
        self.logger.info(f"Tool called: {tool_name}")
    
    def log_agent_step(self, step_name: str, data: Dict[str, Any]):
        """Log an agent processing step."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "agent_step",
            "step_name": step_name,
            "data": data
        }
        self._add_entry(entry)
        self.logger.info(f"Agent step: {step_name}")
    
    def log_human_override(
        self,
        claim_id: str,
        original_decision: Dict[str, Any],
        override_decision: Dict[str, Any],
        reason: Optional[str] = None
    ):
        """Log a human override of agent decision."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "human_override",
            "claim_id": claim_id,
            "original_decision": original_decision,
            "override_decision": override_decision,
            "reason": reason
        }
        self._add_entry(entry)
        self.logger.warning(f"Human override for claim {claim_id}")
    
    def log_evaluation_result(self, system_name: str, metrics: Dict[str, Any]):
        """Log evaluation results."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "evaluation",
            "system_name": system_name,
            "metrics": metrics
        }
        self._add_entry(entry)
        self.logger.info(f"Evaluation logged: {system_name}")
    
    def log_error(self, error_type: str, error_message: str, context: Optional[Dict] = None):
        """Log an error."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        self._add_entry(entry)
        self.logger.error(f"{error_type}: {error_message}")
    
    def _add_entry(self, entry: Dict[str, Any]):
        """Add entry to in-memory log."""
        self.log_entries.append(entry)
    
    def save_log(self):
        """Save accumulated logs to file."""
        with open(self.log_file, 'w') as f:
            json.dump(self.log_entries, f, indent=2, default=str)
        self.logger.info(f"Log saved to {self.log_file}")
    
    def get_logs(
        self,
        log_type: Optional[str] = None,
        claim_id: Optional[str] = None
    ) -> list:
        """Retrieve logs with optional filtering."""
        logs = self.log_entries
        
        if log_type:
            logs = [log for log in logs if log.get("type") == log_type]
        
        if claim_id:
            logs = [
                log for log in logs
                if log.get("claim_id") == claim_id or
                log.get("data", {}).get("claim_id") == claim_id
            ]
        
        return logs
    
    def get_tool_call_stats(self) -> Dict[str, Any]:
        """Get statistics on tool calls."""
        tool_calls = [log for log in self.log_entries if log.get("type") == "tool_call"]
        
        if not tool_calls:
            return {"total_calls": 0, "by_tool": {}}
        
        tool_counts = {}
        for call in tool_calls:
            tool_name = call.get("tool_name")
            tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
        
        return {
            "total_calls": len(tool_calls),
            "by_tool": tool_counts
        }
    
    def get_override_rate(self) -> float:
        """Calculate the human override rate."""
        total_decisions = len([log for log in self.log_entries if log.get("type") == "agent_step" and log.get("step_name") == "claim_processed"])
        overrides = len([log for log in self.log_entries if log.get("type") == "human_override"])
        
        if total_decisions == 0:
            return 0.0
        
        return overrides / total_decisions


class PerformanceTracker:
    """Track performance metrics for the agent system."""
    
    def __init__(self):
        self.metrics = {
            "total_claims": 0,
            "processing_times": [],
            "decisions": [],
            "overrides": 0
        }
    
    def record_claim_processing(
        self,
        claim_id: str,
        processing_time: float,
        decision: Dict[str, Any]
    ):
        """Record a claim processing event."""
        self.metrics["total_claims"] += 1
        self.metrics["processing_times"].append(processing_time)
        self.metrics["decisions"].append({
            "claim_id": claim_id,
            "severity": decision.get("severity"),
            "action": decision.get("action"),
            "timestamp": datetime.now().isoformat()
        })
    
    def record_override(self):
        """Record a human override."""
        self.metrics["overrides"] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        if not self.metrics["processing_times"]:
            avg_time = 0
        else:
            avg_time = sum(self.metrics["processing_times"]) / len(self.metrics["processing_times"])
        
        return {
            "total_claims_processed": self.metrics["total_claims"],
            "average_processing_time": round(avg_time, 2),
            "total_overrides": self.metrics["overrides"],
            "override_rate": self.metrics["overrides"] / max(self.metrics["total_claims"], 1)
        }

