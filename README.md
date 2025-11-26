# Insurance Claims Agent POC

A comprehensive proof-of-concept for an AI-powered insurance claims processing agent that demonstrates the value of agentic systems over traditional rule-based and one-shot LLM approaches.

## 🎯 Overview

This POC implements and evaluates three different approaches to insurance claims processing:

1. **Rule-Based System**: Traditional hard-coded business rules
2. **One-Shot LLM**: Single LLM call without tools
3. **Agentic System**: LLM-powered agent with specialized tools

The system processes insurance claims, assesses risk, determines severity, and recommends actions while providing full observability and human-in-the-loop capabilities.

## ✨ Features

- 🤖 **Intelligent Agent**: LangChain-based orchestrator with multiple specialized tools
- 📊 **Comprehensive Evaluation**: Compare three different system architectures
- 🖥️ **Interactive UI**: Streamlit interface for claim processing and decision review
- 📝 **Full Logging**: Complete observability of agent steps and tool calls
- 👥 **Human-in-the-Loop**: Accept/Override agent decisions with tracking
- 📈 **Performance Metrics**: Accuracy, precision, recall, and processing time analysis

## 🏗️ Architecture

### Agent Tools

1. **Policy Lookup Tool**: Retrieves policy information from mock database
2. **Risk Scoring Tool**: Calculates fraud/risk scores based on claim characteristics
3. **Triage Logger Tool**: Records decisions and maintains audit trail

### Workflow

```
Claim Input → Policy Lookup → Risk Assessment → Severity Determination → 
Action Recommendation → Human Review → Accept/Override → Logging
```

## 📁 Project Structure

```
Insurance POC/
├── config.py                 # Configuration and settings
├── data_generator.py         # Synthetic claims data generation
├── tools.py                  # Agent tools (policy, risk, triage)
├── agent.py                  # Main agentic system
├── evaluation.py             # System comparison and evaluation
├── logger.py                 # Logging and observability
├── streamlit_app.py         # Interactive UI
├── requirements.txt          # Python dependencies
├── .env                     # Environment variables template
├── README.md                # This file
├── data/                    # Generated data and logs
│   ├── claims_data.csv
│   ├── policies_data.csv
│   ├── decisions_log.json
│   └── evaluation_results.json
└── logs/                    # Agent execution logs
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- OpenAI API key (for GPT-4o-mini)

### Installation

1. **Clone or navigate to the project directory**

```bash
cd "Insurance POC"
```

2. **Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create `.env` and add your API key:

```
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.1
```

### Generate Data

Generate synthetic insurance claims data:

```bash
python data_generator.py
```

This creates:
- `data/claims_data.csv`: 200 synthetic insurance claims with narratives
- `data/policies_data.csv`: Corresponding policy information

## 💻 Usage

### Option 1: Interactive UI (Recommended)

Launch the Streamlit application:

```bash
streamlit run streamlit_app.py
```

The UI provides:
- **Process Claims**: Select and process individual claims
- **History**: View decision history and override rate
- **Evaluation**: Compare all three systems on test data

### Option 2: Command Line

#### Test the Agent

```bash
python agent.py
```

#### Run Evaluation

```bash
python evaluation.py
```

This will:
- Process claims with all three systems
- Calculate accuracy and performance metrics
- Save results to `data/evaluation_results.json`

## 📊 Evaluation Metrics

The system evaluates performance using:

- **Severity Accuracy**: Correct classification of claim severity (low/medium/high/critical)
- **Action Accuracy**: Correct recommendation of action (approve/investigate/deny/escalate)
- **Precision, Recall, F1**: Per-class performance metrics
- **Processing Time**: Average time to process a claim
- **Override Rate**: Percentage of human overrides

## 🎓 Research Insights

### Key Findings

Based on the evaluation framework, you can demonstrate:

1. **Agentic vs Rule-Based**: How agents handle edge cases better
2. **Agentic vs One-Shot LLM**: Value of tool use and structured reasoning
3. **Human Trust**: Override rate as a proxy for decision quality
4. **Observability**: Importance of logging for agent systems

### Failure Cases

The system tracks and analyzes:
- High-value claims near coverage limits
- Complex cases with multiple risk factors
- New policies with limited history
- Claims with unusual characteristics

## 🔧 Configuration

Key settings in `config.py`:

```python
# Model Configuration
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.1

# Risk Thresholds
RISK_THRESHOLD_HIGH = 0.7
RISK_THRESHOLD_MEDIUM = 0.4

# Severity Levels
SEVERITY_LEVELS = ["low", "medium", "high", "critical"]

# Actions
ACTIONS = ["approve", "investigate", "deny", "escalate"]
```

## 📝 Logging & Observability

The system provides comprehensive logging:

### Agent Logs

Located in `logs/agent_log_*.json`, capturing:
- Tool calls with inputs/outputs
- Agent reasoning steps
- Human overrides
- Errors and exceptions

### Decision Logs

Located in `data/decisions_log.json`, recording:
- Claim ID and timestamp
- Severity and action
- Risk score
- Full rationale


## 🧪 Testing

Test individual components:

```bash
# Test data generation
python data_generator.py

# Test agent
python agent.py

# Test evaluation
python evaluation.py
```

## 📈 Extending the POC

### Add New Tools

1. Create tool class in `tools.py`
2. Add tool wrapper in `agent.py`
3. Update agent prompt with tool description

### Add New Evaluation Metrics

1. Implement metric in `evaluation.py`
2. Update `_calculate_metrics()` method
3. Display in UI or export to results

### Integrate Real Data

Replace `data_generator.py` with:
- Kaggle dataset loader
- Database connector
- API integration


## 🙏 Acknowledgments

- LangChain for agent framework
- OpenAI for GPT models
- Streamlit for UI framework
- Synthetic data generation inspired by Allstate claims datasets
