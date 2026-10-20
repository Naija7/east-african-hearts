from flask import Flask
from routes.home import home
from routes.auth import auth
from routes.testimonials import testimonials
from routes.matching import matching
import mysql.connector
from dotenv import load_dotenv
import os
from rate_limiter import limiter
from email_sender import init_email

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Behind Railway's proxy: use the real client IP (needed for per-IP rate limits)
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key-change-this')

# Initialize rate limiter
limiter.init_app(app)

# Initialize email
init_email(app)

# Create tables if missing
from db_init import init_db
init_db()

# ---------------------------
# DATABASE CONNECTION SECTION
# ---------------------------
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

db = None
cursor = None
# ---------------------------

# Register Blueprints
app.register_blueprint(home)
app.register_blueprint(auth)
app.register_blueprint(testimonials)
app.register_blueprint(matching)

if __name__ == "__main__":
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
