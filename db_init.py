"""Create all tables if they don't exist. Safe to run on every startup."""
import os
import mysql.connector

TABLES = [
"""CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    gender VARCHAR(20),
    age INT,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""",
"""CREATE TABLE IF NOT EXISTS profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    bio TEXT,
    interests TEXT,
    location VARCHAR(255),
    profile_picture LONGBLOB,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)""",
"""CREATE TABLE IF NOT EXISTS likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    liker_id INT NOT NULL,
    liked_id INT NOT NULL,
    created_at DATETIME,
    FOREIGN KEY (liker_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (liked_id) REFERENCES users(id) ON DELETE CASCADE
)""",
"""CREATE TABLE IF NOT EXISTS matches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user1_id INT NOT NULL,
    user2_id INT NOT NULL,
    status VARCHAR(20),
    created_at DATETIME,
    FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE
)""",
"""CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    match_id INT NOT NULL,
    sender_id INT NOT NULL,
    message_text TEXT,
    sent_at DATETIME,
    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
)""",
"""CREATE TABLE IF NOT EXISTS testimonials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    male_name VARCHAR(100),
    female_name VARCHAR(100),
    country VARCHAR(100),
    story TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""",
"""CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    actor_id INT,
    type VARCHAR(50),
    related_id VARCHAR(50),
    read_status BOOLEAN DEFAULT 0,
    created_at DATETIME
)""",
"""CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    event_type VARCHAR(50),
    details TEXT,
    created_at DATETIME
)""",
"""CREATE TABLE IF NOT EXISTS email_verifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)""",
"""CREATE TABLE IF NOT EXISTS admin_users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
)""",
"""CREATE TABLE IF NOT EXISTS admin_password_resets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT NOT NULL,
    token VARCHAR(100) UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admin_users(id)
)""",
]


def init_db():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'), database=os.getenv('DB_NAME'))
        cur = conn.cursor()
        for stmt in TABLES:
            cur.execute(stmt)
        conn.commit()
        cur.close()
        conn.close()
        print("Database tables ready")
    except Exception as e:
        print(f"Database init failed: {e}")
