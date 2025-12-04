import bcrypt
import sqlite3
from connection import get_db_connection

def create_user(username, password):
    conn = get_db_connection()
    try:
        existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            print(f"Error: User '{username}' already exists.")
            return False
        
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        print(f"User {username} created successfully.")
        return True
    except sqlite3.Error as e:
        print(f"Error creating user: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    create_user("admin", "admin1234")
