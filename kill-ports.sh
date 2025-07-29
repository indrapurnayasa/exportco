#!/bin/bash

echo "=========================================="
echo "🛑 KILLING PROCESSES ON PORTS 80, 443, 8000"
echo "=========================================="

# Function to kill processes on a specific port
kill_port() {
    local port=$1
    echo "🔍 Checking port $port..."
    
    # Find processes using the port
    local pids=$(lsof -ti :$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo "⚠️  Found processes on port $port: $pids"
        echo "🛑 Killing processes on port $port..."
        
        # Kill processes gracefully first
        kill $pids 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        local remaining_pids=$(lsof -ti :$port 2>/dev/null)
        if [ -n "$remaining_pids" ]; then
            echo "💀 Force killing remaining processes on port $port..."
            kill -9 $remaining_pids 2>/dev/null || true
            sleep 1
        fi
        
        # Verify port is free
        if lsof -i :$port 2>/dev/null > /dev/null; then
            echo "❌ Failed to free port $port"
            return 1
        else
            echo "✅ Port $port is now free"
        fi
    else
        echo "✅ Port $port is already free"
    fi
}

# Kill processes on each port
echo "🔍 Step 1: Killing processes on port 80 (HTTP)..."
kill_port 80

echo ""
echo "🔍 Step 2: Killing processes on port 443 (HTTPS)..."
kill_port 443

echo ""
echo "🔍 Step 3: Killing processes on port 8000 (FastAPI)..."
kill_port 8000

echo ""
echo "🔍 Step 4: Killing any remaining uvicorn processes..."
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
pkill -f "python.*app.main" 2>/dev/null || true

echo ""
echo "🔍 Step 5: Final verification..."
echo "📊 Port Status:"

# Check each port
for port in 80 443 8000; do
    if lsof -i :$port 2>/dev/null > /dev/null; then
        echo "❌ Port $port: STILL IN USE"
        lsof -i :$port
    else
        echo "✅ Port $port: FREE"
    fi
done

echo ""
echo "🎯 All ports are now ready for service startup!"
echo "💡 You can now run:"
echo "   ./start-development.sh"
echo "   ./start-production-no-ssl.sh"
echo "   ./start-production-ssl.sh"