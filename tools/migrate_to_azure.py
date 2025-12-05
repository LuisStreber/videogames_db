import sqlite3
import os
from dotenv import load_dotenv
from connection import get_db_connection, get_sqlserver_connection

load_dotenv()

def extract_year(date_value):
    """Extrae el año de una fecha en formato string o retorna el valor si ya es int"""
    if date_value is None:
        return None
    
    # Si ya es un entero, retornarlo
    if isinstance(date_value, int):
        return date_value
    
    # Si es string, extraer el año
    if isinstance(date_value, str):
        # Formatos posibles: '2004-10-04', '2004', etc.
        year_str = date_value.split('-')[0].strip()
        try:
            return int(year_str)
        except:
            return None
    
    return None

def migrate_data():
    print("=" * 60)
    print("MIGRACIÓN DE DATOS: SQLite → Azure SQL Server")
    print("=" * 60)
    
    # Conectar a SQLite
    print("\n📂 Conectando a SQLite...")
    sqlite_conn = get_db_connection()
    sqlite_cursor = sqlite_conn.cursor()
    
    # Conectar a Azure SQL
    print("🔵 Conectando a Azure SQL...")
    azure_conn = get_sqlserver_connection()
    azure_cursor = azure_conn.cursor()
    
    try:
        # MIGRAR USUARIOS
        print("\n" + "=" * 60)
        print("👥 MIGRANDO USUARIOS...")
        print("=" * 60)
        
        users = sqlite_cursor.execute("SELECT id, username, password_hash FROM users").fetchall()
        print(f"   Encontrados: {len(users)} usuarios")
        
        migrated_users = 0
        
        # Habilitar IDENTITY_INSERT para usuarios
        azure_cursor.execute("SET IDENTITY_INSERT users ON")
        
        for user in users:
            try:
                azure_cursor.execute(
                    "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
                    (user[0], user[1], user[2])
                )
                migrated_users += 1
                print(f"   ✅ Usuario migrado: {user[1]}")
            except Exception as e:
                if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                    print(f"   ⚠️  Usuario ya existe: {user[1]} (omitido)")
                else:
                    print(f"   ❌ Error migrando usuario {user[1]}: {e}")
        
        # Deshabilitar IDENTITY_INSERT
        azure_cursor.execute("SET IDENTITY_INSERT users OFF")
        azure_conn.commit()
        print(f"\n✅ Usuarios migrados: {migrated_users}/{len(users)}")
        
        # MIGRAR CONSOLAS
        print("\n" + "=" * 60)
        print("🎮 MIGRANDO CONSOLAS...")
        print("=" * 60)
        
        consoles = sqlite_cursor.execute("""
            SELECT id, name, model, model_normalized, release_date, manufacturer,
                   serial_number_box, serial_number_console, complete_in_box,
                   condition, inventory, sealed
            FROM consoles
        """).fetchall()
        print(f"   Encontradas: {len(consoles)} consolas")
        
        migrated_consoles = 0
        
        if len(consoles) > 0:
            # Habilitar IDENTITY_INSERT para consolas
            azure_cursor.execute("SET IDENTITY_INSERT consoles ON")
            
            for console in consoles:
                try:
                    # Convertir release_date a año (int)
                    release_year = extract_year(console[4])
                    
                    azure_cursor.execute("""
                        INSERT INTO consoles (
                            id, name, model, model_normalized, release_date, manufacturer,
                            serial_number_box, serial_number_console, complete_in_box,
                            condition, inventory, sealed
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (console[0], console[1], console[2], console[3], release_year, console[5],
                          console[6], console[7], console[8], console[9], console[10], console[11]))
                    migrated_consoles += 1
                    print(f"   ✅ Consola migrada: {console[1]} - {console[2]}")
                except Exception as e:
                    if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                        print(f"   ⚠️  Consola ya existe: {console[1]} (omitida)")
                    else:
                        print(f"   ❌ Error migrando consola {console[1]}: {e}")
            
            # Deshabilitar IDENTITY_INSERT
            azure_cursor.execute("SET IDENTITY_INSERT consoles OFF")
            azure_conn.commit()
        
        print(f"\n✅ Consolas migradas: {migrated_consoles}/{len(consoles)}")
        
        # MIGRAR JUEGOS
        print("\n" + "=" * 60)
        print("🕹️  MIGRANDO JUEGOS...")
        print("=" * 60)
        
        games = sqlite_cursor.execute("""
            SELECT id, title, release_date, manufacturer, description, genre,
                   platform, platform_normalized, score, complete_in_box,
                   condition, inventory, sealed
            FROM games
        """).fetchall()
        print(f"   Encontrados: {len(games)} juegos")
        
        migrated_games = 0
        
        if len(games) > 0:
            # Habilitar IDENTITY_INSERT para juegos
            azure_cursor.execute("SET IDENTITY_INSERT games ON")
            
            for game in games:
                try:
                    # Convertir release_date a año (int)
                    release_year = extract_year(game[2])
                    
                    azure_cursor.execute("""
                        INSERT INTO games (
                            id, title, release_date, manufacturer, description, genre,
                            platform, platform_normalized, score, complete_in_box,
                            condition, inventory, sealed
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (game[0], game[1], release_year, game[3], game[4], game[5], 
                          game[6], game[7], game[8], game[9], game[10], game[11], game[12]))
                    migrated_games += 1
                    print(f"   ✅ Juego migrado: {game[1]} (año: {release_year})")
                except Exception as e:
                    if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                        print(f"   ⚠️  Juego ya existe: {game[1]} (omitido)")
                    else:
                        print(f"   ❌ Error migrando juego {game[1]}: {e}")
            
            # Deshabilitar IDENTITY_INSERT
            azure_cursor.execute("SET IDENTITY_INSERT games OFF")
            azure_conn.commit()
        
        print(f"\n✅ Juegos migrados: {migrated_games}/{len(games)}")
        
        # RESUMEN FINAL
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE MIGRACIÓN")
        print("=" * 60)
        print(f"   Usuarios: {migrated_users}/{len(users)}")
        print(f"   Consolas: {migrated_consoles}/{len(consoles)}")
        print(f"   Juegos:   {migrated_games}/{len(games)}")
        print("\n✅ MIGRACIÓN COMPLETADA!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR DURANTE LA MIGRACIÓN: {e}")
        azure_conn.rollback()
    finally:
        sqlite_cursor.close()
        sqlite_conn.close()
        azure_cursor.close()
        azure_conn.close()

if __name__ == "__main__":
    confirm = input("\n⚠️  ¿Estás seguro de migrar los datos a Azure SQL? (si/no): ")
    if confirm.lower() == 'si':
        migrate_data()
    else:
        print("❌ Migración cancelada.")