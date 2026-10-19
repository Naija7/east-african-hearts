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
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key-change-this')

# Initialize rate limiter
limiter.init_app(app)

# Initialize email
init_email(app)

# ---------------------------
# DATABASE CONNECTION SECTION
# ---------------------------
db = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

cursor = db.cursor()
# ---------------------------

# Register Blueprints
app.register_blueprint(home)
app.register_blueprint(auth)
app.register_blueprint(testimonials)
app.register_blueprint(matching)

if __name__ == "__main__":
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='127.0.0.1', debug=debug_mode)
