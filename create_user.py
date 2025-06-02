import sqlite3
import bcrypt

conn = sqlite3.connect('db/videogames.db')
cursor = conn.cursor()

# Asegúrate de tener esta tabla con password_hash
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
''')

# Sustituye por el nombre y contraseña que deseas
username = 'admin'
password = '1234'

# Hash the password
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

try:
    cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
    conn.commit()
    print(f'Usuario "{username}" Created successfully with hash password.')
except sqlite3.IntegrityError:
    print(f'El usuario "{username}" Already exist. Consider updating hash password.')

conn.close()
