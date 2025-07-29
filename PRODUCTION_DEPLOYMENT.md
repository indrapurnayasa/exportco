# 🚀 Production Deployment Guide

Simple guide to deploy your Hackathon Service with HTTPS in production.

## 📋 Prerequisites

- VPS/Server with Ubuntu/Debian
- Python 3.10+ installed
- PostgreSQL installed and running
- Domain name (optional, for proper SSL)

## 🔧 Quick Setup (5 minutes)

### Step 1: Upload Files to VPS
```bash
# On your local machine
scp -r . user@your-vps-ip:/opt/hackathon-service/
```

### Step 2: Setup Production HTTPS
```bash
# On your VPS
cd /opt/hackathon-service
chmod +x setup-production-https.sh
./setup-production-https.sh
```

### Step 3: Start Production Service
```bash
# Start the service
./start-production.sh

# Check status
./status-production.sh
```

## 🌐 Your Production Endpoints

After setup, your service will be available at:

- **Health Check**: `https://your-server-ip:8443/health`
- **API Docs**: `https://your-server-ip:8443/docs`
- **Seasonal Trend**: `https://your-server-ip:8443/api/v1/export/seasonal-trend`
- **Country Demand**: `https://your-server-ip:8443/api/v1/export/country-demand`

## 🔧 Service Management

### Manual Control
```bash
# Start service
./start-production.sh

# Stop service
./stop-production.sh

# Check status
./status-production.sh

# Restart service
./stop-production.sh && ./start-production.sh
```

### Systemd Control (Auto-start on boot)
```bash
# Start service
sudo systemctl start hackathon-service

# Stop service
sudo systemctl stop hackathon-service

# Check status
sudo systemctl status hackathon-service

# Restart service
sudo systemctl restart hackathon-service

# Enable auto-start
sudo systemctl enable hackathon-service
```

## 🔍 Monitoring & Logs

```bash
# View real-time logs
tail -f logs/uvicorn-https.log

# View HTTP logs
tail -f logs/uvicorn-http.log

# Check service status
./status-production.sh
```

## 🧪 Testing Your Setup

```bash
# Test HTTP (internal)
curl http://127.0.0.1:8000/health

# Test HTTPS (external)
curl -k https://your-server-ip:8443/health

# Test API endpoint
curl -k https://your-server-ip:8443/api/v1/export/seasonal-trend
```

## 🎯 Frontend Configuration

Update your frontend to use the HTTPS endpoint:

```javascript
// Change from HTTP to HTTPS
fetch('https://your-server-ip:8443/api/v1/export/seasonal-trend?endDate=31-12-2024')
```

## 🔐 SSL Certificate

This setup uses a self-signed certificate. To accept it:

1. Visit `https://your-server-ip:8443/health` in your browser
2. Click "Advanced" → "Proceed to site"
3. The certificate is now trusted for that browser

## 🛠️ Troubleshooting

### Service Won't Start
```bash
# Check logs
tail -f logs/uvicorn-https.log

# Check if port is in use
sudo netstat -tlnp | grep :8443

# Check database connection
psql -h localhost -U maverick -d hackathondb -c "SELECT 1;"
```

### SSL Certificate Issues
```bash
# Regenerate certificates
rm -rf ssl/
./setup-production-https.sh
```

### Firewall Issues
```bash
# Check firewall status
sudo ufw status

# Allow ports
sudo ufw allow 8443
sudo ufw allow 8000
```

## 📊 Performance Monitoring

```bash
# Check memory usage
ps aux | grep uvicorn

# Check disk space
df -h

# Check system resources
htop
```

## 🔄 Updates & Maintenance

### Update Application
```bash
# Stop service
./stop-production.sh

# Update code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start service
./start-production.sh
```

### Certificate Renewal
```bash
# Certificates are valid for 365 days
# To renew early:
rm -rf ssl/
./setup-production-https.sh
```

## 🚨 Security Checklist

- [ ] Firewall configured (UFW)
- [ ] SSL certificates installed
- [ ] Service running on HTTPS
- [ ] Database backups configured
- [ ] Log monitoring in place
- [ ] Regular security updates

## 📞 Support

If you encounter issues:

1. Check service logs: `tail -f logs/uvicorn-https.log`
2. Check service status: `./status-production.sh`
3. Verify database connection
4. Test endpoints manually
5. Check firewall rules: `sudo ufw status`

## 🎉 Success Indicators

Your production setup is working when:

- ✅ `./status-production.sh` shows both services running
- ✅ `curl -k https://your-server-ip:8443/health` returns `{"status": "healthy"}`
- ✅ Your frontend can fetch data from the HTTPS endpoint
- ✅ No SSL certificate errors in browser console

---

**That's it!** Your Hackathon Service is now running in production with HTTPS support. 🚀