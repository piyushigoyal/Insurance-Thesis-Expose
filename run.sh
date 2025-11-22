#!/bin/bash
# Quick start script for Insurance Claims Agent POC

echo "🛡️  ZURICH INSURANCE"
echo "AI Claims Agent POC"
echo "================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "Please edit .env and add your API keys before proceeding."
    exit 1
fi

# Check if data exists
if [ ! -f "data/claims_data.csv" ]; then
    echo "📊 Generating Zurich Insurance claims data..."
    python data_generator.py
fi

# Launch Streamlit app
echo ""
echo "🚀 Launching Zurich Insurance Claims Agent..."
echo "================================"
echo ""
streamlit run streamlit_app.py

