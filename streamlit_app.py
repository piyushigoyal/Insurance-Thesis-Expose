"""Streamlit UI for Insurance Claims Agent POC."""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
import time
from pathlib import Path
import config
from agent import InsuranceClaimsAgent
from tools import TriageLoggerTool
from logger import ClaimsLogger, PerformanceTracker
from evaluation import RuleBasedSystem, OneShotLLMSystem


# Page configuration
st.set_page_config(
    page_title="Zurich Insurance - AI Claims Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "claims_data" not in st.session_state:
    try:
        st.session_state.claims_data = pd.read_csv(config.CLAIMS_DATA_PATH)
    except FileNotFoundError:
        st.session_state.claims_data = None

if "agent" not in st.session_state:
    st.session_state.agent = None

if "logger" not in st.session_state:
    st.session_state.logger = ClaimsLogger()

if "performance_tracker" not in st.session_state:
    st.session_state.performance_tracker = PerformanceTracker()

if "decision_history" not in st.session_state:
    st.session_state.decision_history = []

if "current_decision" not in st.session_state:
    st.session_state.current_decision = None


# CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #0033A0;
        text-align: center;
        margin-bottom: 2rem;
    }
    .zurich-logo {
        font-size: 2.5rem;
        color: #0033A0;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .decision-box {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .severity-low {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
    }
    .severity-medium {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
    }
    .severity-high {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
    }
    .severity-critical {
        background-color: #f5c6cb;
        border-left: 5px solid #721c24;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def load_agent(system_type: str):
    """Load the selected agent system."""
    if system_type == "Agentic System":
        return InsuranceClaimsAgent()
    elif system_type == "Rule-Based":
        return RuleBasedSystem()
    elif system_type == "One-Shot LLM":
        return OneShotLLMSystem()
    return None


def display_claim_info(claim: pd.Series):
    """Display claim information."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📋 Claim Details")
        st.write(f"**Claim ID:** {claim['claim_id']}")
        st.write(f"**Policy ID:** {claim['policy_id']}")
        st.write(f"**Type:** {claim['claim_type']}")
        st.write(f"**Amount:** ${claim['claim_amount']:,.2f}")
    
    with col2:
        st.markdown("### 📅 Dates & Location")
        st.write(f"**Incident Date:** {claim['incident_date']}")
        st.write(f"**Report Date:** {claim['report_date']}")
        st.write(f"**Location:** {claim['location']}")
    
    with col3:
        st.markdown("### 👤 Claimant Info")
        st.write(f"**Age:** {claim['claimant_age']}")
        st.write(f"**Prior Claims:** {claim['prior_claims']}")
        st.write(f"**Policy Tenure:** {claim['policy_tenure_years']} years")
    
    st.markdown("### 📝 Claim Narrative")
    st.info(claim['narrative'])


def display_decision(decision: dict):
    """Display agent decision with styling."""
    severity = decision.get("severity", "medium")
    action = decision.get("action", "investigate")
    
    severity_class = f"severity-{severity}"
    
    st.markdown(f"""
    <div class="decision-box {severity_class}">
        <h2 style="margin-top: 0;">🤖 Agent Decision</h2>
        <p><strong>Severity:</strong> <span style="text-transform: uppercase;">{severity}</span></p>
        <p><strong>Action:</strong> <span style="text-transform: uppercase;">{action}</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 💭 Rationale")
    st.write(decision.get("rationale", "No rationale provided"))


def process_claim(claim_dict: dict, system_type: str):
    """Process a claim with the selected system."""
    if st.session_state.agent is None:
        st.session_state.agent = load_agent(system_type)
    
    with st.spinner("🔄 Processing claim..."):
        start_time = time.time()
        
        try:
            result = st.session_state.agent.process_claim(claim_dict)
            processing_time = time.time() - start_time
            
            result["processing_time"] = processing_time
            result["timestamp"] = datetime.now().isoformat()
            result["system_type"] = system_type
            
            # Track performance
            st.session_state.performance_tracker.record_claim_processing(
                claim_dict["claim_id"],
                processing_time,
                result
            )
            
            return result
            
        except Exception as e:
            st.error(f"Error processing claim: {str(e)}")
            return None


def handle_accept_decision(decision: dict, claim: dict):
    """Handle acceptance of agent decision."""
    st.session_state.decision_history.append({
        "claim_id": claim["claim_id"],
        "decision": decision,
        "status": "accepted",
        "timestamp": datetime.now().isoformat(),
        "ground_truth_severity": claim.get("ground_truth_severity"),
        "ground_truth_action": claim.get("ground_truth_action")
    })
    
    st.session_state.logger.log_agent_step("decision_accepted", {
        "claim_id": claim["claim_id"],
        "severity": decision["severity"],
        "action": decision["action"]
    })
    
    st.success("✅ Decision accepted!")
    st.session_state.current_decision = None


def handle_override_decision(decision: dict, claim: dict, override_severity: str, override_action: str, reason: str):
    """Handle override of agent decision."""
    override_decision = {
        "severity": override_severity,
        "action": override_action,
        "rationale": reason
    }
    
    st.session_state.decision_history.append({
        "claim_id": claim["claim_id"],
        "original_decision": decision,
        "override_decision": override_decision,
        "status": "overridden",
        "timestamp": datetime.now().isoformat(),
        "ground_truth_severity": claim.get("ground_truth_severity"),
        "ground_truth_action": claim.get("ground_truth_action")
    })
    
    st.session_state.logger.log_human_override(
        claim["claim_id"],
        decision,
        override_decision,
        reason
    )
    
    st.session_state.performance_tracker.record_override()
    
    st.warning(f"⚠️ Decision overridden!")
    st.session_state.current_decision = None


def display_history():
    """Display decision history."""
    if not st.session_state.decision_history:
        st.info("No decisions yet. Process some claims to see history.")
        return
    
    st.markdown("### 📊 Decision History")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(st.session_state.decision_history)
    accepted = sum(1 for d in st.session_state.decision_history if d["status"] == "accepted")
    overridden = sum(1 for d in st.session_state.decision_history if d["status"] == "overridden")
    override_rate = (overridden / total * 100) if total > 0 else 0
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{total}</h3>
            <p>Total Decisions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{accepted}</h3>
            <p>Accepted</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{overridden}</h3>
            <p>Overridden</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{override_rate:.1f}%</h3>
            <p>Override Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Decision table
    st.markdown("---")
    
    history_df = pd.DataFrame([
        {
            "Claim ID": d["claim_id"],
            "Severity": d["decision"]["severity"] if d["status"] == "accepted" else d["override_decision"]["severity"],
            "Action": d["decision"]["action"] if d["status"] == "accepted" else d["override_decision"]["action"],
            "Status": "✅ Accepted" if d["status"] == "accepted" else "⚠️ Overridden",
            "Timestamp": d["timestamp"]
        }
        for d in reversed(st.session_state.decision_history[-20:])
    ])
    
    st.dataframe(history_df, use_container_width=True)


def main():
    """Main Streamlit app."""
    # Display Zurich logo - centered
    logo_path = Path(__file__).parent / "assets" / "zurich_logo.png"
    
    if logo_path.exists():
        # Create centered columns for logo
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.image(str(logo_path), use_container_width=True)
    else:
        st.markdown('<div class="zurich-logo">🛡️ ZURICH</div>', unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">AI-Powered Claims Processing Agent</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666; margin-bottom: 2rem;">Intelligent automation for faster, more accurate claims decisions</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # Display logo in sidebar - centered
        logo_path = Path(__file__).parent / "assets" / "zurich_logo.png"
        if logo_path.exists():
            # Center the logo in sidebar
            st.markdown('<div style="display: flex; justify-content: center; margin-bottom: 1rem;">', unsafe_allow_html=True)
            st.image(str(logo_path), width=150)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("## 🛡️ Zurich Insurance")
        st.markdown("**AI Claims Agent POC**")
        st.markdown("---")
        st.markdown("## ⚙️ Configuration")
        
        # System selection
        system_type = st.selectbox(
            "Select System",
            ["Agentic System", "Rule-Based", "One-Shot LLM"],
            help="Choose which system to use for processing claims"
        )
        
        if st.button("🔄 Reload Agent"):
            st.session_state.agent = load_agent(system_type)
            st.success(f"Loaded {system_type}")
        
        st.markdown("---")
        
        # Data status
        st.markdown("## 📊 Data Status")
        if st.session_state.claims_data is not None:
            st.success(f"✅ {len(st.session_state.claims_data)} claims loaded")
        else:
            st.error("❌ No claims data found")
            if st.button("Generate Data"):
                with st.spinner("Generating claims data..."):
                    import data_generator
                    generator = data_generator.ClaimsDataGenerator(num_claims=200)
                    claims_df = generator.generate_claims()
                    policies_df = generator.generate_policies(claims_df)
                    generator.save_data(claims_df, policies_df)
                    st.session_state.claims_data = claims_df
                    st.success("Data generated!")
                    st.rerun()
        
        st.markdown("---")
        
        # Performance metrics
        st.markdown("## 📈 Performance")
        perf = st.session_state.performance_tracker.get_summary()
        st.metric("Claims Processed", perf["total_claims_processed"])
        st.metric("Avg Time", f"{perf['average_processing_time']:.2f}s")
        st.metric("Override Rate", f"{perf['override_rate']:.1%}")
    
    # Main content
    tabs = st.tabs(["🔍 Process Claims", "📜 History", "📊 Evaluation"])
    
    with tabs[0]:
        if st.session_state.claims_data is None:
            st.warning("Please generate claims data first using the sidebar button.")
            return
        
        st.markdown("## Select a Claim to Process")
        
        # Claim selection
        claim_options = st.session_state.claims_data["claim_id"].tolist()
        selected_claim_id = st.selectbox("Choose Claim ID", claim_options)
        
        claim = st.session_state.claims_data[
            st.session_state.claims_data["claim_id"] == selected_claim_id
        ].iloc[0]
        
        # Display claim
        display_claim_info(claim)
        
        # Process button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Process Claim", use_container_width=True, type="primary"):
                claim_dict = claim.to_dict()
                result = process_claim(claim_dict, system_type)
                
                if result:
                    st.session_state.current_decision = {
                        "decision": result,
                        "claim": claim_dict
                    }
        
        # Display decision if available
        if st.session_state.current_decision:
            st.markdown("---")
            decision = st.session_state.current_decision["decision"]
            claim_dict = st.session_state.current_decision["claim"]
            
            display_decision(decision)
            
            # Show ground truth (for evaluation)
            with st.expander("📊 Ground Truth (For Evaluation)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**True Severity:** {claim_dict.get('ground_truth_severity', 'N/A')}")
                with col2:
                    st.write(f"**True Action:** {claim_dict.get('ground_truth_action', 'N/A')}")
            
            # Action buttons
            st.markdown("### 🎯 Your Decision")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Accept Decision", use_container_width=True, type="primary"):
                    handle_accept_decision(decision, claim_dict)
                    st.rerun()
            
            with col2:
                if st.button("⚠️ Override Decision", use_container_width=True):
                    st.session_state.show_override_form = True
            
            # Override form
            if st.session_state.get("show_override_form", False):
                st.markdown("---")
                st.markdown("### ✏️ Override Form")
                
                col1, col2 = st.columns(2)
                with col1:
                    override_severity = st.selectbox(
                        "Override Severity",
                        config.SEVERITY_LEVELS,
                        index=config.SEVERITY_LEVELS.index(decision["severity"])
                    )
                with col2:
                    override_action = st.selectbox(
                        "Override Action",
                        config.ACTIONS,
                        index=config.ACTIONS.index(decision["action"])
                    )
                
                override_reason = st.text_area("Reason for Override")
                
                if st.button("Submit Override", type="primary"):
                    if override_reason.strip():
                        handle_override_decision(
                            decision,
                            claim_dict,
                            override_severity,
                            override_action,
                            override_reason
                        )
                        st.session_state.show_override_form = False
                        st.rerun()
                    else:
                        st.error("Please provide a reason for the override")
    
    with tabs[1]:
        display_history()
        
        # Export history
        if st.session_state.decision_history:
            if st.button("💾 Export History"):
                history_file = config.DATA_DIR / "decision_history.json"
                with open(history_file, 'w') as f:
                    json.dump(st.session_state.decision_history, f, indent=2)
                st.success(f"History exported to {history_file}")
    
    with tabs[2]:
        st.markdown("## 📊 System Evaluation")
        st.info("Run evaluation to compare Rule-Based, One-Shot LLM, and Agentic systems")
        
        num_test_claims = st.slider("Number of test claims", 10, 100, 30)
        
        if st.button("🚀 Run Evaluation", type="primary"):
            with st.spinner("Running evaluation... This may take a few minutes."):
                from evaluation import run_evaluation
                results = run_evaluation(num_test_claims)
                
                # Display results
                st.success("Evaluation complete!")
                
                comparison = results["comparison"]
                
                # Metrics comparison
                st.markdown("### 📈 Performance Comparison")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Severity Accuracy")
                    severity_df = pd.DataFrame([
                        {"System": k, "Accuracy": v}
                        for k, v in comparison["severity_accuracy"].items()
                    ])
                    st.bar_chart(severity_df.set_index("System"))
                
                with col2:
                    st.markdown("#### Action Accuracy")
                    action_df = pd.DataFrame([
                        {"System": k, "Accuracy": v}
                        for k, v in comparison["action_accuracy"].items()
                    ])
                    st.bar_chart(action_df.set_index("System"))
                
                # Best system
                st.markdown("### 🏆 Best System")
                best = comparison["best_system"]
                st.success(f"**{best}** achieved the highest overall score!")
                
                # Detailed metrics
                st.markdown("### 📋 Detailed Metrics")
                metrics_df = pd.DataFrame([
                    {
                        "System": system_name,
                        "Severity Acc": f"{results['individual_results'][system_name]['severity_accuracy']:.2%}",
                        "Action Acc": f"{results['individual_results'][system_name]['action_accuracy']:.2%}",
                        "Severity F1": f"{results['individual_results'][system_name]['severity_f1']:.2%}",
                        "Action F1": f"{results['individual_results'][system_name]['action_f1']:.2%}",
                        "Avg Time": f"{results['individual_results'][system_name]['avg_processing_time']:.2f}s"
                    }
                    for system_name in results['individual_results'].keys()
                ])
                st.dataframe(metrics_df, use_container_width=True)


if __name__ == "__main__":
    main()

