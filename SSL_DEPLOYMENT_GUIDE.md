# 🔐 SSL Certificate Implementation Guide

## Prerequisites

### **1. Domain Requirements**
- ✅ Domain purchased and active
- ✅ DNS A record pointing to your server IP
- ✅ Port 80 and 443 open in firewall
- ✅ Domain accessible from internet

### **2. Server Requirements**
- ✅ Ubuntu/Debian server
- ✅ Root access
- ✅ Internet connectivity
- ✅ Port 80 and 443 available

## 🚀 Quick Setup

### **Step 1: Run SSL Setup Script**
```bash
# Make script executable
chmod +x setup-lets-encrypt.sh

# Run the setup script
sudo ./setup-lets-encrypt.sh
```

**What the script does:**
- Installs dependencies (nginx, certbot)
- Generates Let's Encrypt SSL certificate
- Configures Nginx as reverse proxy
- Sets up auto-renewal
- Creates production scripts

### **Step 2: Start Production Service**
```bash
# Start the service with SSL
./start-production-ssl.sh
```

### **Step 3: Test Your API**
```bash
# Test health endpoint
curl https://yourdomain.com/health

# Test API endpoint
curl https://yourdomain.com/api/v1/export/seasonal-trend
```

## 📋 Manual Setup (Alternative)

If you prefer manual setup, follow these steps:

### **1. Install Dependencies**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git nginx certbot python3-certbot-nginx snapd
sudo snap install --classic certbot
sudo ln -sf /snap/bin/certbot /usr/bin/certbot
```

### **2. Generate SSL Certificate**
```bash
# Stop services using port 80
sudo systemctl stop nginx

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

### **3. Configure Nginx**
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/yourdomain.com
```

**Configuration content:**
```nginx
# HTTP redirect to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # API Backend (FastAPI)
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeout settings for Vercel compatibility
        proxy_connect_timeout 10s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # OpenAPI JSON
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Root redirect to API docs
    location / {
        return 301 https://$server_name/docs;
    }
}
```

### **4. Enable Site and Start Services**
```bash
# Enable site
sudo ln -sf /etc/nginx/sites-available/yourdomain.com /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Start services
sudo systemctl start nginx
sudo systemctl enable nginx
```

### **5. Configure Firewall**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22
sudo ufw --force enable
```

### **6. Setup Auto-Renewal**
```bash
# Create renewal script
sudo nano /usr/local/bin/renew-ssl.sh
```

**Script content:**
```bash
#!/bin/bash
/usr/bin/certbot renew --quiet
if [ $? -eq 0 ]; then
    systemctl reload nginx
    echo "$(date): SSL certificate renewed successfully" >> /var/log/ssl-renewal.log
else
    echo "$(date): SSL certificate renewal failed" >> /var/log/ssl-renewal.log
fi
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/renew-ssl.sh

# Add to crontab
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/renew-ssl.sh >> /var/log/ssl-renewal.log 2>&1
```

## 🔧 Frontend Integration

### **1. Update Frontend Code**
Use the optimized frontend code from `vercel-frontend-ssl.js`:

```javascript
const API_BASE_URL = 'https://yourdomain.com';

async function getSeasonalTrend(endDate = null) {
    const response = await fetch(`${API_BASE_URL}/api/v1/export/seasonal-trend?endDate=${endDate}`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
        },
        signal: AbortSignal.timeout(8000)
    });
    
    if (response.ok) {
        return await response.json();
    } else {
        throw new Error(`API Error: ${response.status}`);
    }
}
```

### **2. Vercel Environment Variables**
Add to your Vercel project settings:
```
API_BASE_URL=https://yourdomain.com
API_TIMEOUT=8000
NODE_TLS_REJECT_UNAUTHORIZED=0
```

## 📊 Testing and Monitoring

### **1. Test SSL Certificate**
```bash
# Test with openssl
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Test with curl
curl -I https://yourdomain.com/health
```

### **2. Check Certificate Status**
```bash
# List certificates
sudo certbot certificates

# Test renewal (dry run)
sudo certbot renew --dry-run
```

### **3. Monitor Services**
```bash
# Check service status
./status-production-ssl.sh

# Check logs
tail -f logs/uvicorn-ssl.log
tail -f /var/log/nginx/error.log
```

## 🚨 Troubleshooting

### **Common Issues:**

#### **1. Certificate Generation Failed**
```bash
# Check if port 80 is free
sudo netstat -tulpn | grep :80

# Check DNS resolution
nslookup yourdomain.com

# Check firewall
sudo ufw status
```

#### **2. Nginx Configuration Error**
```bash
# Test configuration
sudo nginx -t

# Check syntax
sudo nginx -T | grep -A 10 -B 10 "error"
```

#### **3. API Not Accessible**
```bash
# Check if FastAPI is running
ps aux | grep uvicorn

# Check port 8000
sudo netstat -tulpn | grep :8000

# Test local API
curl http://127.0.0.1:8000/health
```

#### **4. SSL Certificate Expired**
```bash
# Manual renewal
sudo certbot renew

# Check renewal logs
tail -f /var/log/ssl-renewal.log
```

## 📈 Performance Optimization

### **1. Nginx Optimization**
```nginx
# Add to nginx.conf
worker_processes auto;
worker_connections 1024;
keepalive_timeout 65;
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

### **2. FastAPI Optimization**
```bash
# Start with multiple workers
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
```

### **3. Database Optimization**
```sql
-- Add indexes for better performance
CREATE INDEX idx_export_data_seasonal_trend 
ON export_data (tahun, comodity_code, bulan, netweight);
```

## 🔒 Security Best Practices

### **1. SSL Configuration**
- ✅ TLS 1.2 and 1.3 only
- ✅ Strong cipher suites
- ✅ HSTS headers
- ✅ Security headers

### **2. Firewall Configuration**
- ✅ Only necessary ports open
- ✅ Rate limiting
- ✅ DDoS protection

### **3. Monitoring**
- ✅ Certificate expiration monitoring
- ✅ Service health checks
- ✅ Error log monitoring

## 📝 Maintenance

### **1. Regular Tasks**
- ✅ Monitor certificate expiration
- ✅ Check service logs
- ✅ Update system packages
- ✅ Backup configuration

### **2. Log Locations**
- ✅ Nginx logs: `/var/log/nginx/`
- ✅ SSL renewal: `/var/log/ssl-renewal.log`
- ✅ Application logs: `logs/uvicorn-ssl.log`

### **3. Backup Strategy**
```bash
# Backup SSL certificates
sudo cp -r /etc/letsencrypt/live/yourdomain.com /backup/

# Backup Nginx configuration
sudo cp /etc/nginx/sites-available/yourdomain.com /backup/
```

## 🎯 Success Checklist

- ✅ SSL certificate generated and valid
- ✅ Nginx configured and running
- ✅ FastAPI service running on port 8000
- ✅ Firewall configured
- ✅ Auto-renewal setup
- ✅ Frontend updated with new URLs
- ✅ API endpoints accessible via HTTPS
- ✅ Certificate auto-renewal working
- ✅ Monitoring and logging configured

## 🚀 Next Steps

1. **Test all API endpoints** with HTTPS
2. **Update frontend** to use HTTPS URLs
3. **Monitor performance** and logs
4. **Set up monitoring** for certificate expiration
5. **Configure backups** for SSL certificates
6. **Document the setup** for team members

Your production service is now secure with valid SSL certificates! 🎉