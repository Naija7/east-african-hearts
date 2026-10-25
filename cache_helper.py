"""
Cache helper for discovery profiles
Replaces in-memory dict with database-backed cache
"""
import json
from datetime import datetime
from utils import log_error, log_info

class ProfileCache:
    """Thread-safe profile cache using database"""

    CACHE_KEY = 'discovery_profiles'
    CACHE_TTL_SECONDS = 30

    @staticmethod
    def get(db):
        """Get cached profiles if still valid"""
        try:
            cursor = db.cursor(dictionary=True)
            cursor.execute(f"""
                SELECT profiles_data FROM cache
                WHERE cache_key = %s
                AND created_at > DATE_SUB(NOW(), INTERVAL {ProfileCache.CACHE_TTL_SECONDS} SECOND)
                LIMIT 1
            """, (ProfileCache.CACHE_KEY,))

            result = cursor.fetchone()
            cursor.close()

            if result:
                profiles = json.loads(result['profiles_data'])
                log_info(f"Cache HIT: Retrieved {len(profiles)} profiles from cache")
                return profiles

            log_info("Cache MISS: No valid cache found")
            return None

        except Exception as e:
            log_error(f"Cache GET error: {e}", exc_info=True)
            return None

    @staticmethod
    def set(db, profiles):
        """Cache profiles in database"""
        try:
            cursor = db.cursor()
            profiles_json = json.dumps(profiles, default=str)

            cursor.execute(f"""
                INSERT INTO cache (cache_key, profiles_data, created_at)
                VALUES (%s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    profiles_data = VALUES(profiles_data),
                    created_at = NOW()
            """, (ProfileCache.CACHE_KEY, profiles_json))

            db.commit()
            cursor.close()
            log_info(f"Cache SET: Cached {len(profiles)} profiles")

        except Exception as e:
            log_error(f"Cache SET error: {e}", exc_info=True)
            db.rollback()

    @staticmethod
    def clear(db):
        """Clear cache"""
        try:
            cursor = db.cursor()
            cursor.execute("DELETE FROM cache WHERE cache_key = %s", (ProfileCache.CACHE_KEY,))
            db.commit()
            cursor.close()
            log_info("Cache cleared")

        except Exception as e:
            log_error(f"Cache CLEAR error: {e}", exc_info=True)
            db.rollback()
