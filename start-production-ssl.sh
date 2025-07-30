#!/bin/bash

echo "=========================================="
echo "🚀 STARTING PRODUCTION SERVICE WITH SSL"
echo "=========================================="

# Kill any processes using our ports first
echo "🛑 Clearing ports before startup..."
./kill-ports.sh

echo ""
echo "🚀 Starting production service..."

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

# Start FastAPI service (HTTP only, Nginx handles HTTPS)
echo "Starting FastAPI service on port 8000..."
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4 > logs/uvicorn-ssl.log 2>&1 &

# Wait for service to start
sleep 5

# Check if service is running
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo "✅ FastAPI service started successfully"
    echo "🌐 Your API is now available at:"
    echo "   https://dev-ngurah.fun/api/v1/export/seasonal-trend"
    echo "   https://dev-ngurah.fun/docs"
    echo "   https://dev-ngurah.fun/health"
    echo ""
    echo "📝 Logs are available at: logs/uvicorn-ssl.log"
    echo "🔍 To monitor logs: tail -f logs/uvicorn-ssl.log"
    echo ""
    echo "🔧 To stop the service: ./stop-production-ssl.sh"
    echo "📊 To check status: ./status-production-ssl.sh"
else
    echo "❌ Failed to start FastAPI service"
    echo "Check logs: tail -f logs/uvicorn-ssl.log"
    exit 1
fi
