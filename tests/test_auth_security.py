import os
import unittest
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from db import get_db_connection
from email_verification import (
    create_verification_token,
    verify_token,
    create_password_reset_token,
    verify_password_reset_token,
    complete_password_reset
)

class AuthSecurityTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()
        cls.conn = get_db_connection()
        cls.cursor = cls.conn.cursor(dictionary=True)

        # Clean up test user if exists
        cls.test_email = "test_security_audit@example.com"
        cls.cursor.execute("DELETE FROM users WHERE email = %s", (cls.test_email,))
        cls.cursor.execute("SELECT id FROM admin_users WHERE username = %s", ("test_security_admin",))
        existing_admin = cls.cursor.fetchone()
        if existing_admin:
            cls.cursor.execute("DELETE FROM admin_password_resets WHERE admin_id = %s", (existing_admin['id'],))
            cls.cursor.execute("DELETE FROM admin_users WHERE id = %s", (existing_admin['id'],))
        cls.conn.commit()

        # Insert test user
        cls.pw_hash = generate_password_hash("Password123!")
        cls.cursor.execute("""
            INSERT INTO users (full_name, email, password_hash, gender, age, email_verified)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ("Security Test User", cls.test_email, cls.pw_hash, "Male", 25, 1))
        cls.conn.commit()
        cls.user_id = cls.cursor.lastrowid

        # Insert test admin
        cls.cursor.execute("""
            INSERT INTO admin_users (username, email, password_hash)
            VALUES (%s, %s, %s)
        """, ("test_security_admin", "admin_audit@example.com", cls.pw_hash))
        cls.conn.commit()
        cls.admin_id = cls.cursor.lastrowid

    @classmethod
    def tearDownClass(cls):
        try:
            cls.cursor.execute("DELETE FROM password_resets WHERE user_id = %s", (cls.user_id,))
            cls.cursor.execute("DELETE FROM users WHERE email = %s", (cls.test_email,))
            cls.cursor.execute("DELETE FROM admin_password_resets WHERE admin_id = %s", (cls.admin_id,))
            cls.cursor.execute("DELETE FROM admin_users WHERE id = %s", (cls.admin_id,))
            cls.conn.commit()
            cls.cursor.close()
            cls.conn.close()
        except Exception as e:
            print(f"Cleanup error: {e}")

    def test_user_password_reset_flow(self):
        # 1. Create password reset token
        token = create_password_reset_token(self.user_id, self.conn)
        self.assertIsNotNone(token)
        self.assertTrue(len(token) > 20)

        # 2. Verify token
        is_valid, user_id, error = verify_password_reset_token(token, self.conn)
        self.assertTrue(is_valid)
        self.assertEqual(user_id, self.user_id)
        self.assertIsNone(error)

        # 3. Complete password reset with new password
        new_pw = "NewSecretPassword456!"
        new_pw_hash = generate_password_hash(new_pw)
        success = complete_password_reset(self.user_id, new_pw_hash, self.conn)
        self.assertTrue(success)

        # 4. Old token should now be consumed/invalid
        is_valid_again, _, _ = verify_password_reset_token(token, self.conn)
        self.assertFalse(is_valid_again)

        # 5. Check in DB that password was updated
        self.cursor.execute("SELECT password_hash FROM users WHERE id = %s", (self.user_id,))
        row = self.cursor.fetchone()
        self.assertTrue(check_password_hash(row['password_hash'], new_pw))
        self.assertFalse(check_password_hash(row['password_hash'], "Password123!"))

    def test_admin_password_reset_request(self):
        # Test admin forgot password endpoint (which previously threw TypeError)
        response = self.client.post("/admin-forgot-password", data={
            "username": "test_security_admin"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Check that token was recorded in admin_password_resets table
        self.cursor.execute("SELECT * FROM admin_password_resets WHERE admin_id = %s", (self.admin_id,))
        record = self.cursor.fetchone()
        self.assertIsNotNone(record)
        self.assertTrue(len(record['token']) > 20)

    def test_login_enforces_email_verification_when_enabled(self):
        # Create unverified user
        unverified_email = "unverified_test@example.com"
        self.cursor.execute("DELETE FROM users WHERE email = %s", (unverified_email,))
        self.cursor.execute("""
            INSERT INTO users (full_name, email, password_hash, gender, age, email_verified)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ("Unverified User", unverified_email, self.pw_hash, "Female", 22, 0))
        self.conn.commit()

        # Temporarily enable email verification
        os.environ['EMAIL_VERIFICATION_ENABLED'] = 'true'
        try:
            response = self.client.post("/login", data={
                "email": unverified_email,
                "password": "Password123!"
            }, follow_redirects=False)

            # Should redirect to resend_verification
            self.assertEqual(response.status_code, 302)
            self.assertIn("/resend-verification", response.location)
        finally:
            os.environ['EMAIL_VERIFICATION_ENABLED'] = 'false'
            self.cursor.execute("DELETE FROM users WHERE email = %s", (unverified_email,))
            self.conn.commit()

    def test_get_login_page_renders_ok(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Forgot your password?", response.data)

    def test_get_forgot_password_renders_ok(self):
        response = self.client.get("/forgot-password")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Reset Your Password", response.data)

if __name__ == "__main__":
    unittest.main()

