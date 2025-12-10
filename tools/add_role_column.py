from connection import get_sqlserver_connection

def add_role_column():
    conn = get_sqlserver_connection()
    cursor = conn.connection.cursor()
    
    print("=" * 60)
    print("AGREGANDO COLUMNA 'role' A TABLA USERS")
    print("=" * 60)
    
    try:
        # 1. Verificar si la columna ya existe
        print("\n1️⃣  Verificando si columna 'role' existe...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'role'
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            print("   ⚠️  La columna 'role' ya existe. Saltando...")
        else:
            # 2. Agregar columna role
            print("   📝 Agregando columna 'role'...")
            cursor.execute("""
                ALTER TABLE users 
                ADD role NVARCHAR(50) NOT NULL DEFAULT 'viewer'
            """)
            conn.commit()
            print("   ✅ Columna 'role' agregada")
        
        # 3. Actualizar usuario admin existente
        print("\n2️⃣  Actualizando rol del usuario 'admin' a 'admin'...")
        cursor.execute("""
            UPDATE users 
            SET role = 'admin' 
            WHERE username = 'admin'
        """)
        conn.commit()
        print("   ✅ Usuario admin actualizado")
        
        # 4. Verificar
        print("\n3️⃣  Verificando usuarios y roles...")
        cursor.execute("SELECT id, username, role FROM users")
        users = cursor.fetchall()
        
        print("\n   Usuarios en la base de datos:")
        for user in users:
            print(f"   - ID: {user[0]}, Username: {user[1]}, Role: {user[2]}")
        
        print("\n" + "=" * 60)
        print("✅ COLUMNA 'role' AGREGADA CORRECTAMENTE!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_role_column()