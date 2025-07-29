#!/bin/bash

echo "=========================================="
echo "🛑 STOPPING PRODUCTION SERVICE"
echo "=========================================="

# Stop FastAPI service
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true

# Stop Nginx if running
if command -v systemctl &> /dev/null; then
    systemctl stop nginx 2>/dev/null || true
elif command -v service &> /dev/null; then
    service nginx stop 2>/dev/null || true
else
    pkill -f nginx 2>/dev/null || true
fi

echo "✅ Services stopped"
echo "📝 You can restart with: ./start-production-ssl.sh"