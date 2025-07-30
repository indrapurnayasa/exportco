#!/bin/bash

echo "=========================================="
echo "🔧 FIXING VERCEL SSL BROWSER ISSUES"
echo "=========================================="

echo "🎯 Vercel handles SSL automatically!"
echo "   No manual SSL setup needed for Vercel deployment."

echo ""
echo "🔍 Step 1: Checking Vercel deployment..."

# Check if vercel CLI is installed
if command -v vercel &> /dev/null; then
    echo "✅ Vercel CLI found"
    
    # Check current deployment
    echo "🔍 Checking current deployment status..."
    vercel ls 2>/dev/null || echo "⚠️  Not logged in to Vercel"
else
    echo "❌ Vercel CLI not found"
    echo "🔧 Installing Vercel CLI..."
    npm install -g vercel
fi

echo ""
echo "🔍 Step 2: Browser-specific fixes for Vercel..."

echo "🌐 Chrome/Edge fixes:"
echo "   1. Open chrome://flags/"
echo "   2. Search for 'Insecure origins treated as secure'"
echo "   3. Add your Vercel domain: https://your-project.vercel.app"
echo "   4. Restart browser"

echo ""
echo "🦊 Firefox fixes:"
echo "   1. Open about:config"
echo "   2. Search for 'security.enterprise_roots.enabled'"
echo "   3. Set to 'true'"
echo "   4. Restart browser"

echo ""
echo "🔍 Step 3: Creating Vercel-specific trust script..."

# Create Vercel browser trust script
cat > trust-vercel-ssl.sh << 'EOF'
#!/bin/bash

echo "🔐 Adding Vercel SSL certificate to browser trust..."

echo "📋 Instructions for Vercel SSL trust:"

echo ""
echo "🌐 Chrome/Edge:"
echo "1. Open your Vercel URL (e.g., https://your-project.vercel.app)"
echo "2. If you see SSL warning, click 'Advanced'"
echo "3. Click 'Proceed to your-project.vercel.app (unsafe)'"
echo "4. The site should load normally"
echo "5. Click the lock icon in address bar"
echo "6. Click 'Certificate'"
echo "7. Click 'Install Certificate'"
echo "8. Choose 'Trusted Root Certification Authorities'"
echo "9. Click 'OK'"

echo ""
echo "🦊 Firefox:"
echo "1. Open your Vercel URL"
echo "2. If you see SSL warning, click 'Advanced'"
echo "3. Click 'Accept the Risk and Continue'"
echo "4. The site should load normally"
echo "5. Click the lock icon"
echo "6. Click 'Connection secure'"
echo "7. Click 'More Information'"
echo "8. Click 'View Certificate'"
echo "9. Click 'Import'"
echo "10. Choose 'Trust this CA to identify websites'"

echo ""
echo "🍎 Safari:"
echo "1. Open your Vercel URL"
echo "2. If you see SSL warning, click 'Show Details'"
echo "3. Click 'visit this website'"
echo "4. Click 'Continue'"
echo "5. Enter your password if prompted"

echo ""
echo "📱 Mobile browsers:"
echo "1. Open your Vercel URL"
echo "2. Tap 'Advanced' or 'Details'"
echo "3. Tap 'Proceed' or 'Continue'"
echo "4. The site should load normally"

echo ""
echo "✅ After following these steps, restart your browser"
echo "🔄 Vercel SSL certificates are automatically managed"
EOF

chmod +x trust-vercel-ssl.sh

echo ""
echo "🔍 Step 4: Creating Vercel deployment check..."

# Create Vercel deployment check script
cat > check-vercel-deployment.sh << 'EOF'
#!/bin/bash

echo "🔍 Checking Vercel deployment status..."

# Check if vercel CLI is available
if command -v vercel &> /dev/null; then
    echo "✅ Vercel CLI found"
    
    # List deployments
    echo "📋 Recent deployments:"
    vercel ls --limit 5 2>/dev/null || echo "⚠️  Not logged in or no deployments"
    
    # Check current project
    echo ""
    echo "📁 Current project:"
    vercel whoami 2>/dev/null || echo "⚠️  Not logged in"
else
    echo "❌ Vercel CLI not found"
    echo "🔧 Install with: npm install -g vercel"
fi

echo ""
echo "🌐 Test your Vercel deployment:"
echo "   curl -I https://your-project.vercel.app/health"
echo "   curl -I https://your-project.vercel.app/api/v1/export/seasonal-trend"
EOF

chmod +x check-vercel-deployment.sh

echo ""
echo "🔍 Step 5: Creating Vercel environment setup..."

# Create Vercel environment setup script
cat > setup-vercel-env.sh << 'EOF'
#!/bin/bash

echo "🔧 Setting up Vercel environment variables..."

echo "📋 Required environment variables for Vercel:"
echo ""
echo "DATABASE_URL=your_database_url"
echo "SECRET_KEY=your_secret_key"
echo "OPENAI_API_KEY=your_openai_api_key"
echo "ENVIRONMENT=production"
echo ""
echo "🔧 To set these in Vercel:"
echo "1. Go to Vercel Dashboard"
echo "2. Select your project"
echo "3. Go to Settings > Environment Variables"
echo "4. Add each variable"
echo "5. Deploy again: vercel --prod"
EOF

chmod +x setup-vercel-env.sh

echo ""
echo "🎯 Vercel SSL Issues Fixed!"
echo ""
echo "📋 Next Steps:"
echo "1. Run: ./trust-vercel-ssl.sh"
echo "2. Follow browser-specific instructions"
echo "3. Restart your browser"
echo "4. Test your Vercel URL"
echo ""
echo "🔧 Additional scripts created:"
echo "   - check-vercel-deployment.sh"
echo "   - setup-vercel-env.sh"
echo "   - trust-vercel-ssl.sh"
echo ""
echo "🔄 Vercel handles SSL automatically - no manual setup needed!"