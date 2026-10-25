"""
Database migration: Convert BLOB photos to Cloudinary URLs + add cache table
Run this BEFORE deploying the code changes
"""
import mysql.connector
from db import get_db_connection

def migrate():
    db = get_db_connection()
    cursor = db.cursor()

    try:
        print("Starting database migration...")

        # Step 1: Modify profiles table - change profile_picture from BLOB to VARCHAR
        print("1. Modifying profiles table...")
        cursor.execute("ALTER TABLE profiles MODIFY COLUMN profile_picture VARCHAR(500)")
        print("   ✅ Changed profile_picture column to VARCHAR(500)")

        # Step 2: Clear existing photos (fresh start with Cloudinary)
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
        print("1. Install Cloudinary: pip install cloudinary")
        print("2. Add Cloudinary env vars: CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET")
        print("3. Deploy updated code")
        print("4. Users can re-upload their photos")

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        db.rollback()
        raise
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    migrate()
