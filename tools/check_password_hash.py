from connection import get_sqlserver_connection

conn = get_sqlserver_connection()
cursor = conn.cursor()

cursor.execute("SELECT id, username, password_hash, LEN(password_hash) as hash_length FROM users")
users = cursor.fetchall()

for user in users:
    print(f"Usuario: {user['username']}")
    print(f"ID: {user['id']}")
    print(f"Hash length: {user['hash_length']}")
    print(f"Hash type: {type(user['password_hash'])}")
    print(f"Hash (primeros 50 chars): {str(user['password_hash'])[:50]}")
    print(f"Hash bytes (repr): {repr(user['password_hash'][:30])}")
    print("-" * 60)

conn.close()