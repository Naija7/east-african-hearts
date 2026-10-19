# Security Setup Guide - East African Hearts

## 🔐 Environment Variables Setup

All sensitive information is now stored in `.env` file instead of hardcoded in the code.

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

1. The `.env` file has been created with current values
2. **IMPORTANT**: Before deploying to production, change these values:

```bash
# In .env file, update:

# 1. Database Password (CRITICAL!)
DB_PASSWORD=maurinho  # ❌ Change this!
DB_PASSWORD=your_new_strong_password  # ✅ Use strong password

# 2. Admin Credentials (CRITICAL!)
ADMIN_USERNAME=admin  # Can change
ADMIN_PASSWORD=Admin@123  # ❌ Change this!
ADMIN_PASSWORD=your_new_strong_admin_password  # ✅ Use strong password

# 3. Secret Key (CRITICAL!)
FLASK_SECRET_KEY=your-super-secret-key-change-this-in-production-12345
# Generate a secure one:
# Python: import secrets; secrets.token_hex(32)

# 4. Flask Debug Mode (CRITICAL!)
FLASK_DEBUG=False  # Never True in production!
```

### Step 3: Secure the .env File

The `.env` file is added to `.gitignore` and will NOT be committed to git.

```bash
# Verify .env is in .gitignore
cat .gitignore | grep .env
```

### Step 4: Share with Developers (SAFE)

Use `.env.example` to share with developers:
- Contains structure only
- NO secrets
- Developers copy it and fill in their own values:

```bash
cp .env.example .env
# Then edit .env with their own values
```

---

## 📝 Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `DB_HOST` | Database host | `localhost` |
| `DB_USER` | Database user | `root` |
| `DB_PASSWORD` | Database password | `strong_password_123` |
| `DB_NAME` | Database name | `datingdb` |
| `FLASK_SECRET_KEY` | Session encryption key | Generated via `secrets.token_hex(32)` |
| `FLASK_ENV` | Environment | `development` or `production` |
| `FLASK_DEBUG` | Debug mode | `False` (NEVER True in production!) |
| `ADMIN_USERNAME` | Admin login username | `admin` |
| `ADMIN_PASSWORD` | Admin login password | `strong_password_123` |

---

## ✅ Security Checklist

- [x] Removed hardcoded database credentials
- [x] Removed hardcoded admin credentials
- [x] Removed hardcoded secret key
- [x] Disabled debug mode by default
- [x] Created .env for secrets
- [x] Created .env.example for developers
- [x] Added .env to .gitignore

---

## 🚀 Before Production

1. **Generate Secure Secret Key:**
   ```python
   import secrets
   print(secrets.token_hex(32))
   # Copy output to .env FLASK_SECRET_KEY
   ```

2. **Change ALL Passwords:**
   - Database password
   - Admin password
   - Secret key

3. **Set Production Values:**
   ```
   FLASK_ENV=production
   FLASK_DEBUG=False
   ```

4. **Verify .env is in .gitignore**

5. **Never commit .env to git!**

---

## 📦 Files Created/Updated

✅ `.env` - Secrets (gitignored)
✅ `.env.example` - Template for developers
✅ `.gitignore` - Prevent accidental commits
✅ `requirements.txt` - Dependencies including python-dotenv
✅ `app.py` - Uses environment variables
✅ `routes/auth.py` - Uses environment variables
✅ `routes/testimonials.py` - Uses environment variables
✅ `routes/matching.py` - Uses environment variables

---

## 🔍 Verification

Run the app and verify it works:

```bash
python app.py
```

If you see any errors about missing environment variables, check your .env file.

