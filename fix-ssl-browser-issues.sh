#!/bin/bash

echo "=========================================="
echo "🔧 FIXING SSL BROWSER ISSUES"
echo "=========================================="

# Get domain from environment or use default
DOMAIN=${DOMAIN:-"yourdomain.com"}

echo "🔍 Step 1: Checking current SSL certificate status..."

# Check if certbot is available
if command -v certbot &> /dev/null; then
    echo "✅ Certbot found"
    
    # Check certificate status
    if certbot certificates | grep -q "$DOMAIN"; then
        echo "✅ SSL certificate found for $DOMAIN"
        certbot certificates | grep "$DOMAIN" -A 5
        
        # Check certificate expiration
        echo ""
        echo "🔍 Checking certificate expiration..."
        certbot certificates | grep "$DOMAIN" -A 10 | grep "VALID"
    else
        echo "❌ SSL certificate not found for $DOMAIN"
        echo "🔧 Creating new SSL certificate..."
        sudo certbot certonly --standalone -d $DOMAIN
    fi
else
    echo "❌ Certbot not found"
    echo "🔧 Installing certbot..."
    sudo apt update
    sudo apt install -y certbot
fi

echo ""
echo "🔍 Step 2: Checking Nginx configuration..."

# Check Nginx configuration
if [ -f "/etc/nginx/sites-available/$DOMAIN" ]; then
    echo "✅ Nginx config found"
    
    # Check SSL configuration in Nginx
    if grep -q "ssl_certificate" "/etc/nginx/sites-available/$DOMAIN"; then
        echo "✅ SSL configuration found in Nginx"
    else
        echo "❌ SSL configuration missing in Nginx"
        echo "🔧 Updating Nginx configuration..."
        sudo ./setup-lets-encrypt.sh
    fi
else
    echo "❌ Nginx config not found"
    echo "🔧 Creating Nginx configuration..."
    sudo ./setup-lets-encrypt.sh
fi

echo ""
echo "🔍 Step 3: Checking system time and date..."

# Check system time
echo "📅 Current system time: $(date)"
echo "🌍 Timezone: $(timedatectl show --property=Timezone --value 2>/dev/null || echo 'Unknown')"

# Check if time is synchronized
if command -v timedatectl &> /dev/null; then
    if timedatectl status | grep -q "synchronized: yes"; then
        echo "✅ System time is synchronized"
    else
        echo "⚠️  System time may not be synchronized"
        echo "🔧 Syncing system time..."
        sudo timedatectl set-ntp true
    fi
fi

echo ""
echo "🔍 Step 4: Clearing browser cache and SSL state..."

echo "🧹 Clearing system SSL cache..."
sudo rm -rf /var/cache/nginx/* 2>/dev/null || true
sudo rm -rf /tmp/nginx* 2>/dev/null || true

echo "🔄 Restarting Nginx..."
sudo systemctl restart nginx 2>/dev/null || true

echo ""
echo "🔍 Step 5: Testing SSL connection..."

# Test SSL connection
echo "🔐 Testing SSL connection to $DOMAIN..."
if command -v openssl &> /dev/null; then
    echo "SSL Certificate Info:"
    echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates
else
    echo "⚠️  OpenSSL not available for testing"
fi

echo ""
echo "🔍 Step 6: Browser-specific fixes..."

echo "🌐 Chrome/Edge fixes:"
echo "   1. Open chrome://flags/"
echo "   2. Search for 'Insecure origins treated as secure'"
echo "   3. Add your domain: https://$DOMAIN"
echo "   4. Restart browser"

echo ""
echo "🦊 Firefox fixes:"
echo "   1. Open about:config"
echo "   2. Search for 'security.enterprise_roots.enabled'"
echo "   3. Set to 'true'"
echo "   4. Restart browser"

echo ""
echo "🔍 Step 7: Creating browser trust script..."

# Create browser trust script
cat > trust-ssl-browser.sh << 'EOF'
#!/bin/bash

echo "🔐 Adding SSL certificate to browser trust..."

# Get domain
DOMAIN=${DOMAIN:-"yourdomain.com"}

echo "📋 Instructions for browser trust:"

echo ""
echo "🌐 Chrome/Edge:"
echo "1. Open https://$DOMAIN"
echo "2. Click 'Advanced' or 'Details'"
echo "3. Click 'Proceed to $DOMAIN (unsafe)'"
echo "4. Click the lock icon in address bar"
echo "5. Click 'Certificate'"
echo "6. Click 'Install Certificate'"
echo "7. Choose 'Trusted Root Certification Authorities'"
echo "8. Click 'OK'"

echo ""
echo "🦊 Firefox:"
echo "1. Open https://$DOMAIN"
echo "2. Click 'Advanced'"
echo "3. Click 'Accept the Risk and Continue'"
echo "4. Click the lock icon"
echo "5. Click 'Connection secure'"
echo "6. Click 'More Information'"
echo "7. Click 'View Certificate'"
echo "8. Click 'Import'"
echo "9. Choose 'Trust this CA to identify websites'"

echo ""
echo "🍎 Safari:"
echo "1. Open https://$DOMAIN"
echo "2. Click 'Show Details'"
echo "3. Click 'visit this website'"
echo "4. Click 'Continue'"
echo "5. Enter your password if prompted"

echo ""
echo "✅ After following these steps, restart your browser"
EOF

chmod +x trust-ssl-browser.sh

echo ""
echo "🔍 Step 8: Creating automatic SSL renewal..."

# Create SSL renewal script
cat > renew-ssl.sh << 'EOF'
#!/bin/bash

echo "🔄 Renewing SSL certificate..."

# Get domain
DOMAIN=${DOMAIN:-"yourdomain.com"}

# Renew certificate
if command -v certbot &> /dev/null; then
    echo "🔄 Running certbot renew..."
    sudo certbot renew --quiet
    
    # Reload Nginx
    echo "🔄 Reloading Nginx..."
    sudo systemctl reload nginx
    
    echo "✅ SSL certificate renewed successfully"
else
    echo "❌ Certbot not found"
fi
EOF

chmod +x renew-ssl.sh

echo ""
echo "🔍 Step 9: Setting up automatic renewal..."

# Add to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * $(pwd)/renew-ssl.sh >> /var/log/ssl-renewal.log 2>&1") | crontab -

echo ""
echo "🎯 SSL Browser Issues Fixed!"
echo ""
echo "📋 Next Steps:"
echo "1. Run: ./trust-ssl-browser.sh"
echo "2. Follow browser-specific instructions"
echo "3. Restart your browser"
echo "4. Test: https://$DOMAIN"
echo ""
echo "🔄 SSL will auto-renew daily at 2 AM"
echo "📝 Check logs: tail -f /var/log/ssl-renewal.log"