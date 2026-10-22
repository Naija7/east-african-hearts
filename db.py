"""Database connection and pooling module for East African Hearts"""

import os
from flask import g, has_app_context
from werkzeug.local import LocalProxy
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

_pool = None


def _get_pool():
    """Lazily initialize and return the MySQL connection pool."""
    global _pool
    if _pool is None:
        try:
            pool_size = int(os.getenv('DB_POOL_SIZE', '5'))
            _pool = pooling.MySQLConnectionPool(
                pool_name="eaf_pool",
                pool_size=pool_size,
                pool_reset_session=True,
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                connection_timeout=10
            )
            print("MySQL connection pool initialized successfully")
        except Exception as e:
            print(f"Warning: Failed to initialize MySQL connection pool: {e}")
            _pool = None
    return _pool


def get_db_connection():
    """Create a standalone connection, or borrow one from the pool if available."""
    pool = _get_pool()
    if pool is not None:
        try:
            conn = pool.get_connection()
            if conn.is_connected():
                return conn
        except Exception as e:
            print(f"Pool get_connection failed, falling back to direct connection: {e}")

    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        connection_timeout=10
    )


def get_db():
    """
    Get a per-request database connection.
    Reuses connection within the request and pings to handle idle timeouts.
    """
    if has_app_context():
        if 'db' not in g:
            g.db = get_db_connection()
        else:
            try:
                g.db.ping(reconnect=True, attempts=3, delay=1)
            except Exception:
                g.db = get_db_connection()
        return g.db
    return get_db_connection()


def close_db(e=None):
    """Close the per-request database connection when request teardown occurs."""
    if has_app_context():
        conn = g.pop('db', None)
        if conn is not None:
            try:
                if conn.is_connected():
                    conn.close()
            except Exception:
                pass


def init_app_db(app):
    """Register teardown hook on Flask app."""
    app.teardown_appcontext(close_db)


# Global proxy for convenient usage across blueprints
db = LocalProxy(get_db)

