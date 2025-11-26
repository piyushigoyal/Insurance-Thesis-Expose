# Quick Start Guide
## Zurich Insurance - AI Claims Agent POC

Get the Zurich Insurance Claims Agent POC up and running in 5 minutes!

## 🚀 Quick Start (macOS/Linux)

### 1. Set up environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API key

Edit `.env` and add your API key:

```
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.1
```

### 3. Generate data

```bash
python data_generator.py
```

Expected output:
```
Generating insurance claims data...
✓ Saved 200 claims to data/claims_data.csv
✓ Saved XX policies to data/policies_data.csv
```

### 4. Launch the app

```bash
streamlit run streamlit_app.py
```

## 🚀 Alternative: Use the Run Script

```bash
chmod +x run.sh
./run.sh
```

## 🖥️ Using the UI

### Process Claims Tab

1. Select a claim from the dropdown
2. Click "🚀 Process Claim"
3. Review the agent's decision
4. Either:
   - Click "✅ Accept Decision" to approve
   - Click "⚠️ Override Decision" to change it

### History Tab

- View all processed claims
- See override rate and statistics
- Export decision history

### Evaluation Tab

1. Choose number of test claims (10-100)
2. Click "🚀 Run Evaluation"
3. Wait for comparison of all three systems
4. View metrics and determine best performer

## 🧪 Command Line Usage

### Test the Agent

```bash
python agent.py
```

### Run Full Evaluation

```bash
python evaluation.py
```

## 📊 Understanding the Output

### Severity Levels
- **Low**: < $5,000
- **Medium**: $5,000 - $25,000
- **High**: $25,000 - $75,000
- **Critical**: > $75,000

### Actions
- **Approve**: Process claim automatically
- **Investigate**: Requires further review
- **Deny**: Reject claim
- **Escalate**: Send to senior adjuster


## 🎯 Next Steps

1. **Process Claims**: Try different claims and see how the agent handles them
2. **Override Decisions**: Test the human-in-the-loop feature
3. **Run Evaluation**: Compare the three systems
4. **Check Logs**: Explore `logs/` directory for detailed execution traces
5. **Customize**: Edit `config.py` to adjust thresholds and behavior

## 📚 Learn More

- Full architecture: `ARCHITECTURE.md`
- Configuration: `config.py`
- Extend the agent: `agent.py` and `tools.py`

---

Enjoy exploring the Zurich Insurance Claims Agent POC! 🎉

