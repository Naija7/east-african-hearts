#!/usr/bin/env python3
"""
Admin Credential Management Script
Usage: python manage_admin.py --action [create|update|delete|list]
"""

import os
import sys
import argparse
from getpass import getpass
import mysql.connector
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

def get_db():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

def create_admin(username, email, password):
    """Create new admin user"""
    if not username or not email or not password:
        print("❌ Username, email, and password are required")
        return False

    if len(password) < 8:
        print("❌ Password must be at least 8 characters")
        return False

    try:
        db = get_db()
        cursor = db.cursor()

        # Check if user exists
        cursor.execute("SELECT id FROM admin_users WHERE username = %s", (username,))
        if cursor.fetchone():
            print(f"❌ Admin user '{username}' already exists")
            cursor.close()
            db.close()
            return False

        # Create user
        password_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO admin_users (username, email, password_hash, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (username, email, password_hash))
        db.commit()
        cursor.close()
        db.close()

        print(f"✅ Admin user '{username}' created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        return False

def update_admin_password(username, new_password):
    """Update admin password"""
    if not username or not new_password:
        print("❌ Username and password are required")
        return False

    if len(new_password) < 8:
        print("❌ Password must be at least 8 characters")
        return False

    try:
        db = get_db()
        cursor = db.cursor()

        # Check if user exists
        cursor.execute("SELECT id FROM admin_users WHERE username = %s", (username,))
        if not cursor.fetchone():
            print(f"❌ Admin user '{username}' not found")
            cursor.close()
            db.close()
            return False

        # Update password
        password_hash = generate_password_hash(new_password)
        cursor.execute("""
            UPDATE admin_users SET password_hash = %s WHERE username = %s
        """, (password_hash, username))
        db.commit()
        cursor.close()
        db.close()

        print(f"✅ Password updated for '{username}'")
        return True
    except Exception as e:
        print(f"❌ Error updating password: {e}")
        return False

def list_admins():
    """List all admin users"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, username, email, created_at, last_login
            FROM admin_users
            ORDER BY created_at DESC
        """)
        admins = cursor.fetchall()
        cursor.close()
        db.close()

        if not admins:
            print("❌ No admin users found")
            return

        print("\n📋 Admin Users:")
        print("-" * 80)
        for admin in admins:
            print(f"ID: {admin['id']}")
            print(f"  Username: {admin['username']}")
            print(f"  Email: {admin['email']}")
            print(f"  Created: {admin['created_at']}")
            print(f"  Last Login: {admin['last_login'] or 'Never'}")
            print()
    except Exception as e:
        print(f"❌ Error listing admins: {e}")

def delete_admin(username):
    """Delete admin user"""
    if not username:
        print("❌ Username is required")
        return False

    try:
        db = get_db()
        cursor = db.cursor()

        # Check if user exists
        cursor.execute("SELECT id FROM admin_users WHERE username = %s", (username,))
        if not cursor.fetchone():
            print(f"❌ Admin user '{username}' not found")
            cursor.close()
            db.close()
            return False

        # Confirm deletion
        confirm = input(f"Are you sure you want to delete '{username}'? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Deletion cancelled")
            cursor.close()
            db.close()
            return False

        # Delete user
        cursor.execute("DELETE FROM admin_users WHERE username = %s", (username,))
        # Also delete any pending password reset tokens
        cursor.execute("""
            DELETE FROM admin_password_resets
            WHERE admin_id = (SELECT id FROM admin_users WHERE username = %s)
        """, (username,))
        db.commit()
        cursor.close()
        db.close()

        print(f"✅ Admin user '{username}' deleted successfully")
        return True
    except Exception as e:
        print(f"❌ Error deleting admin: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Admin Credential Management")
    parser.add_argument('--action', choices=['create', 'update', 'delete', 'list'],
                       required=True, help='Action to perform')
    parser.add_argument('--username', help='Admin username')
    parser.add_argument('--email', help='Admin email')
    parser.add_argument('--password', help='Admin password (will prompt if not provided)')

    args = parser.parse_args()

    if args.action == 'create':
        username = args.username or input("Enter admin username: ").strip()
        email = args.email or input("Enter admin email: ").strip()
        password = args.password or getpass("Enter admin password: ")
        create_admin(username, email, password)

    elif args.action == 'update':
        username = args.username or input("Enter admin username: ").strip()
        password = args.password or getpass("Enter new password: ")
        update_admin_password(username, password)

    elif args.action == 'delete':
        username = args.username or input("Enter admin username: ").strip()
        delete_admin(username)

    elif args.action == 'list':
        list_admins()

if __name__ == '__main__':
    main()
