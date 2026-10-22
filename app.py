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

# Initialize rate limiter
limiter.init_app(app)

# Initialize email
init_email(app)

# Initialize database pool & teardown handler
init_app_db(app)

# Create tables if missing
from db_init import init_db
init_db()

# Register Blueprints
app.register_blueprint(home)
app.register_blueprint(auth)
app.register_blueprint(testimonials)
app.register_blueprint(matching)

if __name__ == "__main__":
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
