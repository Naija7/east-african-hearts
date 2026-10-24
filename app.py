from flask import Flask
from routes.home import home
from routes.auth import auth
from routes.testimonials import testimonials
from routes.matching import matching
from dotenv import load_dotenv
import os
from rate_limiter import limiter
from email_sender import init_email
from db import init_app_db, get_db_connection
from datetime import datetime, timedelta
from flask_limiter.strategies import FixedWindowRateLimiterStrategy
from flask_limiter.util import get_remote_address

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Behind Railway's proxy: use the real client IP (needed for per-IP rate limits)
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
_debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
_secret = os.getenv("FLASK_SECRET_KEY")
if not _secret:
    if not _debug:
        raise RuntimeError("FLASK_SECRET_KEY must be set")
    _secret = "dev-only-secret"
app.secret_key = _secret

app.config.update(
    SESSION_COOKIE_SECURE=not _debug,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# CSRF protection for all POST routes
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# Database-backed rate limit storage for MySQL
class DatabaseRateLimiterStorage:
    """MySQL-backed storage for rate limiting - persists across restarts"""

    def __init__(self):
        self.db = None

    def _get_db(self):
        """Get database connection"""
        if self.db is None:
            self.db = get_db_connection()
        return self.db

    def get(self, key):
        """Get current count for a key"""
        try:
            db = self._get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT count FROM rate_limits WHERE `key` = %s AND reset_at > NOW()",
                (key,)
            )
            result = cursor.fetchone()
            cursor.close()
            return result['count'] if result else 0
        except Exception as e:
            print(f"Rate limit get error: {e}")
            return 0

    def set(self, key, value, ex=None):
        """Set count for a key with optional expiration"""
        try:
            db = self._get_db()
            cursor = db.cursor()
            reset_at = datetime.now() + timedelta(seconds=ex) if ex else None
            cursor.execute(
                """INSERT INTO rate_limits (`key`, count, reset_at)
                   VALUES (%s, %s, %s)
                   ON DUPLICATE KEY UPDATE count = %s, reset_at = %s""",
                (key, value, reset_at, value, reset_at)
            )
            db.commit()
            cursor.close()
        except Exception as e:
            print(f"Rate limit set error: {e}")

    def incr(self, key, delta=1, ex=None):
        """Increment count for a key"""
        try:
            db = self._get_db()
            cursor = db.cursor(dictionary=True)
            reset_at = datetime.now() + timedelta(seconds=ex) if ex else None

            # First, check if key exists and is not expired
            cursor.execute(
                "SELECT count FROM rate_limits WHERE `key` = %s AND reset_at > NOW()",
                (key,)
            )
            result = cursor.fetchone()

            if result:
                new_count = result['count'] + delta
                cursor.execute(
                    "UPDATE rate_limits SET count = %s, reset_at = %s WHERE `key` = %s",
                    (new_count, reset_at, key)
                )
            else:
                cursor.execute(
                    """INSERT INTO rate_limits (`key`, count, reset_at)
                       VALUES (%s, %s, %s)""",
                    (key, delta, reset_at)
                )
            db.commit()
            cursor.close()
            return self.get(key)
        except Exception as e:
            print(f"Rate limit increment error: {e}")
            return 0

    def clear(self, key):
        """Clear a rate limit key"""
        try:
            db = self._get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM rate_limits WHERE `key` = %s", (key,))
            db.commit()
            cursor.close()
        except Exception as e:
            print(f"Rate limit clear error: {e}")

# Initialize database and create tables first
init_app_db(app)
from db_init import init_db
init_db()

# Now initialize rate limiter with custom storage
db_storage = DatabaseRateLimiterStorage()
limiter.storage = db_storage
limiter.init_app(app, strategy=FixedWindowRateLimiterStrategy())

# Initialize email
init_email(app)

# Register Blueprints
app.register_blueprint(home)
app.register_blueprint(auth)
app.register_blueprint(testimonials)
app.register_blueprint(matching)

if __name__ == "__main__":
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
