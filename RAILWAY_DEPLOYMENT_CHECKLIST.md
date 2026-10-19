# Railway Deployment Checklist

## ✅ Pre-Deployment (Do This First)

### 1. Code Preparation
- [ ] Run app locally: `python app.py` (should start on http://127.0.0.1:5000)
- [ ] All tests pass
- [ ] No uncommitted changes: `git status` (should be clean)
- [ ] Push to GitHub: `git push origin main`

### 2. GitHub Setup
- [ ] Create GitHub account: https://github.com/signup
- [ ] Create new repository for this project
- [ ] Push code: `git push -u origin main`
- [ ] Verify code is on GitHub

### 3. Generate Production Credentials (DO NOT SKIP)
Save these somewhere secure (password manager):
```
FLASK_SECRET_KEY: 38526a31a74f231603eb19b8df6179d61fff48d82b2e730baa9e82553ce80cda
ADMIN_PASSWORD: z5YZO$jOsr0mwmMm (for first admin user)
```

---

## 🚀 Railway Deployment (15 Minutes)

### Step 1: Sign Up
1. Go to https://railway.app
2. Click "Start Free"
3. Sign up with GitHub (easiest option)
4. Connect your GitHub account

### Step 2: Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub"
3. Select your repository (east-african-hearts)
4. Railway auto-detects Flask app ✅

### Step 3: Set Environment Variables
In Railway Dashboard → Variables tab, add:

```
FLASK_SECRET_KEY=38526a31a74f231603eb19b8df6179d61fff48d82b2e730baa9e82553ce80cda
FLASK_ENV=production
FLASK_DEBUG=False

# MySQL will be auto-configured by Railway
# After adding MySQL plugin, use:
# DB_HOST = (copy from MySQL plugin settings)
# DB_USER = root (default)
# DB_PASSWORD = (copy from MySQL plugin settings)
# DB_NAME = datingdb

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

APP_URL=https://your-app.railway.app
```

### Step 4: Add MySQL Database
1. In Railway Dashboard, click "Add Service"
2. Select "MySQL"
3. Wait for MySQL to provision (2-3 minutes)
4. Copy the connection details
5. Update environment variables with MySQL credentials

### Step 5: Initialize Database
1. SSH into Railway container:
   ```bash
   railway run bash
   ```

2. Create database and tables:
   ```bash
   mysql -h $DB_HOST -u root -p$DB_PASSWORD
   ```

3. Run SQL:
   ```sql
   CREATE DATABASE IF NOT EXISTS datingdb;
   USE datingdb;
   
   -- Create all tables from your schema
   -- (Copy from your existing database)
   ```

### Step 6: Create First Admin User
```bash
railway run python manage_admin.py --action create --username admin --email your@email.com
```

When prompted, enter password: `z5YZO$jOsr0mwmMm`

### Step 7: Deploy
- Railway auto-deploys when you push to GitHub
- Check deployment status in Railway Dashboard
- Wait for "Running" status (green indicator)

---

## ✅ Post-Deployment Testing

### Test These Features
- [ ] App is accessible at `https://your-app.railway.app`
- [ ] HTTPS working (green lock icon)
- [ ] Admin login works (username: admin)
- [ ] User registration works
- [ ] Email verification emails send
- [ ] Password reset works
- [ ] Search/filtering works
- [ ] Notifications work
- [ ] Database queries work
- [ ] Rate limiting works

### Monitor for Issues
```bash
# View logs
railway logs

# Check environment variables
railway variables

# SSH into container
railway run bash
```

---

## 🔒 Security Checklist

- [ ] All credentials in Railway Variables (not in code)
- [ ] FLASK_SECRET_KEY is set to secure value
- [ ] FLASK_DEBUG is False in production
- [ ] `.env` file NOT committed to GitHub
- [ ] `.env.production` NOT committed to GitHub
- [ ] Database password is strong
- [ ] HTTPS is enabled (Railway does this automatically)
- [ ] Email credentials are app-password (not real Gmail password)
- [ ] Admin password changed from default

---

## 📊 Monitoring Setup

### 1. Error Tracking (Optional but Recommended)
```bash
pip install sentry-sdk
```

Add to `app.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

### 2. Uptime Monitoring
- Go to https://uptimerobot.com (free)
- Add your app URL
- Get alerts if app goes down

### 3. Database Backups
- Railway: Automatic daily backups ✅
- Manual backup: `railway run mysqldump -h $DB_HOST -u root -p$DB_PASSWORD datingdb > backup.sql`

---

## 🎯 Custom Domain (Optional)

### Add Your Domain
1. Railway Dashboard → Settings → Custom Domain
2. Add your domain (e.g., `eastafricanhearts.com`)
3. Update DNS records:
   - Add CNAME: `yourdomain.com → your-app.railway.app`
   - Wait 24 hours for propagation

---

## 💰 Cost Estimate

| Item | Cost |
|------|------|
| Flask App | $5/month |
| MySQL Database | Included |
| Storage | Included |
| **Total** | **$5-7/month** |

First month: Free ($5 credit)

---

## 🆘 Troubleshooting

### App won't deploy
- [ ] Check Railway logs: `railway logs`
- [ ] Verify all dependencies in `requirements.txt`
- [ ] Check `Procfile` exists (Railway auto-generates it)

### Database connection failing
- [ ] Verify MySQL service is "Running"
- [ ] Check DB credentials in Railway Variables
- [ ] Verify database name is correct

### Email not sending
- [ ] Check Gmail app password (not regular password)
- [ ] Verify `MAIL_USERNAME` is correct
- [ ] Check spam folder for test emails
- [ ] Enable "Less secure app access" if needed

### Admin login not working
- [ ] SSH into Railway: `railway run bash`
- [ ] Run: `python manage_admin.py --action list`
- [ ] Verify admin user exists
- [ ] Reset password if needed

---

## ✨ You're Done!

Your East African Hearts dating platform is now live on Railway! 🎉

**Next Steps:**
1. Test with real users
2. Monitor performance
3. Add custom domain
4. Set up backup strategy
5. Plan marketing launch

**Questions?** Check Railway docs: https://docs.railway.app

