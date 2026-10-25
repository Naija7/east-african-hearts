"""
Database migration: Convert BLOB photos to Base64 strings in MySQL + add cache table
Run this BEFORE deploying the code changes
"""
import mysql.connector
from db import get_db_connection

def migrate():
    db = get_db_connection()
    cursor = db.cursor()

    try:
        print("Starting database migration...")

        # Step 1: Modify profiles table - change profile_picture from BLOB to LONGTEXT
        print("1. Modifying profiles table...")
        cursor.execute("ALTER TABLE profiles MODIFY COLUMN profile_picture LONGTEXT")
        print("   ✅ Changed profile_picture column to LONGTEXT (for Base64 strings)")

        # Step 2: Clear existing photos (fresh start with Base64)
        print("2. Clearing existing photos...")
        cursor.execute("UPDATE profiles SET profile_picture = NULL")
        print(f"   ✅ Cleared photos (affected rows: {cursor.rowcount})")

        # Step 3: Create cache table
        print("3. Creating cache table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                cache_key VARCHAR(100) PRIMARY KEY,
                profiles_data LONGTEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("   ✅ Created cache table")

        db.commit()
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Deploy updated code")
        print("2. Users can upload photos in their profile")
        print("3. Photos stored as Base64 in MySQL")
        print("4. Discovery page uses PostgreSQL cache for speed")

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        db.rollback()
        raise
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    migrate()
