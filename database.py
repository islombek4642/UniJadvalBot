import sqlite3
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DATABASE_FILE", "schedules.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            chat_id INTEGER PRIMARY KEY,
            file_id TEXT DEFAULT '',
            language TEXT DEFAULT 'UZ',
            broadcast_time TEXT DEFAULT '',
            weekend_mode INTEGER DEFAULT 0,
            group_title TEXT DEFAULT ''
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            phone_number TEXT,
            first_name TEXT,
            last_name TEXT,
            username TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            chat_id INTEGER PRIMARY KEY,
            title TEXT,
            username TEXT,
            type TEXT DEFAULT 'supergroup',
            member_count INTEGER DEFAULT 0
        )
    """)
    # Migration: Add broadcast_time column if it doesn't exist
    cursor.execute("PRAGMA table_info(schedules)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'broadcast_time' not in columns:
        cursor.execute("ALTER TABLE schedules ADD COLUMN broadcast_time TEXT DEFAULT ''")
        logger.info("Database migration: added 'broadcast_time' column.")
    
    if 'weekend_mode' not in columns:
        cursor.execute("ALTER TABLE schedules ADD COLUMN weekend_mode INTEGER DEFAULT 0")
        logger.info("Database migration: added 'weekend_mode' column.")
    
    # Migration: Add language column if it doesn't exist (re-adding this from original init_db logic)
    if 'language' not in columns:
        cursor.execute("ALTER TABLE schedules ADD COLUMN language TEXT DEFAULT 'UZ'")
        logger.info("Database migration: added 'language' column.")

    if 'group_title' not in columns:
        cursor.execute("ALTER TABLE schedules ADD COLUMN group_title TEXT DEFAULT ''")
        logger.info("Database migration: added 'group_title' column.")

    # Migration: Remove updated_at column if it exists (as it's removed from CREATE TABLE)
    if 'updated_at' in columns:
        # SQLite does not support dropping columns directly in older versions,
        # but for simplicity and common use cases, we'll assume a new table creation
        # or manual migration if this becomes an issue.
        # For now, we'll just ensure it's not created if it doesn't exist.
        # If it exists, it will remain but won't be used by new code.
        # A proper migration would involve renaming, creating new, copying, dropping old.
        logger.warning("The 'updated_at' column is no longer managed by init_db. If it exists, it will persist.")

    # Migration: Move group titles from schedules to groups table if groups table is empty but schedules has data
    cursor.execute("SELECT count(*) FROM groups")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT chat_id, group_title FROM schedules")
        rows = cursor.fetchall()
        for row in rows:
            chat_id, title = row
            if title: # Only migrate if title exists
                cursor.execute("INSERT OR IGNORE INTO groups (chat_id, title) VALUES (?, ?)", (chat_id, title))
        if rows:
            logger.info(f"Migrated {len(rows)} groups to 'groups' table.")

    # Migration: Add type column to groups if it doesn't exist
    cursor.execute("PRAGMA table_info(groups)")
    group_columns = [column[1] for column in cursor.fetchall()]
    if 'type' not in group_columns:
        cursor.execute("ALTER TABLE groups ADD COLUMN type TEXT DEFAULT 'supergroup'")
        logger.info("Database migration: added 'type' column to groups.")

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

def get_chat_time(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT broadcast_time FROM schedules WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else ''

def set_chat_time(chat_id, time_str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO schedules (chat_id, broadcast_time, file_id, language) 
            VALUES (?, ?, '', 'UZ') 
            ON CONFLICT(chat_id) DO UPDATE SET broadcast_time = EXCLUDED.broadcast_time
        """, (chat_id, time_str))
        conn.commit()
        conn.close()
        logger.info(f"Broadcast time set to {time_str} for chat_id: {chat_id}")
    except Exception as e:
        logger.error(f"Error setting broadcast time for {chat_id}: {e}")
        raise e

def save_schedule(chat_id: int, file_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Check if chat already exists to preserve language and time
        cursor.execute("SELECT language, broadcast_time FROM schedules WHERE chat_id = ?", (chat_id,))
        result = cursor.fetchone()
        lang = result[0] if result else 'UZ'
        time = result[1] if result else ''
        
        cursor.execute("""
            INSERT OR REPLACE INTO schedules (chat_id, file_id, language, broadcast_time)
            VALUES (?, ?, ?, ?)
        """, (chat_id, file_id, lang, time))
        conn.commit()
        conn.close()
        logger.info(f"Schedule saved for chat_id: {chat_id}")
    except Exception as e:
        logger.error(f"Error saving schedule for {chat_id}: {e}")

def delete_schedule(chat_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schedules WHERE chat_id = ?", (chat_id,))
        conn.commit()
        conn.close()
        logger.info(f"Schedule deleted for chat_id: {chat_id}")
    except Exception as e:
        logger.error(f"Error deleting schedule for {chat_id}: {e}")

    except Exception as e:
        logger.error(f"Error deleting schedule for {chat_id}: {e}")

def register_group(chat_id, title="", group_type="supergroup", username=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Update Groups Table (Identity)
        cursor.execute("""
            INSERT OR IGNORE INTO groups (chat_id, title, type, username)
            VALUES (?, ?, ?, ?)
        """, (chat_id, title, group_type, username))
        cursor.execute("UPDATE groups SET title = ?, type = ?, username = ? WHERE chat_id = ?", (title, group_type, username, chat_id))
        
        # 2. Update Schedules Table (Configuration) - ensure entry exists
        cursor.execute("""
            INSERT OR IGNORE INTO schedules (chat_id, file_id, language, broadcast_time, weekend_mode)
            VALUES (?, '', 'UZ', '', 0)
        """, (chat_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"Group registered/updated: {chat_id} - {title}")
    except Exception as e:
        logger.error(f"Error registering group {chat_id}: {e}")

def set_chat_language(chat_id: int, language: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO schedules (chat_id, language, file_id, broadcast_time) 
            VALUES (?, ?, '', '') 
            ON CONFLICT(chat_id) DO UPDATE SET language = EXCLUDED.language
        """, (chat_id, language))
        conn.commit()
        conn.close()
        logger.info(f"Language set to {language} for chat_id: {chat_id}")
    except Exception as e:
        logger.error(f"Error setting language for {chat_id}: {e}")

def get_chat_language(chat_id: int) -> str:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM schedules WHERE chat_id = ?", (chat_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 'UZ'
    except Exception as e:
        logger.error(f"Error fetching language for {chat_id}: {e}")
        return 'UZ'

def get_schedule(chat_id: int):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT file_id FROM schedules WHERE chat_id = ?", (chat_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error fetching schedule for {chat_id}: {e}")
        return None

def get_all_schedules():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id, file_id, language, broadcast_time, weekend_mode FROM schedules WHERE file_id != ''")
        results = cursor.fetchall()
        conn.close()
        logger.info(f"Found {len(results)} active entries in database.")
        return results
    except Exception as e:
        logger.error(f"Error fetching all schedules: {e}")
        return []

def toggle_weekend_mode(chat_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT weekend_mode FROM schedules WHERE chat_id = ?", (chat_id,))
        result = cursor.fetchone()
        current = result[0] if result else 0
        new_val = 1 if current == 0 else 0
        cursor.execute("UPDATE schedules SET weekend_mode = ? WHERE chat_id = ?", (new_val, chat_id))
        conn.commit()
        conn.close()
        return new_val
    except Exception as e:
        logger.error(f"Error toggling weekend mode for {chat_id}: {e}")
        return None

def get_weekend_mode(chat_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT weekend_mode FROM schedules WHERE chat_id = ?", (chat_id,))
        result = cursor.fetchone()
        conn.close()
        return bool(result[0]) if result else False
    except Exception as e:
        logger.error(f"Error getting weekend mode for {chat_id}: {e}")
        return False

def save_user_contact(user_id, phone, first_name, last_name, username):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, phone_number, first_name, last_name, username)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, phone, first_name, last_name, username))
        conn.commit()
        conn.close()
        logger.info(f"User contact saved for user_id: {user_id}")
    except Exception as e:
        logger.error(f"Error saving user contact for {user_id}: {e}")

def get_user(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return None

def get_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM schedules WHERE file_id != ''")
        active_group_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM groups")
        total_group_count = cursor.fetchone()[0]
        
        conn.close()
        return {"users": user_count, "active_groups": active_group_count, "total_groups": total_group_count}
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {"users": 0, "groups": 0}

def count_users():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error counting users: {e}")
        return 0

def get_all_user_ids():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        results = cursor.fetchall()
        conn.close()
        return [r[0] for r in results]
    except Exception as e:
        logger.error(f"Error fetching all user IDs: {e}")
        return []

def get_paginated_users(limit, offset):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, phone_number, username FROM users LIMIT ? OFFSET ?", (limit, offset))
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Error fetching paginated users: {e}")
        return []

def count_groups():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM groups")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error counting groups: {e}")
        return 0

def get_paginated_groups(limit, offset):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Return ID, Title, Type, Username
        cursor.execute("SELECT chat_id, title, type, username FROM groups LIMIT ? OFFSET ?", (limit, offset))
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Error fetching paginated groups: {e}")
        return []


if __name__ == "__main__":
    init_db()
