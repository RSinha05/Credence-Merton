#!/bin/bash

echo "===================================================="
echo "🏦 Starting Aurelis / Credence-MertonX Platform"
echo "===================================================="

# Check if ports are in use
PID_API=$(lsof -ti:8000)
if [ ! -z "$PID_API" ]; then
  kill -9 $PID_API
fi

PID_UI=$(lsof -ti:5173)
if [ ! -z "$PID_UI" ]; then
  kill -9 $PID_UI
fi

echo "🚀 Starting FastAPI Backend (Multi-Asset & Retail API)..."
uvicorn api.app:app --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
FASTAPI_PID=$!

sleep 2

echo "✨ Starting Aurelis Frontend (Vite/React)..."
cd frontend && npm run dev -- --open &
VITE_PID=$!

# Cleanup on exit
trap "kill $FASTAPI_PID $VITE_PID" EXIT
wait
