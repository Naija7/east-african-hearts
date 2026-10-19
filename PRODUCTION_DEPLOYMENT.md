# PRODUCTION DEPLOYMENT GUIDE

**Choose ONE of these platforms for your 5,000 users app:**

---

## OPTION 1: RAILWAY (RECOMMENDED - Easiest & Cheapest)

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial production app"
git branch -M main
git remote add origin https://github.com/yourname/yourrepo.git
git push -u origin main
```

### Step 2: Deploy to Railway
1. Go to https://railway.app
2. Sign up with GitHub
3. Create new project → Deploy from GitHub
4. Select your repository
5. Railway auto-detects Flask app

### Step 3: Configure Environment
In Railway dashboard → Variables:
```
FLASK_SECRET_KEY=<generate-32-char-random>
FLASK_ENV=production
DB_HOST=<railway-mysql-host>
DB_USER=root
DB_PASSWORD=<railway-generated>
DB_NAME=east_african_dating
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=<app-password>
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
```

### Step 4: Create Database & Tables
```bash
# SSH into Railway container
# Run this to create tables:
mysql -h <DB_HOST> -u root -p
```

Then run:
```sql
CREATE DATABASE east_african_dating;
USE east_african_dating;

-- Create all tables (users, profiles, etc.)
-- [Run your CREATE TABLE statements]

-- Create admin table
CREATE TABLE admin_users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(100) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_login DATETIME
);

-- Create password reset table
CREATE TABLE admin_password_resets (
  id INT PRIMARY KEY AUTO_INCREMENT,
  admin_id INT NOT NULL,
  token VARCHAR(100) UNIQUE NOT NULL,
  expires_at DATETIME NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (admin_id) REFERENCES admin_users(id)
);
```

### Step 5: Create First Admin
```bash
# SSH into container, or run via Railway CLI:
python manage_admin.py --action create --username admin --email your@email.com
```

### Step 6: Deploy Custom Domain
Railway → Settings → Custom Domain → Add your domain

**Total Cost:** $5-7/month (includes MySQL)

---

## OPTION 2: RENDER (FREE TIER + Paid Database)

### Step 1-2: Same as Railway (GitHub push)

### Step 3: Create MySQL Database
1. Go to https://render.com
2. Dashboard → New MySQL
3. Choose pricing tier (paid ~$15/month)
4. Copy connection details

### Step 4: Deploy Web Service
1. New Web Service
2. Connect GitHub repository
3. Set environment variables (same as above)
4. Deploy

### Step 5: Create Admin
```bash
# SSH into service
python manage_admin.py --action create --username admin
```

**Total Cost:** $7-15/month (depending on DB tier)

---

## OPTION 3: HEROKU (Most Reliable)

### Step 1: Sign up & Install CLI
```bash
curl https://cli.heroku.com/install.sh | sh
heroku login
```

### Step 2: Create App
```bash
heroku create your-app-name
```

### Step 3: Add MySQL Database
```bash
heroku addons:create cleardb:ignite
heroku config | grep CLEARDB_DATABASE_URL
```

### Step 4: Set Environment Variables
```bash
heroku config:set FLASK_SECRET_KEY=xxx
heroku config:set FLASK_ENV=production
heroku config:set SESSION_COOKIE_SECURE=True
heroku config:set SESSION_COOKIE_HTTPONLY=True
```

### Step 5: Deploy
```bash
git push heroku main
```

### Step 6: Create Admin
```bash
heroku run python manage_admin.py --action create --username admin
```

### Step 7: Setup Domain
```bash
heroku domains:add your-domain.com
```

**Total Cost:** $50/month (Heroku is expensive compared to alternatives)

---

## DEPLOY WITH .env SECURITY

### Create .env.production (NEVER commit to Git):
```
FLASK_SECRET_KEY=<32-char-random-string>
FLASK_ENV=production
DB_HOST=your-production-db.com
DB_USER=production_user
DB_PASSWORD=<strong-password>
DB_NAME=east_african_dating
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=<gmail-app-password>
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

### .gitignore (protect secrets):
```
.env
.env.production
.env.local
*.pyc
__pycache__/
instance/
.DS_Store
```

---

## POST-DEPLOYMENT CHECKLIST

- [ ] Test admin login works
- [ ] Test user registration works
- [ ] Test email verification works
- [ ] Test password reset works
- [ ] Test admin password reset works
- [ ] Test search & filters work
- [ ] Test notifications work
- [ ] Verify HTTPS is enabled
- [ ] Verify secure cookies are set
- [ ] Verify rate limiting works
- [ ] Check database backups configured
- [ ] Monitor error logs
- [ ] Test with 10+ concurrent users
- [ ] Verify logging is working
- [ ] Test from different countries (for your African users)

---

## MONITORING & MAINTENANCE

### Set up error monitoring:
```bash
# Install Sentry for error tracking
pip install sentry-sdk
```

### Add to app.py:
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

### Database Backups:
- Railway: Automatic daily
- Render: Configure backups
- Heroku: Use pg_backup_api

### Monitoring:
- Set up uptime monitoring (UptimeRobot - free)
- Monitor database size
- Check logs regularly
- Monitor user growth

---

## MY FINAL RECOMMENDATION

**For your East African dating platform with 5,000 users:**

### BEST CHOICE: Railway
- ✅ Cheapest (~$5-7/month)
- ✅ Easiest to deploy
- ✅ Good performance
- ✅ MySQL included
- ✅ Auto-scaling
- ✅ Great support

### Second Choice: Render
- ✅ Free tier available
- ✅ Easy deployment
- ✅ Scales well
- ⚠️ Database extra cost

### Avoid: Replit for Production
- ❌ Not designed for production
- ❌ File system ephemeral
- ❌ Limited resources
- ❌ Expensive at scale
- ❌ Data loss risk

---

**Budget:** Plan for $7-12/month for reliable production hosting
**Time to Deploy:** 30 minutes with Railway
**Quality:** Production-ready, scalable to 5,000+ users

