# 🚀 Vercel Deployment Guide

## 📋 **Overview**
This guide shows you how to deploy your FastAPI service on Vercel with automatic SSL handling.

## 🎯 **Why NO SSL for Vercel?**

✅ **Vercel handles SSL automatically** - Free SSL certificates  
✅ **Better performance** - Edge network optimization  
✅ **Simpler deployment** - No manual SSL setup  
✅ **Global CDN** - Automatic content delivery  

## 🚀 **Quick Start**

### **1. Start Service for Vercel**
```bash

```

### **2. Test Locally**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/export/seasonal-trend
```

## 📁 **Vercel Configuration**

### **vercel.json** (Already exists in your project)
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
  ]
}
```

### **requirements.txt** (Already exists)
Your existing requirements.txt is perfect for Vercel.

## 🔧 **Deployment Steps**

### **1. Install Vercel CLI**
```bash
npm install -g vercel
```

### **2. Login to Vercel**
```bash
vercel login
```

### **3. Deploy**
```bash
vercel
```

### **4. For Production**
```bash
vercel --prod
```

## 🌐 **Service URLs After Deployment**

Once deployed, your service will be available at:
- **API Endpoint**: `https://your-project.vercel.app/api/v1/export/seasonal-trend`
- **Documentation**: `https://your-project.vercel.app/docs`
- **Health Check**: `https://your-project.vercel.app/health`

## 📊 **Vercel vs Self-Hosted SSL**

| Feature | Vercel | Self-Hosted SSL |
|---------|--------|-----------------|
| SSL Setup | ✅ Automatic | ❌ Manual |
| Certificate Renewal | ✅ Automatic | ❌ Manual |
| CDN | ✅ Global | ❌ None |
| Performance | ✅ Optimized | ⚠️ Standard |
| Cost | ✅ Free tier | ❌ Server costs |
| Maintenance | ✅ Zero | ❌ High |

## 🛠 **Local Development**

### **For Vercel Development:**
```bash
./start-vercel.sh
```

### **For Production Testing:**
```bash
./start-production-no-ssl.sh
```

## 📝 **Environment Variables**

Set these in Vercel dashboard:
```bash
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
# Add other environment variables as needed
```

## 🔍 **Monitoring**

### **Vercel Dashboard:**
- Function logs
- Performance metrics
- Error tracking

### **Local Logs:**
```bash
tail -f logs/uvicorn-vercel.log
```

## 🎯 **Best Practices**

1. **Use `start-vercel.sh`** for Vercel deployment
2. **Set environment variables** in Vercel dashboard
3. **Test locally first** with `./start-vercel.sh`
4. **Monitor logs** in Vercel dashboard
5. **Use Vercel's edge functions** for better performance

## 🚨 **Troubleshooting**

### **Port Issues:**
```bash
./kill-ports.sh
./start-vercel.sh
```

### **Service Not Starting:**
```bash
tail -f logs/uvicorn-vercel.log
```

### **Vercel Deployment Issues:**
```bash
vercel logs
```

## 📞 **Support**

- **Vercel Docs**: https://vercel.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Local Issues**: Check `logs/uvicorn-vercel.log`