"""Configuration settings for the Insurance Claims Agent POC."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
MODELS_DIR = PROJECT_ROOT / "models"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))

# Data Configuration
CLAIMS_DATA_PATH = DATA_DIR / "claims_data.csv"
POLICIES_DATA_PATH = DATA_DIR / "policies_data.csv"
DECISIONS_LOG_PATH = DATA_DIR / "decisions_log.json"

# Agent Configuration
MAX_ITERATIONS = 5
AGENT_VERBOSE = True

# Risk Thresholds
RISK_THRESHOLD_HIGH = 0.7
RISK_THRESHOLD_MEDIUM = 0.4

# Severity Levels
SEVERITY_LEVELS = ["low", "medium", "high", "critical"]
ACTIONS = ["approve", "investigate", "deny", "escalate"]

