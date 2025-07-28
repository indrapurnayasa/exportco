#!/bin/bash

# Hackathon Service Management Script
# Usage: ./hackathon-service.sh [start|stop|restart|status|logs]

set -e  # Exit on any error

# Configuration
SERVICE_NAME="hackathon-service"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$APP_DIR/logs"
PID_FILE="$APP_DIR/hackathon_service.pid"
PORT=${PORT:-8000}
HOST=${HOST:-"0.0.0.0"}
WORKERS=${WORKERS:-4}
ENVIRONMENT=${ENVIRONMENT:-"production"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ✅ $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ⚠️  $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ❌ $1"
}

# Function to check if service is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# Function to stop service
stop_service() {
    print_status "Stopping $SERVICE_NAME..."
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_status "Sending SIGTERM to process $pid..."
            kill -TERM "$pid"
            
            # Wait for graceful shutdown
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 30 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            if ps -p "$pid" > /dev/null 2>&1; then
                print_warning "Process not responding to SIGTERM, sending SIGKILL..."
                kill -KILL "$pid"
            fi
            
            print_success "Service stopped successfully"
        else
            print_warning "Process $pid not found"
        fi
        rm -f "$PID_FILE"
    else
        print_warning "PID file not found"
    fi
}

# Function to start service
start_service() {
    print_status "Starting $SERVICE_NAME..."
    
    # Check if already running
    if is_running; then
        print_error "Service is already running (PID: $(cat "$PID_FILE"))"
        exit 1
    fi
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    # Install dependencies if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        print_status "Installing/updating dependencies..."
        
        # Check Python version and fix distutils issue if needed
        python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if [[ "$python_version" == "3.12"* ]] || [[ "$python_version" == "3.13"* ]]; then
            print_warning "Detected Python $python_version, applying distutils fix..."
            pip install --upgrade pip setuptools>=68.0.0 wheel>=0.40.0
        fi
        
        # Install requirements
        pip install -r requirements.txt
    fi
    
    # Set environment variables
    export PYTHONPATH="$APP_DIR:$PYTHONPATH"
    export ENVIRONMENT="$ENVIRONMENT"
    
    # Start the service with uvicorn
    print_status "Starting server on $HOST:$PORT with $WORKERS workers..."
    
    nohup uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers "$WORKERS" \
        --log-level info \
        --access-log \
        --log-config /dev/null \
        > "$LOG_DIR/uvicorn.log" 2>&1 &
    
    local pid=$!
    echo "$pid" > "$PID_FILE"
    
    # Wait a moment for the service to start
    sleep 3
    
    # Check if service started successfully
    if ps -p "$pid" > /dev/null 2>&1; then
        print_success "Service started successfully (PID: $pid)"
        print_success "Server running on http://$HOST:$PORT"
        print_success "Health check: http://$HOST:$PORT/health"
        print_success "API docs: http://$HOST:$PORT/docs"
        print_success "Logs available in: $LOG_DIR/"
    else
        print_error "Failed to start service"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# Function to restart service
restart_service() {
    print_status "Restarting $SERVICE_NAME..."
    stop_service
    sleep 2
    start_service
}

# Function to show status
show_status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_success "Service is running (PID: $pid)"
        print_status "Server: http://$HOST:$PORT"
        print_status "Health: http://$HOST:$PORT/health"
    else
        print_error "Service is not running"
    fi
}

# Function to show logs
show_logs() {
    local log_type=${1:-"service"}
    case $log_type in
        "service"|"app")
            if [ -f "$LOG_DIR/hackathon_service.log" ]; then
                tail -f "$LOG_DIR/hackathon_service.log"
            else
                print_error "Service log file not found"
            fi
            ;;
        "api"|"requests")
            if [ -f "$LOG_DIR/api_requests.log" ]; then
                tail -f "$LOG_DIR/api_requests.log"
            else
                print_error "API requests log file not found"
            fi
            ;;
        "error"|"errors")
            if [ -f "$LOG_DIR/hackathon_service_errors.log" ]; then
                tail -f "$LOG_DIR/hackathon_service_errors.log"
            else
                print_error "Error log file not found"
            fi
            ;;
        "uvicorn")
            if [ -f "$LOG_DIR/uvicorn.log" ]; then
                tail -f "$LOG_DIR/uvicorn.log"
            else
                print_error "Uvicorn log file not found"
            fi
            ;;
        *)
            print_error "Unknown log type. Available: service, api, error, uvicorn"
            ;;
    esac
}

# Function to show help
show_help() {
    echo "Hackathon Service Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the service"
    echo "  stop      Stop the service"
    echo "  restart   Restart the service"
    echo "  status    Show service status"
    echo "  logs      Show logs (default: service)"
    echo "  logs api  Show API request logs"
    echo "  logs error Show error logs"
    echo "  logs uvicorn Show uvicorn logs"
    echo "  help      Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  PORT        Server port (default: 8000)"
    echo "  HOST        Server host (default: 0.0.0.0)"
    echo "  WORKERS     Number of workers (default: 4)"
    echo "  ENVIRONMENT Environment (default: production)"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 stop"
    echo "  $0 restart"
    echo "  $0 status"
    echo "  $0 logs"
    echo "  PORT=9000 $0 start"
}

# Main script logic
case "${1:-help}" in
    "start")
        start_service
        ;;
    "stop")
        stop_service
        ;;
    "restart")
        restart_service
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "$2"
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac 