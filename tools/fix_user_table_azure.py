from connection import get_sqlserver_connection
import bcrypt

def fix_users_table():
    conn = get_sqlserver_connection()
    cursor = conn.connection.cursor()  # Usar cursor real de pyodbc
    
    print("=" * 60)
    print("ARREGLANDO TABLA USERS EN AZURE SQL")
    print("=" * 60)
    
    try:
        # 1. Crear tabla temporal con estructura correcta
        print("\n1️⃣  Creando tabla temporal...")
        cursor.execute("""
            CREATE TABLE users_new (
                id INT PRIMARY KEY IDENTITY(1,1),
                username NVARCHAR(255) NOT NULL UNIQUE,
                password_hash VARBINARY(255) NOT NULL
            )
        """)
        conn.commit()
        print("   ✅ Tabla temporal creada")
        
        # 2. Eliminar tabla vieja
        print("\n2️⃣  Eliminando tabla users antigua...")
        cursor.execute("DROP TABLE users")
        conn.commit()
        print("   ✅ Tabla antigua eliminada")
        
        # 3. Renombrar tabla nueva
        print("\n3️⃣  Renombrando tabla temporal...")
        cursor.execute("EXEC sp_rename 'users_new', 'users'")
        conn.commit()
        print("   ✅ Tabla renombrada")
        
        # 4. Crear usuario admin con hash correcto
        print("\n4️⃣  Creando usuario admin con hash correcto...")
        password = "admin123"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("admin", password_hash)
        )
        conn.commit()
        print("   ✅ Usuario admin creado correctamente")
        
        # 5. Verificar
        print("\n5️⃣  Verificando...")
        cursor.execute("SELECT id, username, LEN(password_hash) as hash_length FROM users")
        users = cursor.fetchall()
        
        for user in users:
            print(f"   Usuario: {user[1]}")
            print(f"   ID: {user[0]}")
            print(f"   Hash length: {user[2]} bytes")
        
        print("\n" + "=" * 60)
        print("✅ TABLA USERS ARREGLADA CORRECTAMENTE!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    confirm = input("\n⚠️  Esto eliminará y recreará la tabla users. ¿Continuar? (si/no): ")
    if confirm.lower() == 'si':
        fix_users_table()
    else:
        print("❌ Operación cancelada.")