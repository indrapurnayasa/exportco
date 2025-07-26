# Quick Deployment Script

This script automates the entire deployment process from GitHub clone to live service.

## 🚀 One-Command Deployment

### Step 1: Upload Scripts to VPS

```bash
# From your local machine, upload the deployment scripts
scp setup.sh deploy-github.sh github-setup.sh root@101.50.2.59:/root/
```

### Step 2: Run Complete Deployment

```bash
# SSH to your VPS
ssh root@101.50.2.59

# Make scripts executable
chmod +x setup.sh deploy-github.sh github-setup.sh

# Run the complete deployment
./deploy-github.sh
```

## 🔧 Manual Step-by-Step (If you prefer to understand each step)

### Step 1: Prepare GitHub Repository

```bash
# On your local machine
cd /Users/66371/Documents/BNI/Hackathon\ BI/hackathon-service

# Initialize and push to GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/hackathon-service.git
git branch -M main
git push -u origin main
```

### Step 2: Connect to VPS and Set Up

```bash
# SSH to VPS
ssh root@101.50.2.59

# Create deployment user
adduser hackathon
usermod -aG sudo hackathon
su - hackathon
```

### Step 3: Set Up GitHub Authentication

```bash
# Method 1: Personal Access Token (Recommended)
# 1. Go to GitHub.com → Settings → Developer settings → Personal access tokens
# 2. Generate new token with 'repo' scope
# 3. Copy the token

# On VPS:
./github-setup.sh
# Choose option 1 and enter your username + token
```

### Step 4: Deploy Application

```bash
# Update repository name in script
nano deploy-github.sh
# Change: GITHUB_REPO="your-github-username/hackathon-service"

# Run deployment
./deploy-github.sh
```

### Step 5: Verify Deployment

```bash
# Check service status
sudo systemctl status hackathon-service

# Test the API
curl http://101.50.2.59/api/v1/

# View logs
sudo journalctl -u hackathon-service -f
```

## 🎯 Your Service is Live!

- **Main API**: http://101.50.2.59
- **API Docs**: http://101.50.2.59/docs
- **ReDoc**: http://101.50.2.59/redoc

## 🔄 Future Updates

```bash
# Make changes locally and push to GitHub
git add .
git commit -m "Update"
git push origin main

# On VPS, update the application
cd /opt/hackathon-service
./update.sh
```

## 🆘 Quick Troubleshooting

```bash
# Check service status
sudo systemctl status hackathon-service

# View logs
sudo journalctl -u hackathon-service -f

# Restart service
sudo systemctl restart hackathon-service

# Check if port is in use
sudo netstat -tlnp | grep :8000
```

---

**That's it! Your Hackathon Service is deployed and running! 🚀** 