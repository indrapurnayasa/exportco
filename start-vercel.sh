#!/bin/bash

echo "=========================================="
echo "🚀 STARTING SERVICE FOR VERCEL DEPLOYMENT"
echo "=========================================="

# Kill any processes using our ports first
echo "🛑 Clearing ports before startup..."
./kill-ports.sh

echo ""
echo "🚀 Starting service for Vercel..."

# Check if conda is available and activate environment
if command -v conda &> /dev/null; then
    echo "Activating conda environment..."
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate hackathon-env
else
    echo "Conda not found, using system Python..."
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start FastAPI service optimized for Vercel
echo "Starting FastAPI service on port 8000..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 > logs/uvicorn-vercel.log 2>&1 &

# Wait for service to start
sleep 5

# Check if service is running
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo "✅ FastAPI service started successfully"
    echo "🌐 Your API is now available at:"
    echo "   http://localhost:8000/api/v1/export/seasonal-trend"
    echo "   http://localhost:8000/docs"
    echo "   http://localhost:8000/health"
    echo ""
    echo "📝 Logs are available at: logs/uvicorn-vercel.log"
    echo "🔍 To monitor logs: tail -f logs/uvicorn-vercel.log"
    echo ""
    echo "🎯 Vercel Configuration:"
    echo "   - Port: 8000"
    echo "   - Host: 0.0.0.0"
    echo "   - Workers: 1 (optimized for Vercel)"
    echo "   - SSL: Handled by Vercel"
    echo ""
    echo "🛑 To stop: ./stop-production-ssl.sh"
else
    echo "❌ Failed to start FastAPI service"
    echo "Check logs: tail -f logs/uvicorn-vercel.log"
    exit 1
fi