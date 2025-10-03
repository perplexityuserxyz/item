import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict

class Database:
    def __init__(self, db_name: str = "osint_bot.db"):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                date TEXT,
                FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                FOREIGN KEY (referred_id) REFERENCES users(user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS protected_numbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT UNIQUE,
                added_by INTEGER,
                added_date TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT UNIQUE,
                type TEXT,
                added_by INTEGER,
                added_date TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                search_type TEXT,
                query TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id: int, username: Optional[str] = None, first_name: Optional[str] = None, referrer_id: Optional[int] = None) -> bool:
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
        
        if row:
            return {
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'credits': row[3],
                'referrer_id': row[4],
                'referred_count': row[5],
                'is_banned': row[6],
                'joined_date': row[7],
                'last_active': row[8]
            }
        return None
    
    def update_credits(self, user_id: int, amount: int, operation: str = 'add') -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if operation == 'add':
            cursor.execute('UPDATE users SET credits = credits + ? WHERE user_id = ?', (amount, user_id))
        elif operation == 'deduct':
            cursor.execute('UPDATE users SET credits = credits - ? WHERE user_id = ? AND credits >= ?', 
                         (amount, user_id, amount))
        elif operation == 'set':
            cursor.execute('UPDATE users SET credits = ? WHERE user_id = ?', (amount, user_id))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def deduct_credit(self, user_id: int) -> bool:
        return self.update_credits(user_id, 1, 'deduct')
    
    def ban_user(self, user_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def unban_user(self, user_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def is_banned(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        return user['is_banned'] == 1 if user else False
    
    def add_protected_number(self, number: str, added_by: int) -> bool:
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
    
    def remove_protected_number(self, number: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM protected_numbers WHERE number = ?', (number,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def is_protected(self, number: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM protected_numbers WHERE number = ?', (number,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def get_protected_numbers(self) -> List[str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT number FROM protected_numbers')
        numbers = [row[0] for row in cursor.fetchall()]
        conn.close()
        return numbers
    
    def add_to_blacklist(self, identifier: str, type: str, added_by: int) -> bool:
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
    
    def remove_from_blacklist(self, identifier: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM blacklist WHERE identifier = ?', (identifier,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def is_blacklisted(self, identifier: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM blacklist WHERE identifier = ?', (identifier,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
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
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_banned = 0')
        active_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_banned = 1')
        banned_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM search_logs')
        total_searches = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM referrals')
        total_referrals = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(credits) FROM users')
        total_credits = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'banned_users': banned_users,
            'total_searches': total_searches,
            'total_referrals': total_referrals,
            'total_credits': total_credits
        }
    
    def get_all_user_ids(self) -> List[int]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE is_banned = 0')
        user_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return user_ids
    
    def update_last_active(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_active = ? WHERE user_id = ?', 
                     (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()
    
    def add_commission(self, referrer_id: int, amount: int):
        commission = int(amount * 0.30)
        self.update_credits(referrer_id, commission, 'add')
