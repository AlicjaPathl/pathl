import sqlite3
import time

class LocalDB:
    def __init__(self, filename="local.db"):
        self.conn = sqlite3.connect(filename)
        self.cur = self.conn.cursor()

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS kv (
            key TEXT PRIMARY KEY,
            value TEXT,
            expires_at REAL
        )
        """)
        self.conn.commit()

    # zapis
    def set(self, key, value, ttl=None):
        expires = time.time() + ttl if ttl else None
        self.cur.execute("""
        REPLACE INTO kv (key, value, expires_at)
        VALUES (?, ?, ?)
        """, (key, value, expires))
        self.conn.commit()

    # odczyt
    def get(self, key):
        self.cur.execute("SELECT value, expires_at FROM kv WHERE key=?", (key,))
        row = self.cur.fetchone()

        if not row:
            return None

        value, expires = row

        # TTL check
        if expires and time.time() > expires:
            self.delete(key)
            return None

        return value

    # usuwanie
    def delete(self, key):
        self.cur.execute("DELETE FROM kv WHERE key=?", (key,))
        self.conn.commit()

    # sprawdzenie istnienia
    def exists(self, key):
        return self.get(key) is not None

    # czyszczenie wygasłych
    def cleanup(self):
        self.cur.execute("DELETE FROM kv WHERE expires_at IS NOT NULL AND expires_at < ?", (time.time(),))
        self.conn.commit()