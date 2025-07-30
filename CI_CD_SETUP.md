# CI/CD Setup Guide for VPS Deployment

## 🚀 **Overview**

This CI/CD pipeline automatically deploys your FastAPI application to your VPS when you push code to the main branch. It handles:

- ✅ **Automatic code pull** from GitHub
- ✅ **Port management** (kills conflicting processes)
- ✅ **SSL certificate validation** and renewal
- ✅ **Nginx configuration** updates
- ✅ **FastAPI service** restart
- ✅ **Health checks** and testing

## 🔧 **Setup Steps**

### **1. Generate SSH Key for VPS**

```bash
# On your local machine, generate SSH key
ssh-keygen -t rsa -b 4096 -C "indrapurnayasaa@gmail.com"

# Copy public key to VPS
ssh-copy-id username@your-vps-ip

# Or manually add to VPS
cat ~/.ssh/id_rsa.pub
# Then add to ~/.ssh/authorized_keys on VPS
```

### **2. Add GitHub Secrets**

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `VPS_HOST` | `101.50.2.59` | Your VPS IP address |
| `VPS_USERNAME` | `root` | SSH username |
| `VPS_SSH_KEY` | `-----BEGIN OPENSSH PRIVATE KEY-----...` | Your private SSH key |
| `VPS_PORT` | `22` | SSH port (usually 22) |

### **3. Test Deployment**

```bash
# On your VPS, test the deployment script
cd ~/exportco
./deploy.sh
```

### **4. Manual Deployment Commands**

```bash
# Kill ports and restart
./kill-ports.sh
./start-production-ssl.sh

# Check status
./status-production-ssl.sh

# Test service
curl -I https://dev-ngurah.fun/api/v1/export/seasonal-trend
```

## 🔄 **How It Works**

### **GitHub Actions Workflow**

1. **Trigger**: Push to main/master branch
2. **SSH Connection**: Connects to VPS using secrets
3. **Deployment Script**: Runs comprehensive deployment
4. **Health Checks**: Verifies service is working

### **Deployment Process**

1. **Port Management**: Kills any conflicting processes
2. **Code Update**: Pulls latest code from GitHub
3. **Environment**: Activates conda environment
4. **Dependencies**: Installs/updates Python packages
5. **SSL Certificate**: Validates and renews if needed
6. **Nginx Config**: Updates reverse proxy configuration
7. **Service Start**: Starts FastAPI with SSL
8. **Health Check**: Tests API endpoints

## 🛠 **Troubleshooting**

### **Common Issues**

1. **SSH Connection Failed**
   ```bash
   # Test SSH connection
   ssh username@your-vps-ip
   ```

2. **Port Already in Use**
   ```bash
   # Manual port kill
   sudo lsof -ti:80 | xargs sudo kill -9
   sudo lsof -ti:443 | xargs sudo kill -9
   sudo lsof -ti:8000 | xargs sudo kill -9
   ```

3. **SSL Certificate Issues**
   ```bash
   # Regenerate certificate
   sudo certbot certonly --standalone -d dev-ngurah.fun
   ```

4. **Nginx Configuration Error**
   ```bash
   # Test nginx config
   sudo nginx -t
   ```

### **Manual Deployment**

If GitHub Actions fails, run manually:

```bash
# On VPS
cd ~/exportco
./deploy.sh
```

## 📊 **Monitoring**

### **Check Service Status**

```bash
./status-production-ssl.sh
```

### **View Logs**

```bash
# FastAPI logs
tail -f logs/uvicorn-ssl.log

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### **Test Endpoints**

```bash
# Health check
curl https://dev-ngurah.fun/health

# API endpoint
curl https://dev-ngurah.fun/api/v1/export/seasonal-trend

# Documentation
curl https://dev-ngurah.fun/docs
```

## 🔒 **Security Notes**

- ✅ **SSH key authentication** (no passwords)
- ✅ **SSL certificate validation**
- ✅ **Automatic certificate renewal**
- ✅ **Secure nginx configuration**
- ✅ **CORS properly configured**

## 🎯 **Expected Results**

After successful deployment:

- ✅ **GitHub Actions**: Green checkmark
- ✅ **VPS Service**: Running on HTTPS
- ✅ **SSL Certificate**: Valid and trusted
- ✅ **API Endpoints**: Accessible and working
- ✅ **Health Checks**: All passing

## 📝 **Customization**

### **Change Domain**

Edit `deploy.sh` and change:
```bash
DOMAIN="your-new-domain.com"
```

### **Add Environment Variables**

Add to GitHub Secrets:
- `DATABASE_URL`
- `SECRET_KEY`
- `API_KEYS`

### **Modify Deployment Steps**

Edit `.github/workflows/deploy.yml` to add custom steps.

## 🚀 **Ready to Deploy!**

1. Push your code to GitHub
2. GitHub Actions will automatically deploy
3. Check the Actions tab for deployment status
4. Test your API at `https://dev-ngurah.fun`

**Your CI/CD pipeline is now ready for seamless deployments!**