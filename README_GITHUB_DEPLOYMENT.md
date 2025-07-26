# GitHub-Based Deployment Guide

This guide shows you how to deploy your Hackathon Service directly from GitHub to your VPS (101.50.2.59).

## 🎯 Benefits of GitHub-Based Deployment

- ✅ **Version Control**: Track all changes and rollback if needed
- ✅ **Collaboration**: Multiple developers can work on the same codebase
- ✅ **Automation**: Easy to set up CI/CD pipelines
- ✅ **Backup**: Your code is safely stored in the cloud
- ✅ **Easy Updates**: One command to pull latest changes

## 🔧 Prerequisites

1. **GitHub Repository**: Your code must be pushed to GitHub
2. **VPS Access**: SSH access to your VPS
3. **GitHub Authentication**: Choose one of the methods below

## 📋 Step 1: Prepare Your GitHub Repository

### 1.1 Push your code to GitHub
```bash
# On your local machine
cd /Users/66371/Documents/BNI/Hackathon\ BI/exportco

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/exportco.git
git branch -M main
git push -u origin main
```

### 1.2 Repository Structure
Make sure your repository includes:
- `requirements.txt`
- `alembic.ini` and `alembic/` directory
- `app/` directory with your FastAPI application
- `.gitignore` (to exclude sensitive files)

## 🔐 Step 2: Set Up GitHub Authentication on VPS

### Option A: Personal Access Token (Recommended)

#### 2.1 Create Personal Access Token
1. Go to GitHub.com → Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Give it a name: "VPS Deployment"
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (if using GitHub Actions)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

#### 2.2 Configure on VPS
```bash
# SSH to your VPS
ssh root@101.50.2.59

# Run the GitHub setup script
chmod +x github-setup.sh
./github-setup.sh

# Choose option 1 (Personal Access Token)
# Enter your GitHub username and the token you created
```

### Option B: SSH Keys

#### 2.1 Generate SSH Key on VPS
```bash
# SSH to your VPS
ssh root@101.50.2.59

# Generate SSH key
ssh-keygen -t rsa -b 4096 -C "vps@101.50.2.59"

# Display the public key
cat ~/.ssh/id_rsa.pub
```

#### 2.2 Add SSH Key to GitHub
1. Go to GitHub.com → Settings → SSH and GPG keys
2. Click "New SSH key"
3. Title: "VPS 101.50.2.59"
4. Paste the public key from step 2.1
5. Click "Add SSH key"

#### 2.3 Test SSH Connection
```bash
# Test the connection
ssh -T git@github.com
# You should see: "Hi username! You've successfully authenticated..."
```

### Option C: GitHub CLI

```bash
# SSH to your VPS
ssh root@101.50.2.59

# Run the GitHub setup script
chmod +x github-setup.sh
./github-setup.sh

# Choose option 3 (GitHub CLI)
# Follow the interactive prompts
```

## 🚀 Step 3: Deploy from GitHub

### 3.1 First-Time Deployment
```bash
# SSH to your VPS
ssh root@101.50.2.59

# Update the repository name in the script
nano ~/deploy-from-github.sh
# Change: GITHUB_REPO="indrapurnayasa/exportco"

# Run the deployment
./deploy-from-github.sh
```

### 3.2 Verify Deployment
```bash
# Check service status
sudo systemctl status exportco

# Test the API
curl http://101.50.2.59/api/v1/

# Check logs
sudo journalctl -u exportco -f
```

## 🔄 Step 4: Update Your Application

### 4.1 Make Changes Locally
```bash
# On your local machine
cd /Users/66371/Documents/BNI/Hackathon\ BI/exportco

# Make your changes
# ... edit files ...

# Commit and push
git add .
git commit -m "Add new feature"
git push origin main
```

### 4.2 Deploy Updates to VPS
```bash
# SSH to your VPS
ssh root@101.50.2.59

# Update the application
./update-repo.sh
```

## 🤖 Step 5: Automated Deployment (Optional)

### 5.1 GitHub Actions Workflow
Create `.github/workflows/deploy.yml` in your repository:

```yaml
name: Deploy to VPS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Deploy to VPS
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: 101.50.2.59
        username: root
        key: ${{ secrets.VPS_SSH_KEY }}
        script: |
          cd /opt/exportco
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          alembic upgrade head
          sudo systemctl restart exportco
```

### 5.2 Webhook Deployment
Set up a webhook on your VPS to automatically deploy on push:

```bash
# Install webhook handler
sudo apt install webhook

# Create webhook configuration
sudo tee /etc/webhook.conf > /dev/null << EOF
[
  {
    "id": "deploy-hackathon",
    "execute-command": "/home/root/update-repo.sh",
    "command-working-directory": "/home/root"
  }
]
EOF

# Start webhook service
sudo systemctl enable webhook
sudo systemctl start webhook
```

## 📊 Step 6: Monitoring and Maintenance

### 6.1 Check Deployment Status
```bash
# Service status
sudo systemctl status exportco

# Recent logs
sudo journalctl -u exportco -n 50

# Git status
cd /opt/exportco
git status
git log --oneline -5
```

### 6.2 Rollback to Previous Version
```bash
cd /opt/exportco

# List recent commits
git log --oneline -10

# Rollback to specific commit
git reset --hard <commit-hash>
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart exportco
```

### 6.3 Environment Variables
```bash
# Edit environment variables
sudo nano /opt/exportco/.env

# Restart service after changes
sudo systemctl restart exportco
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Authentication Failed
```bash
# Test GitHub connection
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# For SSH
ssh -T git@github.com
```

#### 2. Repository Not Found
```bash
# Check repository URL
cd /opt/exportco
git remote -v

# Update remote URL
git remote set-url origin https://github.com/YOUR_USERNAME/exportco.git
```

#### 3. Permission Denied
```bash
# Fix file permissions
sudo chown -R $USER:$USER /opt/exportco
sudo chmod -R 755 /opt/exportco
```

#### 4. Service Won't Start
```bash
# Check logs
sudo journalctl -u exportco -f

# Check dependencies
cd /opt/exportco
source venv/bin/activate
pip list
```

## 📋 Useful Commands

### Git Operations
```bash
# Check repository status
cd /opt/exportco
git status
git log --oneline -5

# Pull latest changes
git pull origin main

# Check for conflicts
git diff HEAD~1
```

### Service Management
```bash
# Restart service
sudo systemctl restart exportco

# View real-time logs
sudo journalctl -u exportco -f

# Check service configuration
sudo systemctl cat exportco
```

### Database Operations
```bash
# Run migrations
cd /opt/exportco
source venv/bin/activate
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Check migration status
alembic current
alembic history
```

## 🎯 Best Practices

1. **Always test locally** before pushing to GitHub
2. **Use meaningful commit messages** for easy rollback
3. **Keep sensitive data in environment variables** (not in Git)
4. **Set up automated testing** in GitHub Actions
5. **Monitor your application** after each deployment
6. **Keep backups** of your database and configuration
7. **Use feature branches** for major changes
8. **Document your deployment process**

## 🚀 Quick Reference

### Initial Setup
```bash
# 1. Set up GitHub authentication
./github-setup.sh

# 2. Deploy for the first time
./deploy-from-github.sh

# 3. Update repository name in script
nano ~/deploy-from-github.sh
```

### Regular Updates
```bash
# Pull and deploy updates
./update-repo.sh

# Or manually
cd /opt/exportco
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart exportco
```

### Monitoring
```bash
# Check service status
sudo systemctl status exportco

# View logs
sudo journalctl -u exportco -f

# Test API
curl http://101.50.2.59/api/v1/
```

Your service will be available at:
- **Main API**: http://101.50.2.59
- **API Documentation**: http://101.50.2.59/docs
- **ReDoc**: http://101.50.2.59/redoc 