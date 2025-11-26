# Architecture Documentation

## System Overview

The Insurance Claims Agent POC is built using a modular architecture that separates concerns and enables easy extension and testing.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Streamlit UI                         │
│  (streamlit_app.py)                                         │
│  - Claim Input Interface                                    │
│  - Decision Display & Override                              │
│  - History & Analytics Dashboard                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Orchestrator                       │
│  (agent.py)                                                 │
│  - LangChain Agent Executor                                 │
│  - Tool Selection & Invocation                              │
│  - Decision Synthesis                                       │
└────┬──────────┬──────────┬──────────────────────────────────┘
     │          │          │
     ▼          ▼          ▼
┌─────────┐ ┌──────────┐ ┌────────────┐
│ Policy  │ │   Risk   │ │  Triage    │
│ Lookup  │ │ Scoring  │ │  Logger    │
│  Tool   │ │   Tool   │ │   Tool     │
└─────────┘ └──────────┘ └────────────┘
     │          │              │
     ▼          ▼              ▼
┌─────────────────────────────────────┐
│           Data Layer                │
│  - Claims Data (CSV)                │
│  - Policies Data (CSV)              │
│  - Decision Log (JSON)              │
└─────────────────────────────────────┘

        Parallel Systems:
┌──────────────┐  ┌─────────────┐  ┌──────────────┐
│  Rule-Based  │  │  One-Shot   │  │   Agentic    │
│    System    │  │  LLM System │  │    System    │
└──────────────┘  └─────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┴─────────────────┘
                         │
                         ▼
              ┌────────────────────┐
              │  Evaluation System │
              │  (evaluation.py)   │
              └────────────────────┘
```

## Core Components

### 1. Configuration Layer (`config.py`)

**Purpose**: Centralized configuration management

**Key Responsibilities**:
- Environment variable loading
- Path management
- Model configuration
- Risk thresholds and business rules

**Configuration Parameters**:
```python
- LLM_MODEL: Model selection (gpt-4, gpt-4o-mini, etc.)
- LLM_TEMPERATURE: Control randomness (0.0-1.0)
- RISK_THRESHOLD_HIGH: Risk score threshold for high risk
- RISK_THRESHOLD_MEDIUM: Risk score threshold for medium risk
- SEVERITY_LEVELS: Classification levels
- ACTIONS: Available actions for claims
```

### 2. Data Generation (`data_generator.py`)

**Purpose**: Generate realistic synthetic insurance claims data

**Components**:
- `ClaimsDataGenerator`: Main generator class
  - `generate_claims()`: Create claims with metadata
  - `generate_policies()`: Create corresponding policies
  - `_generate_narrative()`: Create realistic claim narratives
  - `_assign_ground_truth()`: Label data for evaluation

**Data Schema**:

Claims:
```
- claim_id: Unique identifier
- policy_id: Associated policy
- claim_type: Category of claim
- claim_amount: Dollar amount
- incident_date: When incident occurred
- report_date: When claim was reported
- location: Geographic location
- claimant_age: Age of claimant
- prior_claims: Number of previous claims
- policy_tenure_years: Years as customer
- narrative: Descriptive text
- ground_truth_severity: True severity level
- ground_truth_action: True recommended action
```

Policies:
```
- policy_id: Unique identifier
- policy_type: Standard/Premium/Basic
- coverage_limit: Maximum coverage
- deductible: Deductible amount
- customer_name: Policy holder name
- policy_start_date: Policy start date
- claims_history_count: Total claims filed
- is_active: Policy status
```

### 3. Agent Tools (`tools.py`)

#### PolicyLookupTool

**Purpose**: Retrieve policy information for risk assessment

**Methods**:
- `lookup(policy_id)`: Returns policy details

**Use Case**: Agent needs coverage limits, policy type, and claims history to make informed decisions

#### RiskScoringTool

**Purpose**: Calculate fraud/risk scores

**Algorithm**:
```python
risk_score = Σ(risk_factor_weight × indicator)

Risk Factors:
- High claim amount (>$50k): 0.3
- Multiple prior claims (≥3): 0.25
- New policy (<1 year): 0.15
- Late reporting (>30 days): 0.15
- Near coverage limit (>80%): 0.2
- Age risk factors: 0.10
- High-risk location: 0.05
```

**Methods**:
- `calculate_risk_score()`: Returns risk score, level, and factors

**Output**:
```json
{
  "risk_score": 0.45,
  "risk_level": "medium",
  "risk_factors": ["multiple_prior_claims", "new_policy"],
  "explanation": "Risk level is medium. Contributing factors: ..."
}
```

#### TriageLoggerTool

**Purpose**: Audit trail and decision logging

**Methods**:
- `log_decision()`: Record triage decision
- `get_decision_history()`: Retrieve historical decisions

**Logged Information**:
- Timestamp
- Claim ID
- Severity and action
- Rationale
- Risk score
- Policy information

### 4. Agent System (`agent.py`)

#### InsuranceClaimsAgent

**Architecture**: LangChain OpenAI Functions Agent

**Components**:
1. **LLM**: OpenAI GPT-4o-mini (configurable)
2. **Tools**: Policy Lookup, Risk Scoring, Triage Logger
3. **Prompt**: System instructions with guidelines
4. **Agent Executor**: Orchestrates tool calls and reasoning

**Processing Flow**:
```
1. Receive claim input
2. Parse and structure claim data
3. Create detailed prompt with claim information
4. Agent invokes tools:
   a. Policy lookup → Get coverage details
   b. Risk scoring → Calculate risk score
   c. Reasoning → Determine severity and action
   d. Triage logger → Log decision
5. Parse agent output
6. Return structured decision
```

**Prompt Engineering**:
- Role definition: Expert insurance adjuster
- Task breakdown: Step-by-step instructions
- Guidelines: Severity and action criteria
- Output format: Structured response requirements

**Error Handling**:
- Try-catch for API failures
- Default escalation on errors
- Comprehensive error logging

### 5. Evaluation System (`evaluation.py`)

#### Three System Implementations

**1. RuleBasedSystem**
```python
Logic:
if claim_amount < 5000 and risk < 0.3 and prior_claims < 2:
    action = "approve"
elif severity == "critical" or risk >= 0.7:
    action = "escalate"
else:
    action = "investigate"
```

**2. OneShotLLMSystem**
- Single LLM call
- No tool access
- All information in prompt
- Parse structured response

**3. AgenticSystem**
- Full agent with tools
- Multi-step reasoning
- Tool use for information gathering
- Comprehensive decision making

#### EvaluationSystem

**Purpose**: Compare systems objectively

**Metrics**:
1. **Accuracy**: Correct classifications
2. **Precision**: True positives / (True positives + False positives)
3. **Recall**: True positives / (True positives + False negatives)
4. **F1 Score**: Harmonic mean of precision and recall
5. **Confusion Matrix**: Detailed error analysis
6. **Processing Time**: Performance measurement

**Evaluation Process**:
```
For each system:
  For each test claim:
    1. Process claim
    2. Compare to ground truth
    3. Record metrics
    4. Track processing time
  Calculate aggregate metrics
Compare systems:
  Overall score = 0.4*severity_acc + 0.4*action_acc + 0.1*sev_f1 + 0.1*act_f1
Identify best performer
```

### 6. Logging & Observability (`logger.py`)

#### ClaimsLogger

**Purpose**: Comprehensive logging for debugging and analysis

**Log Types**:
1. **Tool Calls**: Every tool invocation with inputs/outputs
2. **Agent Steps**: Processing stages and decisions
3. **Human Overrides**: When humans change agent decisions
4. **Evaluation Results**: System comparison metrics
5. **Errors**: Exceptions and failures

**Log Format** (JSON):
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "type": "tool_call",
  "tool_name": "risk_scoring",
  "inputs": {...},
  "output": {...}
}
```

**Analytics Methods**:
- `get_tool_call_stats()`: Tool usage statistics
- `get_override_rate()`: Human intervention frequency
- `get_logs()`: Filtered log retrieval

#### PerformanceTracker

**Purpose**: Real-time performance monitoring

**Tracked Metrics**:
- Total claims processed
- Processing times
- Decision distribution
- Override count and rate


## Extension Points

### Adding New Tools

1. **Create tool class in `tools.py`**:
```python
class NewTool:
    def method(self, params):
        # Implementation
        return result
```

2. **Add wrapper in `agent.py`**:
```python
def new_tool_wrapper(params: str) -> str:
    result = self.new_tool.method(params)
    self.logger.log_tool_call("new_tool", params, result)
    return str(result)
```

3. **Register in tools list**:
```python
Tool(
    name="new_tool",
    func=new_tool_wrapper,
    description="..."
)
```

### Adding New Evaluation Metrics

1. **Implement in `evaluation.py`**:
```python
def _calculate_new_metric(self, predictions):
    # Calculate metric
    return metric_value
```

2. **Update `_calculate_metrics()`** to include new metric

3. **Display in UI** (`streamlit_app.py`)

