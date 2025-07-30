#!/bin/bash

echo "=========================================="
echo "📊 PRODUCTION SERVICE STATUS"
echo "=========================================="

# Get domain from environment or use dev-ngurah.fun
DOMAIN=${DOMAIN:-"dev-ngurah.fun"}

# Check FastAPI service
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo "✅ FastAPI service: RUNNING"
    echo "   Process ID: $(pgrep -f 'uvicorn.*app.main:app')"
else
    echo "❌ FastAPI service: STOPPED"
fi

# Check Nginx
if command -v systemctl &> /dev/null; then
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx service: RUNNING"
    else
        echo "❌ Nginx service: STOPPED"
    fi
elif pgrep -f nginx > /dev/null; then
    echo "✅ Nginx service: RUNNING"
else
    echo "❌ Nginx service: STOPPED"
fi

# Check SSL certificate
if command -v certbot &> /dev/null; then
    if certbot certificates | grep -q "$DOMAIN"; then
        echo "✅ SSL certificate: VALID"
        certbot certificates | grep "$DOMAIN" -A 5
    else
        echo "❌ SSL certificate: NOT FOUND"
    fi
else
    echo "⚠️  Certbot not found - SSL certificate status unknown"
fi

# Check ports
echo ""
echo "🔍 Port Status:"
if netstat -tuln 2>/dev/null | grep -q ":80 "; then
    echo "✅ Port 80: IN USE"
else
    echo "❌ Port 80: FREE"
fi

if netstat -tuln 2>/dev/null | grep -q ":443 "; then
    echo "✅ Port 443: IN USE"
else
    echo "❌ Port 443: FREE"
fi

if netstat -tuln 2>/dev/null | grep -q ":8000 "; then
    echo "✅ Port 8000: IN USE"
else
    echo "❌ Port 8000: FREE"
fi

# Check service health
echo ""
echo "🏥 Service Health:"
if curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/health 2>/dev/null | grep -q "200"; then
    echo "✅ HTTPS Health Check: OK"
else
    echo "❌ HTTPS Health Check: FAILED"
fi

if curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN 2>/dev/null | grep -q "301"; then
    echo "✅ HTTP Redirect: OK"
else
    echo "❌ HTTP Redirect: FAILED"
fi

# Check SSL certificate validity
echo ""
echo "🔐 SSL Certificate Details:"
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo "✅ Certificate file exists"
    openssl x509 -in /etc/letsencrypt/live/$DOMAIN/fullchain.pem -text -noout 2>/dev/null | grep -E "(Subject|Issuer|Not After)" | head -3
else
    echo "❌ Certificate file not found"
fi

echo ""
echo "🌐 Service URLs:"
echo "   https://$DOMAIN/api/v1/export/seasonal-trend"
echo "   https://$DOMAIN/docs"
echo "   https://$DOMAIN/health"