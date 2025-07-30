#!/bin/bash

echo "=========================================="
echo "🧹 CLEARING BROWSER CACHE & SSL STATE"
echo "=========================================="

echo "🔍 Step 1: Clearing system SSL cache..."

# Clear system SSL cache
sudo rm -rf /var/cache/nginx/* 2>/dev/null || true
sudo rm -rf /tmp/nginx* 2>/dev/null || true
sudo rm -rf /var/lib/nginx/* 2>/dev/null || true

echo "✅ System SSL cache cleared"

echo ""
echo "🔍 Step 2: Browser-specific cache clearing..."

echo "🌐 Chrome/Edge cache locations:"
echo "   Linux: ~/.config/google-chrome/Default/Cache"
echo "   macOS: ~/Library/Caches/Google/Chrome/Default"
echo "   Windows: %LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache"

echo ""
echo "🦊 Firefox cache locations:"
echo "   Linux: ~/.mozilla/firefox/*.default*/cache2"
echo "   macOS: ~/Library/Caches/Firefox/Profiles"
echo "   Windows: %APPDATA%\\Mozilla\\Firefox\\Profiles"

echo ""
echo "🍎 Safari cache locations:"
echo "   macOS: ~/Library/Caches/com.apple.Safari"

echo ""
echo "🔍 Step 3: Creating browser cache clearing scripts..."

# Create Chrome cache clearing script
cat > clear-chrome-cache.sh << 'EOF'
#!/bin/bash

echo "🧹 Clearing Chrome/Edge cache..."

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    rm -rf ~/.config/google-chrome/Default/Cache/* 2>/dev/null || true
    rm -rf ~/.config/google-chrome/Default/Code\ Cache/* 2>/dev/null || true
    rm -rf ~/.config/google-chrome/Default/GPUCache/* 2>/dev/null || true
    echo "✅ Chrome cache cleared (Linux)"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    rm -rf ~/Library/Caches/Google/Chrome/Default/* 2>/dev/null || true
    rm -rf ~/Library/Application\ Support/Google/Chrome/Default/Cache/* 2>/dev/null || true
    echo "✅ Chrome cache cleared (macOS)"
else
    echo "⚠️  Manual clearing required for this OS"
    echo "   Clear: %LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache"
fi
EOF

chmod +x clear-chrome-cache.sh

# Create Firefox cache clearing script
cat > clear-firefox-cache.sh << 'EOF'
#!/bin/bash

echo "🧹 Clearing Firefox cache..."

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    rm -rf ~/.mozilla/firefox/*.default*/cache2/* 2>/dev/null || true
    rm -rf ~/.mozilla/firefox/*.default*/storage/* 2>/dev/null || true
    echo "✅ Firefox cache cleared (Linux)"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    rm -rf ~/Library/Caches/Firefox/Profiles/*/cache2/* 2>/dev/null || true
    rm -rf ~/Library/Application\ Support/Firefox/Profiles/*/storage/* 2>/dev/null || true
    echo "✅ Firefox cache cleared (macOS)"
else
    echo "⚠️  Manual clearing required for this OS"
    echo "   Clear: %APPDATA%\\Mozilla\\Firefox\\Profiles"
fi
EOF

chmod +x clear-firefox-cache.sh

# Create Safari cache clearing script
cat > clear-safari-cache.sh << 'EOF'
#!/bin/bash

echo "🧹 Clearing Safari cache..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS only
    rm -rf ~/Library/Caches/com.apple.Safari/* 2>/dev/null || true
    rm -rf ~/Library/Safari/LocalStorage/* 2>/dev/null || true
    echo "✅ Safari cache cleared"
else
    echo "⚠️  Safari is only available on macOS"
fi
EOF

chmod +x clear-safari-cache.sh

echo ""
echo "🔍 Step 4: Creating comprehensive cache clearing script..."

# Create comprehensive cache clearing script
cat > clear-all-browser-cache.sh << 'EOF'
#!/bin/bash

echo "🧹 Clearing ALL browser caches..."

# Run all cache clearing scripts
./clear-chrome-cache.sh
./clear-firefox-cache.sh
./clear-safari-cache.sh

echo ""
echo "🔄 Restarting browsers..."
echo "   Please close all browser windows and restart them"

echo ""
echo "📋 Manual steps for complete cache clearing:"
echo ""
echo "🌐 Chrome/Edge:"
echo "1. Open chrome://settings/clearBrowserData"
echo "2. Select 'All time' for time range"
echo "3. Check 'Cached images and files'"
echo "4. Check 'Cookies and other site data'"
echo "5. Click 'Clear data'"
echo ""
echo "🦊 Firefox:"
echo "1. Open about:preferences#privacy"
echo "2. Click 'Clear Data' under 'Cookies and Site Data'"
echo "3. Check 'Cached Web Content'"
echo "4. Click 'Clear'"
echo ""
echo "🍎 Safari:"
echo "1. Open Safari > Preferences > Privacy"
echo "2. Click 'Manage Website Data'"
echo "3. Click 'Remove All'"
echo "4. Go to Develop > Empty Caches"
EOF

chmod +x clear-all-browser-cache.sh

echo ""
echo "🔍 Step 5: Creating SSL certificate reset script..."

# Create SSL certificate reset script
cat > reset-ssl-certificates.sh << 'EOF'
#!/bin/bash

echo "🔐 Resetting SSL certificates..."

# Clear SSL certificate cache
sudo rm -rf /etc/ssl/certs/* 2>/dev/null || true
sudo update-ca-certificates 2>/dev/null || true

# Clear browser SSL state
echo "🧹 Clearing browser SSL state..."

# Chrome/Edge SSL state
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    rm -rf ~/.config/google-chrome/Default/Network\ Persistent\ State 2>/dev/null || true
elif [[ "$OSTYPE" == "darwin"* ]]; then
    rm -rf ~/Library/Application\ Support/Google/Chrome/Default/Network\ Persistent\ State 2>/dev/null || true
fi

# Firefox SSL state
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    rm -rf ~/.mozilla/firefox/*.default*/cert8.db 2>/dev/null || true
    rm -rf ~/.mozilla/firefox/*.default*/cert9.db 2>/dev/null || true
elif [[ "$OSTYPE" == "darwin"* ]]; then
    rm -rf ~/Library/Application\ Support/Firefox/Profiles/*/cert8.db 2>/dev/null || true
    rm -rf ~/Library/Application\ Support/Firefox/Profiles/*/cert9.db 2>/dev/null || true
fi

echo "✅ SSL certificates reset"
echo "🔄 Please restart your browser"
EOF

chmod +x reset-ssl-certificates.sh

echo ""
echo "🎯 Browser Cache Clearing Complete!"
echo ""
echo "📋 Available scripts:"
echo "   - clear-chrome-cache.sh"
echo "   - clear-firefox-cache.sh"
echo "   - clear-safari-cache.sh"
echo "   - clear-all-browser-cache.sh"
echo "   - reset-ssl-certificates.sh"
echo ""
echo "🚀 Quick fix:"
echo "   ./clear-all-browser-cache.sh"
echo "   ./reset-ssl-certificates.sh"
echo ""
echo "📱 Then restart your browser and test your site"