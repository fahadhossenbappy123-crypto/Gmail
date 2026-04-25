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

⚠️ **IMPORTANT: Database URL Format**
Render থেকে যে DATABASE_URL পাবেন, তা হবে `postgresql://` দিয়ে শুরু হওয়া।
SQLAlchemy-কে লাগে `postgresql+psycopg2://` দিয়ে শুরু। 
**নিচের ফরম্যাট ব্যবহার করুন:**

```
DATABASE_URL=postgresql+psycopg2://gmaildb_user:rXeArKM1bjE9N2fyb4vGaPiKEBK9cPcx@dpg-d7lpa3beo5us73cvns4g-a:5432/gmaildb?sslmode=require
FLASK_ENV=production
SECRET_KEY=your-very-secret-key-here-minimum-32-characters-long
PORT=5000
```

**নোট:**
- Database URL-এ `:5432` port যোগ করুন
- URL-এ `?sslmode=require` রাখুন (Render এ required)
- SECRET_KEY মিনিমাম 32 ক্যারেক্টার লম্বা হতে হবে
- Config.py স্বয়ংক্রিয়ভাবে `postgresql://` কে `postgresql+psycopg2://` তে রূপান্তরিত করবে

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

---

## **Database সমস্যা সমাধান:**

### **1. DATABASE_URL কি সঠিক?**
✅ সঠিক ফরম্যাট:
```
postgresql+psycopg2://username:password@host:5432/dbname?sslmode=require
```

❌ ভুল ফরম্যাট:
```
postgresql://username:password@host/dbname
postgres://username:password@host/dbname
```

### **2. Connection Timeout Error?**
এই ফিক্স করুন config.py-তে:
```python
'connect_args': {
    'connect_timeout': 10,  # 5 থেকে 10 করুন
}
```

### **3. SSL সম্পর্কিত সমস্যা?**
নিশ্চিত করুন DATABASE_URL-এ যোগ করা আছে:
```
?sslmode=require
```

### **4. Pool সাইজ বড় হয়েছে?**
Render free tier-এ pool সাইজ কমান:
```python
'pool_size': 5,
'max_overflow': 10,
```

---

## **Deploy করার সময় এই ধাপ অনুসরণ করুন:**

### **Step 1: Local-এ Test করুন**
```bash
# Database migrate করুন
python migrate_db.py

# App চালান
python run.py
```

### **Step 2: Render-এ Deploy করুন**
1. GitHub-এ push করুন
2. Render Dashboard → Deploy

### **Step 3: Database Initialize করুন** (প্রথমবার)
1. Render Dashboard → "Shell" tab ওপেন করুন
2. এই কমান্ড চালান:
```bash
python migrate_db.py
```

### **Step 4: Logs চেক করুন**
1. Dashboard → "Logs" tab
2. এই লাইন খুঁজুন: `✓ Database tables created/verified`

---

## **🔧 এডভান্সড Troubleshooting**

### **Error: "could not connect to server"**
```
সমাধান:
1. Render Dashboard → Resources
2. PostgreSQL database running আছে কিনা চেক করুন
3. DATABASE_URL সম্পূর্ণ কিনা নিশ্চিত করুন
4. Port সংখ্যা (:5432) আছে কিনা চেক করুন
```

### **Error: "no pg_hba.conf entry"**
```
সমাধান:
1. DATABASE_URL-এ ?sslmode=require যোগ করুন
2. Server এ SSL enabled আছে নিশ্চিত করুন
```

### **Error: "server closed the connection unexpectedly"**
```
সমাধান:
1. Pool size কমান (pool_size: 5, max_overflow: 10)
2. Connection timeout বাড়ান (connect_timeout: 10)
3. Pool recycle কমান (pool_recycle: 1800)
```

### **Error: "relation does not exist"**
```
সমাধান:
1. Database tables তৈরি হয়নি
2. Render Shell এ চালান: python migrate_db.py
3. বা Logs এ "Database tables created" খুঁজুন
```

### **App Running কিন্তু Database সংযোগ নেই**
```
সমাধান:
1. Render Dashboard → Logs → check for "Database connection failed"
2. DATABASE_URL environment variable set আছে কিনা চেক করুন
3. Restart service (যেকোনো changes এর পর)
```

---

## **✅ Deployment Checklist**

- [ ] GitHub repo তৈরি করা
- [ ] `requirements.txt` updated করা
- [ ] `config.py` এ DATABASE_URL conversion logic আছে
- [ ] `migrate_db.py` script তৈরি করা
- [ ] Render account তৈরি করা
- [ ] PostgreSQL database create করা
- [ ] Environment variables সেট করা:
  - [ ] DATABASE_URL (correct format)
  - [ ] FLASK_ENV=production
  - [ ] SECRET_KEY (long random string)
  - [ ] PORT=5000
- [ ] Build command সঠিক: `pip install -r requirements.txt`
- [ ] Start command সঠিক: `gunicorn run:app ...`
- [ ] Deploy success হয়েছে কিনা চেক করা
- [ ] Database migration চালানো: `python migrate_db.py`
- [ ] App health check করা (https://your-app.onrender.com)
- [ ] Admin login test করা
- [ ] Gmail account creation test করা
- [ ] Database query করা (Dashboard → SQL)

---

## **🚀 Performance Tips**

1. **Connection Pooling**: Pool size optimize করার জন্য
   ```python
   # Free Tier
   'pool_size': 5,
   'max_overflow': 10,
   
   # Paid Tier
   'pool_size': 10,
   'max_overflow': 20,
   ```

2. **Query Optimization**: Heavy queries এ indices ব্যবহার করুন
   ```python
   # database.py এ পরে add করুন
   __table_args__ = (Index('ix_user_email', 'email'),)
   ```

3. **Cache**: Frequently accessed data cache করুন
   ```python
   from flask_caching import Cache
   cache = Cache(app, config={'CACHE_TYPE': 'simple'})
   ```

---

## **📊 Monitoring**

### **Render Dashboard এ:**
- Logs tab → Real-time logs দেখুন
- Metrics tab → CPU, Memory, Network usage
- Events tab → Deploy history

### **Database Query:**
- Shell tab → `psql` command দিয়ে database query করুন
- SQL Runner → GUI তে query execute করুন

---

## **🔐 Security Best Practices**

1. ✅ PostgreSQL SSL required (`?sslmode=require`)
2. ✅ SECRET_KEY minimum 32 characters
3. ✅ FLASK_ENV=production (development এ নয়)
4. ✅ Admin password change করুন (admin123 থেকে)
5. ✅ Google credentials file secure রাখুন
6. ✅ Environment variables কখনো commit করবেন না
7. ✅ `.env` file `.gitignore` এ add করুন

---

## **📞 যদি সমস্যা হয়:**

1. **Logs check করুন**: `your-app.onrender.com` → Logs
2. **Database connect তেস্ট করুন**: 
   ```bash
   python migrate_db.py
   ```
3. **Local-এ test করুন**:
   ```bash
   python run.py
   ```
4. **Render support contact করুন**: https://render.com/support
