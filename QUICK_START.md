# Quick Start Guide - Deploy to VPS (101.50.2.59)

## 🚀 Fast Deployment (5 minutes)

### Step 1: Connect to your VPS
```bash
ssh root@101.50.2.59
# or
ssh your-username@101.50.2.59
```

### Step 2: Upload your files
From your local machine:
```bash
# Option A: Using SCP
scp -r /Users/66371/Documents/BNI/Hackathon\ BI/hackathon-service root@101.50.2.59:/root/

# Option B: Using rsync (recommended)
rsync -avz --exclude='venv' --exclude='__pycache__' /Users/66371/Documents/BNI/Hackathon\ BI/hackathon-service/ root@101.50.2.59:/root/hackathon-service/
```

### Step 3: Run the setup and deployment
On your VPS:
```bash
cd /root/hackathon-service
chmod +x setup.sh deploy.sh

# Run setup (this will configure the system)
./setup.sh

# Run deployment (this will deploy your application)
./deploy.sh
```

### Step 4: Verify deployment
```bash
# Check if service is running
sudo systemctl status hackathon-service

# Test the API
curl http://101.50.2.59/api/v1/

# Check the documentation
curl http://101.50.2.59/docs
```

## 🎯 Your service is now live at:
- **Main API**: http://101.50.2.59
- **API Docs**: http://101.50.2.59/docs
- **ReDoc**: http://101.50.2.59/redoc

## 🔧 Important Next Steps:

1. **Update your OpenAI API key**:
   ```bash
   sudo nano /opt/hackathon-service/.env
   # Change: OPENAI_API_KEY=your-actual-openai-api-key-here
   sudo systemctl restart hackathon-service
   ```

2. **Set up SSL (recommended)**:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

3. **Monitor your service**:
   ```bash
   # View logs
   sudo journalctl -u hackathon-service -f
   
   # Check system resources
   htop
   ```

## 🆘 Troubleshooting

If something goes wrong:

```bash
# Check service status
sudo systemctl status hackathon-service

# View logs
sudo journalctl -u hackathon-service -n 50

# Restart service
sudo systemctl restart hackathon-service

# Check if port is in use
sudo netstat -tlnp | grep :8000
```

## 📞 Support

- Check logs: `sudo journalctl -u hackathon-service -f`
- View detailed deployment guide: `README_DEPLOYMENT.md`
- Monitor system: `htop`, `df -h`, `free -h`

---

**That's it! Your Hackathon Service is now deployed and running on your VPS.** 