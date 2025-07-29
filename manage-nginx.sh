#!/bin/bash

echo "=========================================="
echo "🌐 NGINX SERVICE MANAGEMENT"
echo "=========================================="

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        log "✅ $1"
    else
        log "❌ $1"
        return 1
    fi
}

# Check Nginx service status
log "📊 Checking Nginx service status..."
if sudo systemctl is-active --quiet nginx; then
    log "✅ Nginx is running"
    sudo systemctl status nginx --no-pager -l
else
    log "❌ Nginx is not running"
fi

echo ""
echo "🔧 Nginx Management Options:"
echo "1. Start Nginx"
echo "2. Stop Nginx"
echo "3. Restart Nginx"
echo "4. Reload Nginx"
echo "5. Check Nginx configuration"
echo "6. View Nginx error logs"
echo "7. Test Nginx configuration"
echo "8. Enable Nginx to start on boot"
echo "9. Disable Nginx from starting on boot"
echo "0. Exit"

read -p "Choose an option (0-9): " choice

case $choice in
    1)
        log "🚀 Starting Nginx..."
        sudo systemctl start nginx
        check_status "Nginx started"
        ;;
    2)
        log "🛑 Stopping Nginx..."
        sudo systemctl stop nginx
        check_status "Nginx stopped"
        ;;
    3)
        log "🔄 Restarting Nginx..."
        sudo systemctl restart nginx
        check_status "Nginx restarted"
        ;;
    4)
        log "🔄 Reloading Nginx..."
        sudo systemctl reload nginx
        check_status "Nginx reloaded"
        ;;
    5)
        log "🔍 Checking Nginx configuration..."
        sudo nginx -t
        check_status "Nginx configuration check"
        ;;
    6)
        log "📋 Viewing Nginx error logs..."
        sudo tail -n 20 /var/log/nginx/error.log
        ;;
    7)
        log "🧪 Testing Nginx configuration..."
        sudo nginx -t
        check_status "Nginx configuration test"
        ;;
    8)
        log "🔧 Enabling Nginx to start on boot..."
        sudo systemctl enable nginx
        check_status "Nginx enabled for boot"
        ;;
    9)
        log "🔧 Disabling Nginx from starting on boot..."
        sudo systemctl disable nginx
        check_status "Nginx disabled from boot"
        ;;
    0)
        log "👋 Exiting..."
        exit 0
        ;;
    *)
        log "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
log "📊 Final Nginx status:"
sudo systemctl status nginx --no-pager -l