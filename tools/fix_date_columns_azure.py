from connection import get_sqlserver_connection

def fix_date_columns():
    conn = get_sqlserver_connection()
    cursor = conn.connection.cursor()  # Cursor real de pyodbc
    
    print("=" * 60)
    print("CAMBIANDO RELEASE_DATE DE INT A DATE EN AZURE SQL")
    print("=" * 60)
    
    try:
        # ===== TABLA GAMES =====
        print("\n🎮 MODIFICANDO TABLA GAMES...")
        
        # 1. Agregar nueva columna DATE
        print("   1️⃣  Agregando columna release_date_new (DATE)...")
        cursor.execute("ALTER TABLE games ADD release_date_new DATE NULL")
        conn.commit()
        
        # 2. Convertir datos existentes (año INT → fecha '2004-01-01')
        print("   2️⃣  Convirtiendo datos existentes...")
        cursor.execute("""
            UPDATE games 
            SET release_date_new = DATEFROMPARTS(release_date, 1, 1)
            WHERE release_date IS NOT NULL
        """)
        conn.commit()
        
        # 3. Eliminar columna vieja
        print("   3️⃣  Eliminando columna vieja...")
        cursor.execute("ALTER TABLE games DROP COLUMN release_date")
        conn.commit()
        
        # 4. Renombrar columna nueva
        print("   4️⃣  Renombrando columna nueva...")
        cursor.execute("EXEC sp_rename 'games.release_date_new', 'release_date', 'COLUMN'")
        conn.commit()
        
        print("   ✅ Tabla games actualizada correctamente")
        
        # ===== TABLA CONSOLES =====
        print("\n🕹️  MODIFICANDO TABLA CONSOLES...")
        
        # 1. Agregar nueva columna DATE
        print("   1️⃣  Agregando columna release_date_new (DATE)...")
        cursor.execute("ALTER TABLE consoles ADD release_date_new DATE NULL")
        conn.commit()
        
        # 2. Convertir datos existentes
        print("   2️⃣  Convirtiendo datos existentes...")
        cursor.execute("""
            UPDATE consoles 
            SET release_date_new = DATEFROMPARTS(release_date, 1, 1)
            WHERE release_date IS NOT NULL
        """)
        conn.commit()
        
        # 3. Eliminar columna vieja
        print("   3️⃣  Eliminando columna vieja...")
        cursor.execute("ALTER TABLE consoles DROP COLUMN release_date")
        conn.commit()
        
        # 4. Renombrar columna nueva
        print("   4️⃣  Renombrando columna nueva...")
        cursor.execute("EXEC sp_rename 'consoles.release_date_new', 'release_date', 'COLUMN'")
        conn.commit()
        
        print("   ✅ Tabla consoles actualizada correctamente")
        
        # ===== VERIFICACIÓN =====
        print("\n" + "=" * 60)
        print("📊 VERIFICANDO CAMBIOS...")
        print("=" * 60)
        
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'games' AND COLUMN_NAME = 'release_date'
        """)
        result = cursor.fetchone()
        print(f"\n✅ games.release_date → Tipo: {result[1]}")
        
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'consoles' AND COLUMN_NAME = 'release_date'
        """)
        result = cursor.fetchone()
        print(f"✅ consoles.release_date → Tipo: {result[1]}")
        
        # Mostrar un ejemplo
        cursor.execute("SELECT TOP 1 title, release_date FROM games WHERE release_date IS NOT NULL")
        game = cursor.fetchone()
        if game:
            print(f"\n📅 Ejemplo: {game[0]} → {game[1]}")
        
        print("\n" + "=" * 60)
        print("✅ CAMBIO COMPLETADO EXITOSAMENTE!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    confirm = input("\n⚠️  Esto modificará las columnas release_date. ¿Continuar? (si/no): ")
    if confirm.lower() == 'si':
        fix_date_columns()
    else:
        print("❌ Operación cancelada.")