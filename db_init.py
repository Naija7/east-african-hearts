"""Create all tables if they don't exist. Safe to run on every startup."""
import os
import mysql.connector
from db import get_db_connection

CORE_TABLES = [
"""CREATE TABLE IF NOT EXISTS users (
  id int NOT NULL AUTO_INCREMENT,
  full_name varchar(100) NOT NULL,
  email varchar(100) NOT NULL,
  password_hash varchar(255) NOT NULL,
  gender enum('Male','Female','Other') NOT NULL,
  age int NOT NULL,
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  email_verified tinyint(1) DEFAULT '0',
  PRIMARY KEY (id),
  UNIQUE KEY email (email),
  KEY idx_gender_age (gender,age),
  CONSTRAINT users_chk_1 CHECK ((age >= 18))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS profiles (
  user_id int NOT NULL,
  bio text,
  interests text,
  location varchar(100) DEFAULT NULL,
  profile_picture longblob,
  PRIMARY KEY (user_id),
  KEY idx_location (location),
  FULLTEXT KEY idx_bio_interests (bio,interests),
  CONSTRAINT profiles_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS likes (
  id int NOT NULL AUTO_INCREMENT,
  liker_id int NOT NULL,
  liked_id int NOT NULL,
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uniq_like (liker_id,liked_id),
  KEY idx_liker (liker_id),
  KEY idx_liked (liked_id),
  CONSTRAINT likes_ibfk_1 FOREIGN KEY (liker_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT likes_ibfk_2 FOREIGN KEY (liked_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS matches (
  id int NOT NULL AUTO_INCREMENT,
  user1_id int NOT NULL,
  user2_id int NOT NULL,
  status enum('Pending','Matched','Blocked') DEFAULT 'Pending',
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uniq_match (user1_id,user2_id),
  KEY user2_id (user2_id),
  KEY idx_status (status),
  KEY idx_created (created_at),
  CONSTRAINT matches_ibfk_1 FOREIGN KEY (user1_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT matches_ibfk_2 FOREIGN KEY (user2_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS messages (
  id int NOT NULL AUTO_INCREMENT,
  match_id int NOT NULL,
  sender_id int NOT NULL,
  message_text text NOT NULL,
  sent_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY sender_id (sender_id),
  KEY idx_match_sender (match_id,sender_id),
  KEY idx_sent_at (sent_at),
  CONSTRAINT messages_ibfk_1 FOREIGN KEY (match_id) REFERENCES matches (id) ON DELETE CASCADE,
  CONSTRAINT messages_ibfk_2 FOREIGN KEY (sender_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS testimonials (
  id int NOT NULL AUTO_INCREMENT,
  male_name varchar(100) NOT NULL,
  female_name varchar(100) NOT NULL,
  country varchar(50) NOT NULL,
  story text,
  image_path varchar(255) DEFAULT NULL,
  status enum('pending','approved','rejected') DEFAULT 'pending',
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS email_verifications (
  id int NOT NULL AUTO_INCREMENT,
  user_id int NOT NULL,
  token varchar(255) NOT NULL,
  expires_at datetime NOT NULL,
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY token (token),
  KEY user_id (user_id),
  CONSTRAINT email_verifications_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
]

# Tables the code uses that were not in the local dump
EXTRA_TABLES = [
"""CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT, actor_id INT, type VARCHAR(50), related_id VARCHAR(50),
    read_status BOOLEAN DEFAULT 0, created_at DATETIME
)""",
"""CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT, event_type VARCHAR(50), details TEXT, created_at DATETIME
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
    FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE
)""",
"""CREATE TABLE IF NOT EXISTS password_resets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(100) UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_user (user_id),
    KEY idx_token (token),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS rate_limits (
    `key` VARCHAR(255) PRIMARY KEY,
    count INT DEFAULT 0,
    reset_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_reset_at (reset_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
]

# Drop order (children first) for replacing the earlier guessed schema
DROP_ORDER = ['messages', 'matches', 'likes', 'email_verifications', 'profiles',
              'testimonials', 'users']


def _replace_guessed_schema(cur):
    """An earlier version created guessed tables (profiles had an `id` column).
    Replace them with the real schema, but only if they hold no rows."""
    cur.execute("SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = DATABASE() AND table_name = 'profiles' "
                "AND column_name = 'id'")
    if cur.fetchone()[0] == 0:
        return
    for t in DROP_ORDER:
        cur.execute(f"SELECT COUNT(*) FROM `{t}`")
        if cur.fetchone()[0] > 0:
            print(f"Old schema kept: table {t} has data")
            return
    for t in DROP_ORDER:
        cur.execute(f"DROP TABLE IF EXISTS `{t}`")
    print("Replaced guessed tables with the real schema")


def init_db():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        _replace_guessed_schema(cur)
        for stmt in CORE_TABLES + EXTRA_TABLES:
            cur.execute(stmt)
        conn.commit()
        print("Database tables ready")
    except Exception as e:
        print(f"Database init failed: {e}")
    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
