#!/bin/bash

echo "===================================================="
echo "🏦 Starting Credence-MertonX Full Platform Pipeline"
echo "===================================================="

# Check if port 8000 is in use, kill if necessary (prevents uvicorn clashes)
PID=$(lsof -ti:8000)
if [ ! -z "$PID" ]; then
  echo "Killing existing FastAPI process on port 8000..."
  kill -9 $PID
fi

# 1. Start the FastAPI Backend Pipeline in the background
echo "🚀 Starting FastAPI Backend (Multi-Asset & Retail API)..."
uvicorn api.app:app --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
FASTAPI_PID=$!

echo "Waiting for API to initialize..."
sleep 5

# 2. Start the Streamlit Frontend
echo "📊 Starting Streamlit Dashboard..."
streamlit run dashboard/app.py --server.port 8501

# Cleanup when Streamlit is closed via Ctrl+C
trap "kill $FASTAPI_PID" EXIT
