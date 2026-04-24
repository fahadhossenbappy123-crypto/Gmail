# Render Deployment Guide

## Render-এ Deploy করার ধাপ:

### **Step 1: Render অ্যাকাউন্ট তৈরি করুন**
https://render.com এ যান এবং সাইন আপ করুন

### **Step 2: নতুন Web Service তৈরি করুন**
1. Dashboard → "New +" → "Web Service"
2. আপনার GitHub repo connect করুন
3. নিচের সেটিংস ব্যবহার করুন:

**Basic Settings:**
- **Name**: gmail-create
- **Region**: Singapore (or closest to you)
- **Branch**: main

**Build & Deploy:**
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn run:app --workers 2 --worker-class sync --timeout 30`

### **Step 3: Environment Variables সেট করুন**
Dashboard → Environment tab → "Add Environment Variable"

```
DATABASE_URL=postgresql://gmaildb_user:rXeArKM1bjE9N2fyb4vGaPiKEBK9cPcx@dpg-d7lpa3beo5us73cvns4g-a/gmaildb
FLASK_ENV=production
SECRET_KEY=your-very-secret-key-here-change-this
GOOGLE_CLIENT_SECRET=client_secret_206553593097-4fnqh23f95cmfkirbi29l1ciebg901dj.apps.googleusercontent.com.json
GOOGLE_SERVICE_ACCOUNT=rugged-nucleus-494309-h6-1e1f8ffafa43.json
```

## **Render Start Command Options:**

### **সাধারণ (Recommended):**
```bash
gunicorn run:app --workers 2 --worker-class sync --timeout 30
```

### **বেশি traffic এর জন্য:**
```bash
gunicorn run:app --workers 4 --worker-class gevent --worker-connections 1000 --timeout 60
```

### **সিম্পল (Debug মোডে):**
```bash
python run.py
```

## **Deploy করার পর:**
1. Logs চেক করুন: Dashboard → "Logs"
2. Health check করুন: `your-app.onrender.com`

## **সমস্যা হলে:**
- Logs দেখুন (Dashboard → Logs tab)
- Build failed? → `pip install -r requirements.txt` local-এ চালান
- Database connection error? → DATABASE_URL সঠিক কিনা চেক করুন

## **Free Tier সীমাবদ্ধতা:**
- ৩০ মিনিট inactivity-র পর app suspend হয়
- Production-এর জন্য Paid plan ব্যবহার করুন
