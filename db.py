import sqlite3
from datetime import datetime, timedelta
import pytz

DB_NAME = "bot_database.db"
DHAKA_TZ = pytz.timezone('Asia/Dhaka')

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            role TEXT DEFAULT 'basic',
            premium_expiry TEXT,
            daily_limit INTEGER DEFAULT 50,
            today_used INTEGER DEFAULT 0,
            last_active_date TEXT,
            is_banned INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

create_tables()

def get_dhaka_date():
    return datetime.now(DHAKA_TZ).strftime("%Y-%m-%d")

def check_daily_reset(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_active_date, role, premium_expiry FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    
    if result:
        last_date, role, expiry_str = result
        current_date = get_dhaka_date()
        
        # Premium Expiry Check
        if role == 'premium' and expiry_str:
            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
            if datetime.now(DHAKA_TZ).date() > expiry_date:
                cursor.execute("UPDATE users SET role='basic', daily_limit=50, premium_expiry=NULL WHERE user_id=?", (user_id,))
                conn.commit()
                role = 'basic'

        # Daily Reset Logic (New Day)
        if last_date != current_date:
            limit = 1000 if role == 'premium' else 50
            cursor.execute("UPDATE users SET today_used=0, last_active_date=?, daily_limit=? WHERE user_id=?", (current_date, limit, user_id))
            conn.commit()
            
    conn.close()

def add_user(user_id, username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        today = get_dhaka_date()
        cursor.execute("INSERT INTO users (user_id, username, last_active_date) VALUES (?, ?, ?)", (user_id, username, today))
    else:
        cursor.execute("UPDATE users SET username=? WHERE user_id=?", (username, user_id))
    conn.commit()
    conn.close()
    check_daily_reset(user_id)

def get_user_info(user_id):
    check_daily_reset(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    return data

def update_usage(user_id, count):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET today_used = today_used + ? WHERE user_id=?", (count, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()
    conn.close()
    return data

def set_premium(user_id, days):
    conn = get_connection()
    cursor = conn.cursor()
    expiry_date = datetime.now(DHAKA_TZ) + timedelta(days=days)
    expiry_str = expiry_date.strftime("%Y-%m-%d")
    cursor.execute("UPDATE users SET role='premium', daily_limit=1000, premium_expiry=? WHERE user_id=?", (expiry_str, user_id))
    conn.commit()
    conn.close()

def set_basic(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role='basic', daily_limit=50, premium_expiry=NULL WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def set_ban_status(user_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_banned=? WHERE user_id=?", (status, user_id))
    conn.commit()
    conn.close()

def reset_user_stats(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    current_date = get_dhaka_date()
    cursor.execute("UPDATE users SET today_used=0, last_active_date=? WHERE user_id=?", (current_date, user_id))
    conn.commit()
    conn.close()

def get_global_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(today_used) FROM users")
    data = cursor.fetchone()
    conn.close()
    return data