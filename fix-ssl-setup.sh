#!/bin/bash

echo "=========================================="
echo "🔧 SSL SETUP DIAGNOSTIC & FIX"
echo "=========================================="

# Get domain from environment or use default
DOMAIN=${DOMAIN:-"yourdomain.com"}

echo "🔍 Step 1: Checking current status..."

# Check what's using port 8000
echo "📊 Port 8000 status:"
if lsof -i :8000 2>/dev/null; then
    echo "⚠️  Port 8000 is in use. Stopping existing processes..."
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    pkill -f "python.*app.main" 2>/dev/null || true
    sleep 2
    if lsof -i :8000 2>/dev/null; then
        echo "❌ Failed to free port 8000"
        echo "   Please manually stop the process using port 8000"
        exit 1
    else
        echo "✅ Port 8000 is now free"
    fi
else
    echo "✅ Port 8000 is free"
fi

echo ""
echo "🔍 Step 2: Checking SSL certificate..."

# Check if SSL certificate exists
if command -v certbot &> /dev/null; then
    if certbot certificates | grep -q "$DOMAIN"; then
        echo "✅ SSL certificate found for $DOMAIN"
    else
        echo "❌ SSL certificate not found for $DOMAIN"
        echo ""
        echo "🔧 To fix SSL certificate, run:"
        echo "   sudo ./setup-lets-encrypt.sh"
        echo ""
        echo "   OR manually:"
        echo "   sudo certbot certonly --standalone -d $DOMAIN"
    fi
else
    echo "❌ Certbot not installed"
    echo ""
    echo "🔧 To install certbot:"
    echo "   sudo apt update"
    echo "   sudo apt install -y certbot"
fi

echo ""
echo "🔍 Step 3: Checking Nginx..."

# Check Nginx installation and configuration
if command -v nginx &> /dev/null; then
    echo "✅ Nginx is installed"
    
    # Check if Nginx config exists
    if [ -f "/etc/nginx/sites-available/$DOMAIN" ]; then
        echo "✅ Nginx config found"
    else
        echo "❌ Nginx config not found"
        echo ""
        echo "🔧 To create Nginx config, run:"
        echo "   sudo ./setup-lets-encrypt.sh"
    fi
else
    echo "❌ Nginx not installed"
    echo ""
    echo "🔧 To install Nginx:"
    echo "   sudo apt update"
    echo "   sudo apt install -y nginx"
fi

echo ""
echo "🔍 Step 4: Quick Fix Options..."

echo "1️⃣  For development (no SSL):"
echo "   ./start-development.sh"
echo ""

echo "2️⃣  For production with SSL (recommended):"
echo "   sudo ./setup-lets-encrypt.sh"
echo "   ./start-production-ssl.sh"
echo ""

echo "3️⃣  For production without SSL (temporary):"
echo "   ./start-production-no-ssl.sh"
echo ""

echo "4️⃣  Check current status:"
echo "   ./status-production-ssl.sh"