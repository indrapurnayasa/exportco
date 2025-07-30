#!/bin/bash

SERVICE="hackathon"
UNIT="${SERVICE}.service"
NGINX_UNIT="nginx"
DOMAIN="dev-ngurah.fun"
APP_PORT=8000
DB_USER="maverick"
DB_PASS="Hackathon2025"
DB_NAME="hackathondb"

function log() {
    echo -e "\033[0;32m[$(date +'%Y-%m-%d %H:%M:%S')] $1\033[0m"
}

function start_service() {
    log "Starting $SERVICE..."
    sudo systemctl start $UNIT
}

function stop_service() {
    log "Stopping $SERVICE..."
    sudo systemctl stop $UNIT
}

function restart_service() {
    log "Restarting $SERVICE..."
    sudo systemctl restart $UNIT
}

function status_service() {
    sudo systemctl status $UNIT
}

function log_service() {
    sudo journalctl -u $UNIT -f
}

function nginx_restart() {
    log "Restarting NGINX..."
    sudo systemctl restart $NGINX_UNIT
}

function nginx_status() {
    sudo systemctl status $NGINX_UNIT
}

function nginx_log() {
    sudo journalctl -u $NGINX_UNIT -f
}

function setup_ssl() {
    log "Setting up SSL with certbot..."
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
    sudo certbot --nginx -d $DOMAIN
}

function check_db() {
    log "Checking database connection..."
    if ! PGPASSWORD=$DB_PASS psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT 1;" 2>/dev/null | grep -q "1"; then
        log "❌ Database connection failed! Please check PostgreSQL."
        exit 1
    else
        log "✅ Database connection successful."
    fi
}

function kill_ports() {
    log "Killing all processes on ports 80, 443, 8000..."
    sudo fuser -k 80/tcp 2>/dev/null || true
    sudo fuser -k 443/tcp 2>/dev/null || true
    sudo fuser -k 8000/tcp 2>/dev/null || true
    sudo pkill -f "nginx" 2>/dev/null || true
    sudo pkill -f "uvicorn" 2>/dev/null || true
    sudo pkill -f "python.*8000" 2>/dev/null || true
    sleep 2
}

function full_deploy() {
    log "=== Starting Full Automated Deployment ==="
    kill_ports
    check_db
    log "Stopping nginx if running..."
    sudo systemctl stop $NGINX_UNIT 2>/dev/null || true
    sudo pkill -f "nginx" 2>/dev/null || true
    sleep 2
    setup_ssl
    log "Testing nginx configuration..."
    sudo nginx -t
    log "Starting nginx..."
    sudo systemctl start $NGINX_UNIT
    sudo systemctl enable $NGINX_UNIT
    log "Restarting $SERVICE service..."
    sudo systemctl stop $UNIT 2>/dev/null || true
    sudo pkill -f "$SERVICE" 2>/dev/null || true
    sudo pkill -f "uvicorn.*8000" 2>/dev/null || true
    sleep 2
    sudo systemctl start $UNIT
    sleep 10
    log "Testing external access to https://$DOMAIN/health ..."
    if curl -s -f "https://$DOMAIN/health" >/dev/null; then
        log "✅ External HTTPS access is working!"
    else
        log "❌ External HTTPS access failed! Please check nginx and service logs."
        exit 1
    fi
    log "=== Deployment completed successfully! ==="
}

function help_menu() {
    echo "Usage: $0 {start|stop|restart|status|log|nginx-restart|nginx-status|nginx-log|setup-ssl|full-deploy|help}"
    echo ""
    echo "  start         Start the FastAPI service"
    echo "  stop          Stop the FastAPI service"
    echo "  restart       Restart the FastAPI service"
    echo "  status        Show FastAPI service status"
    echo "  log           Show FastAPI service logs"
    echo "  nginx-restart Restart NGINX"
    echo "  nginx-status  Show NGINX status"
    echo "  nginx-log     Show NGINX logs"
    echo "  setup-ssl     Setup SSL certificate with certbot"
    echo "  full-deploy   Full clean deployment (kill ports, check db, stop nginx, setup cert, start nginx, start service, test external access)"
    echo "  help          Show this help menu"
}

case "$1" in
    start) start_service ;;
    stop) stop_service ;;
    restart) restart_service ;;
    status) status_service ;;
    log) log_service ;;
    nginx-restart) nginx_restart ;;
    nginx-status) nginx_status ;;
    nginx-log) nginx_log ;;
    setup-ssl) setup_ssl ;;
    full-deploy) full_deploy ;;
    help|*) help_menu ;;
esac