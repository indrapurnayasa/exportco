# 🚀 Vercel Project Configuration Guide

## 📁 **Current Configuration**

Your current `vercel.json` is good but can be enhanced:

```json
{
  "version": 2,
  "builds": [
    { "src": "app/main.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "app/main.py" }
  ]
}
```

## 🔧 **Enhanced Vercel Configuration**

### **1. Updated vercel.json**
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ],
  "functions": {
    "app/main.py": {
      "maxDuration": 30
    }
  },
  "env": {
    "PYTHONPATH": "."
  }
}
```

## 🌍 **Environment Variables**

### **Required Environment Variables:**

Set these in your Vercel dashboard under **Settings > Environment Variables**:

```bash
# Database Configuration
DATABASE_URL=your_postgresql_database_url
DATABASE_URL_VERCEL=your_vercel_postgresql_url

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys
OPENAI_API_KEY=your_openai_api_key

# Redis (if using)
REDIS_URL=your_redis_url

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# CORS Settings
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

### **Optional Environment Variables:**

```bash
# Email Configuration (if using email features)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# File Upload (if using file upload features)
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760

# Monitoring
SENTRY_DSN=your_sentry_dsn
```

## 🏗 **Build Configuration**

### **Build Command:**
```bash
pip install -r requirements.txt
```

### **Output Directory:**
```
.
```

### **Install Command:**
```bash
pip install -r requirements.txt
```

## 📊 **Vercel Dashboard Settings**

### **1. Project Settings:**
- **Framework Preset**: Other
- **Root Directory**: `./`
- **Build Command**: `pip install -r requirements.txt`
- **Output Directory**: `.`
- **Install Command**: `pip install -r requirements.txt`

### **2. Environment Variables:**
Go to **Settings > Environment Variables** and add:

| Variable | Value | Environment |
|----------|-------|-------------|
| `DATABASE_URL` | `your_database_url` | Production, Preview, Development |
| `SECRET_KEY` | `your_secret_key` | Production, Preview, Development |
| `OPENAI_API_KEY` | `your_openai_key` | Production, Preview, Development |
| `ENVIRONMENT` | `production` | Production |
| `ENVIRONMENT` | `preview` | Preview |
| `ENVIRONMENT` | `development` | Development |

### **3. Domains:**
- **Production**: `your-project.vercel.app`
- **Custom Domain**: `api.yourdomain.com` (optional)

## 🔐 **Security Configuration**

### **CORS Settings:**
Add to your FastAPI app:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **Rate Limiting:**
Consider adding rate limiting for production:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

## 📈 **Performance Optimization**

### **1. Function Configuration:**
```json
{
  "functions": {
    "app/main.py": {
      "maxDuration": 30,
      "memory": 1024
    }
  }
}
```

### **2. Caching Headers:**
Add to your responses:

```python
from fastapi.responses import JSONResponse

@app.get("/api/v1/export/seasonal-trend")
async def get_seasonal_trend():
    response = JSONResponse(content=your_data)
    response.headers["Cache-Control"] = "public, max-age=300"
    return response
```

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **Database Connection:**
   ```bash
   # Use Vercel Postgres or external database
   DATABASE_URL=postgresql://user:pass@host:port/db
   ```

2. **Memory Issues:**
   ```json
   {
     "functions": {
       "app/main.py": {
         "memory": 1024
       }
     }
   }
   ```

3. **Timeout Issues:**
   ```json
   {
     "functions": {
       "app/main.py": {
         "maxDuration": 60
       }
     }
   }
   ```

## 📝 **Deployment Checklist**

- [ ] Set all environment variables
- [ ] Configure database connection
- [ ] Set up CORS for frontend
- [ ] Configure rate limiting
- [ ] Set up monitoring
- [ ] Test all endpoints
- [ ] Configure custom domain (optional)

## 🔍 **Monitoring & Logs**

### **Vercel Dashboard:**
- **Functions**: View function logs
- **Analytics**: Monitor performance
- **Errors**: Track error rates

### **Local Testing:**
```bash
# Test locally first
./start-vercel.sh

# Check logs
tail -f logs/uvicorn-vercel.log
```

## 🎯 **Best Practices**

1. **Use environment variables** for all sensitive data
2. **Test locally** before deploying
3. **Monitor performance** in Vercel dashboard
4. **Set up proper CORS** for frontend integration
5. **Use caching** for better performance
6. **Implement rate limiting** for production
7. **Set up monitoring** and error tracking