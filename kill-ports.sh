#!/bin/bash

echo "=========================================="
echo "🛑 KILLING PROCESSES ON PORTS 80, 443, 8000"
echo "=========================================="

# Function to kill processes on a port
kill_port() {
    local port=$1
    local port_name=$2
    
    echo "🔍 Step $3: Killing processes on port $port ($port_name)..."
    echo "🔍 Checking port $port..."
    
    # Find processes using the port
    local pids=$(sudo lsof -ti:$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo "⚠️  Found processes on port $port: $pids"
        echo "🛑 Killing processes on port $port..."
        
        # Kill processes gracefully first
        for pid in $pids; do
            echo "🔄 Sending SIGTERM to PID $pid..."
            sudo kill -TERM $pid 2>/dev/null
        done
        
        # Wait a moment
        sleep 2
        
        # Force kill if still running
        pids=$(sudo lsof -ti:$port 2>/dev/null)
        if [ -n "$pids" ]; then
            echo "🔄 Force killing remaining processes..."
            for pid in $pids; do
                echo "💀 Sending SIGKILL to PID $pid..."
                sudo kill -KILL $pid 2>/dev/null
            done
        fi
        
        # Final check
        sleep 1
        if sudo lsof -ti:$port >/dev/null 2>&1; then
            echo "❌ Port $port is still in use"
            return 1
        else
            echo "✅ Port $port is now free"
            return 0
        fi
    else
        echo "✅ Port $port is already free"
        return 0
    fi
}

# Kill processes on each port
kill_port 80 "HTTP" 1
kill_port 443 "HTTPS" 2
kill_port 8000 "FastAPI" 3

echo ""
echo "🔍 Step 4: Killing any remaining uvicorn processes..."
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true

echo ""
echo "🔍 Step 5: Final verification..."
echo "📊 Port Status:"

# Check final status
if netstat -tuln 2>/dev/null | grep -q ":80 "; then
    echo "❌ Port 80: IN USE"
else
    echo "✅ Port 80: FREE"
fi

if netstat -tuln 2>/dev/null | grep -q ":443 "; then
    echo "❌ Port 443: IN USE"
else
    echo "✅ Port 443: FREE"
fi

if netstat -tuln 2>/dev/null | grep -q ":8000 "; then
    echo "❌ Port 8000: IN USE"
else
    echo "✅ Port 8000: FREE"
fi

echo ""
echo "🎯 All ports are now ready for service startup!"
echo "💡 You can now run:"
echo "   ./start-development.sh"
echo "   ./start-production-no-ssl.sh"
echo "   ./start-production-ssl.sh"