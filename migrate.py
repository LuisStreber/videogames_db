import sqlite3

conn = sqlite3.connect('videogames.db')
with open('backup_sqlite3.sql', 'w') as f:
    for line in conn.iterdump():
        f.write(f'{line}\n')
conn.close()