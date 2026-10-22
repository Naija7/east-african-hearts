import unittest
from app import app
from db import get_db_connection

class FullFlowTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.conn = get_db_connection()
        self.cur = self.conn.cursor()
        self.cur.execute("DELETE FROM users WHERE email = %s", ("flow_test@example.com",))
        self.conn.commit()

    def tearDown(self):
        self.cur.execute("DELETE FROM users WHERE email = %s", ("flow_test@example.com",))
        self.conn.commit()
        self.cur.close()
        self.conn.close()

    def test_full_auth_flow(self):
        # 1. Register
        resp = self.client.post('/register', data={
            'name': 'Flow Tester',
            'email': 'flow_test@example.com',
            'password': 'Password123!',
            'password_confirm': 'Password123!',
            'gender': 'Male',
            'age': '28',
            'location': 'Nairobi',
            'interests': 'Music, Traveling'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Registration successful", resp.data)

        # 2. Login
        resp = self.client.post('/login', data={
            'email': 'flow_test@example.com',
            'password': 'Password123!'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Welcome back!", resp.data)

        # 3. Access home while logged in
        resp = self.client.get('/', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Discovery", resp.data)
        self.assertIn(b"Logout", resp.data)

        # 4. Logout
        resp = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Logged out successfully", resp.data)

if __name__ == "__main__":
    unittest.main()

