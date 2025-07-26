#!/bin/bash

# GitHub Setup Script for VPS
# This script helps you connect your VPS to GitHub

set -e

echo "🔧 GitHub Setup for VPS"
echo "======================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run this script as root. Use a regular user with sudo privileges."
    exit 1
fi

echo "📋 This script will help you set up GitHub authentication on your VPS."
echo "You have several options for connecting to GitHub:"
echo ""
echo "1. Personal Access Token (Recommended for automation)"
echo "2. SSH Keys (Recommended for development)"
echo "3. GitHub CLI (Interactive authentication)"
echo ""

read -p "Which method would you like to use? (1/2/3): " auth_method

case $auth_method in
    1)
        echo ""
        echo "🔑 Setting up Personal Access Token authentication..."
        echo ""
        echo "To create a Personal Access Token:"
        echo "1. Go to GitHub.com → Settings → Developer settings → Personal access tokens"
        echo "2. Click 'Generate new token (classic)'"
        echo "3. Give it a name like 'VPS Deployment'"
        echo "4. Select scopes: repo, workflow (if using GitHub Actions)"
        echo "5. Copy the generated token"
        echo ""
        read -p "Enter your GitHub username: " github_username
        read -s -p "Enter your Personal Access Token: " github_token
        echo ""
        
        # Configure Git to use token
        git config --global credential.helper store
        echo "https://$github_username:$github_token@github.com" > ~/.git-credentials
        chmod 600 ~/.git-credentials
        
        # Test the connection
        echo "Testing GitHub connection..."
        if curl -H "Authorization: token $github_token" https://api.github.com/user | grep -q "login"; then
            echo "✅ GitHub authentication successful!"
        else
            echo "❌ GitHub authentication failed. Please check your token."
            exit 1
        fi
        
        # Create a script to update the repository
        cat > ~/update-repo.sh << EOF
#!/bin/bash
cd /opt/hackathon-service
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart hackathon-service
echo "Repository updated successfully!"
EOF
        chmod +x ~/update-repo.sh
        echo "✅ Created update script: ~/update-repo.sh"
        ;;
        
    2)
        echo ""
        echo "🔑 Setting up SSH Key authentication..."
        echo ""
        
        # Check if SSH key exists
        if [ ! -f ~/.ssh/id_rsa ]; then
            echo "No SSH key found. Generating one..."
            ssh-keygen -t rsa -b 4096 -C "$(whoami)@$(hostname)"
        fi
        
        # Display the public key
        echo ""
        echo "📋 Your SSH public key:"
        echo "================================"
        cat ~/.ssh/id_rsa.pub
        echo "================================"
        echo ""
        echo "To add this key to GitHub:"
        echo "1. Go to GitHub.com → Settings → SSH and GPG keys"
        echo "2. Click 'New SSH key'"
        echo "3. Give it a title like 'VPS $(hostname)'"
        echo "4. Paste the key above"
        echo "5. Click 'Add SSH key'"
        echo ""
        read -p "Press Enter after you've added the key to GitHub..."
        
        # Test SSH connection
        echo "Testing SSH connection to GitHub..."
        if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
            echo "✅ SSH authentication successful!"
        else
            echo "❌ SSH authentication failed. Please check your key setup."
            exit 1
        fi
        
        # Create a script to update the repository
        cat > ~/update-repo.sh << 'EOF'
#!/bin/bash
cd /opt/hackathon-service
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart hackathon-service
echo "Repository updated successfully!"
EOF
        chmod +x ~/update-repo.sh
        echo "✅ Created update script: ~/update-repo.sh"
        ;;
        
    3)
        echo ""
        echo "🔑 Setting up GitHub CLI authentication..."
        echo ""
        
        # Install GitHub CLI
        echo "Installing GitHub CLI..."
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
        sudo apt update
        sudo apt install gh
        
        # Authenticate with GitHub CLI
        echo "Authenticating with GitHub CLI..."
        gh auth login
        
        # Test the connection
        echo "Testing GitHub connection..."
        if gh auth status; then
            echo "✅ GitHub CLI authentication successful!"
        else
            echo "❌ GitHub CLI authentication failed."
            exit 1
        fi
        
        # Create a script to update the repository
        cat > ~/update-repo.sh << 'EOF'
#!/bin/bash
cd /opt/hackathon-service
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart hackathon-service
echo "Repository updated successfully!"
EOF
        chmod +x ~/update-repo.sh
        echo "✅ Created update script: ~/update-repo.sh"
        ;;
        
    *)
        echo "❌ Invalid option. Please run the script again and choose 1, 2, or 3."
        exit 1
        ;;
esac

# Configure Git user
echo ""
echo "🔧 Configuring Git user..."
read -p "Enter your GitHub username: " git_username
read -p "Enter your GitHub email: " git_email

git config --global user.name "$git_username"
git config --global user.email "$git_email"

echo "✅ Git configured with:"
echo "   Username: $git_username"
echo "   Email: $git_email"

# Create deployment script
echo ""
echo "📝 Creating deployment script..."
cat > ~/deploy-from-github.sh << 'EOF'
#!/bin/bash

# GitHub deployment script
GITHUB_REPO="your-github-username/hackathon-service"
GITHUB_BRANCH="main"

echo "🚀 Deploying from GitHub..."

# Create application directory
sudo mkdir -p /opt/hackathon-service
sudo chown $USER:$USER /opt/hackathon-service
cd /opt/hackathon-service

# Clone or pull repository
if [ -d ".git" ]; then
    echo "Repository exists, pulling latest changes..."
    git pull origin $GITHUB_BRANCH
else
    echo "Cloning repository..."
    git clone https://github.com/$GITHUB_REPO.git .
    git checkout $GITHUB_BRANCH
fi

# Set up virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Set up database (if not exists)
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create .env file if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# API Configuration
PROJECT_NAME=Hackathon Service API
VERSION=1.0.0
DESCRIPTION=A FastAPI service for hackathon management
API_V1_STR=/api/v1

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# CORS Configuration
ALLOWED_HOSTS=["*"]

# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# PostgreSQL Database Configuration
POSTGRES_DB=hackathondb
POSTGRES_USER=maverick
POSTGRES_PASSWORD=maverick1946
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://maverick:maverick1946@localhost:5432/hackathondb

# Security Configuration
SECRET_KEY=$(openssl rand -hex 32)
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Logging Configuration
LOG_LEVEL=INFO

# Production settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=1
CACHE_TTL=300
CACHE_MAX_SIZE=1000
MAX_QUERY_LIMIT=10000
QUERY_TIMEOUT=30
EOL
fi

# Run migrations
alembic upgrade head

# Create systemd service
sudo tee /etc/systemd/system/hackathon-service.service > /dev/null << EOL
[Unit]
Description=Hackathon Service API
After=network.target postgresql.service

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=/opt/hackathon-service
Environment=PATH=/opt/hackathon-service/venv/bin
ExecStart=/opt/hackathon-service/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Start service
sudo systemctl daemon-reload
sudo systemctl enable hackathon-service
sudo systemctl restart hackathon-service

echo "✅ Deployment completed!"
echo "🌐 Your service is available at: http://101.50.2.59"
EOF

chmod +x ~/deploy-from-github.sh

echo ""
echo "✅ GitHub setup completed successfully!"
echo ""
echo "📋 Available scripts:"
echo "   - ~/deploy-from-github.sh  (Full deployment from GitHub)"
echo "   - ~/update-repo.sh         (Update existing deployment)"
echo ""
echo "🔧 Next steps:"
echo "   1. Update the GITHUB_REPO variable in deploy-from-github.sh"
echo "   2. Run: ./deploy-from-github.sh"
echo "   3. Update your .env file with actual API keys"
echo ""
echo "💡 Tips:"
echo "   - Use update-repo.sh for quick updates"
echo "   - Set up GitHub Actions for automated deployment"
echo "   - Use webhooks for automatic deployment on push" 