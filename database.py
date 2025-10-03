import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Tuple


class Database:
    def __init__(self, db_name: str = "osint_bot.db"):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                credits INTEGER DEFAULT 2,
                referrer_id INTEGER,
                referred_count INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                joined_date TEXT,
                last_active TEXT
            )
        ''')

        # Referrals
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                date TEXT
            )
        ''')

        # Protected numbers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS protected_numbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT UNIQUE,
                added_by INTEGER,
                added_date TEXT
            )
        ''')

        # Blacklist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT UNIQUE,
                type TEXT,
                added_by INTEGER,
                added_date TEXT
            )
        ''')

        # Search logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                search_type TEXT,
                query TEXT,
                timestamp TEXT
            )
        ''')

        # Redeem codes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS redeem_codes (
                code TEXT PRIMARY KEY,
                credits INTEGER,
                used_by INTEGER,
                used_at TEXT
            )
        ''')

        conn.commit()
        conn.close()

    # ---------------- User management ----------------

    def add_user(self, user_id: int, username: str = None, first_name: str = None, referrer_id: int = None):
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, referrer_id, joined_date, last_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, referrer_id, datetime.now().isoformat(), datetime.now().isoformat()))

            if referrer_id:
                cursor.execute('INSERT INTO referrals (referrer_id, referred_id, date) VALUES (?, ?, ?)',
                               (referrer_id, user_id, datetime.now().isoformat()))
                cursor.execute('UPDATE users SET referred_count = referred_count + 1, credits = credits + 1 WHERE user_id = ?',
                               (referrer_id,))

            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_user(self, user_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_last_active(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_active = ? WHERE user_id = ?', (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()

    def update_credits(self, user_id: int, amount: int, operation: str = 'add') -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        if operation == 'add':
            cursor.execute('UPDATE users SET credits = credits + ? WHERE user_id = ?', (amount, user_id))
        elif operation == 'deduct':
            cursor.execute('UPDATE users SET credits = credits - ? WHERE user_id = ? AND credits >= ?', (amount, user_id, amount))
        elif operation == 'set':
            cursor.execute('UPDATE users SET credits = ? WHERE user_id = ?', (amount, user_id))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def deduct_credit(self, user_id: int) -> bool:
        return self.update_credits(user_id, 1, 'deduct')

    def ban_user(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

    def unban_user(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

    def is_banned(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        return user['is_banned'] == 1 if user else False

    # ---------------- Redeem codes ----------------

    def create_redeem_code(self, code: str, credits: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO redeem_codes (code, credits) VALUES (?, ?)", (code, credits))
        conn.commit()
        conn.close()

    def redeem_code(self, user_id: int, code: str) -> Tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT code, credits, used_by FROM redeem_codes WHERE code = ?", (code,))
        row = cursor.fetchone()

        if not row:
            return False, "❌ Invalid code!"
        if row["used_by"]:
            return False, "❌ Code already used!"

        credits = row["credits"]
        cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (credits, user_id))
        cursor.execute("UPDATE redeem_codes SET used_by = ?, used_at = ? WHERE code = ?", (user_id, datetime.now().isoformat(), code))
        conn.commit()
        conn.close()
        return True, f"✅ {credits} credits added!"

    # ---------------- Protected & blacklist ----------------

    def add_protected_number(self, number: str, added_by: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO protected_numbers (number, added_by, added_date) VALUES (?, ?, ?)',
                           (number, added_by, datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def is_protected(self, number: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM protected_numbers WHERE number = ?', (number,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def add_to_blacklist(self, identifier: str, type: str, added_by: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO blacklist (identifier, type, added_by, added_date) VALUES (?, ?, ?, ?)',
                           (identifier, type, added_by, datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def is_blacklisted(self, identifier: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM blacklist WHERE identifier = ?', (identifier,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    # ---------------- Logging & stats ----------------

    def log_search(self, user_id: int, search_type: str, query: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO search_logs (user_id, search_type, query, timestamp) VALUES (?, ?, ?, ?)',
                       (user_id, search_type, query, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_stats(self) -> Dict:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM search_logs")
        total_searches = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        banned_users = cursor.fetchone()[0]
        conn.close()
        return {
            "total_users": total_users,
            "total_searches": total_searches,
            "banned_users": banned_users
        }
