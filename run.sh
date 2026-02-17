#!/bin/bash

# DocMind AI - Run Script
# Starts both backend and frontend in parallel

set -e

echo "🚀 Starting DocMind AI..."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Please run ./setup.sh first"
    exit 1
fi

# Create necessary directories
mkdir -p data/chroma uploads logs

# Start Redis if not running
if ! redis-cli ping &> /dev/null; then
    echo "Starting Redis..."
    sudo systemctl start redis 2>/dev/null || echo "Warning: Could not start Redis automatically"
fi

# Start Backend
echo "Starting FastAPI backend on http://localhost:8000..."
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start Frontend (if exists)
if [ -d "frontend" ]; then
    echo "Starting Next.js frontend on http://localhost:3000..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
fi

echo ""
echo "======================================"
echo "✅ DocMind AI is running!"
echo "======================================"
echo ""
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait
