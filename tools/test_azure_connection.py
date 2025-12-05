import os
from dotenv import load_dotenv
from connection import get_sqlserver_connection

# Cargar variables de entorno
load_dotenv()

def test_connection():
    print("=" * 50)
    print("PROBANDO CONEXIÓN A AZURE SQL SERVER")
    print("=" * 50)
    
    # Verificar variables de entorno
    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DATABASE')
    username = os.getenv('AZURE_SQL_USER')
    password = os.getenv('AZURE_SQL_PASSWORD')
    
    print(f"\nServer: {server}")
    print(f"Database: {database}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password) if password else 'NO CONFIGURADO'}")
    print("\n" + "=" * 50)
    
    if not all([server, database, username, password]):
        print("❌ ERROR: Faltan credenciales en el archivo .env")
        return False
    
    try:
        print("\n🔄 Intentando conectar a Azure SQL...")
        conn = get_sqlserver_connection()
        print("✅ ¡CONEXIÓN EXITOSA!")
        
        # Probar una consulta simple
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()
        print(f"\n📊 Versión de SQL Server:\n{version[0][:100]}...")
        
        # Verificar tablas
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables = cursor.fetchall()
        
        print(f"\n📋 Tablas encontradas ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        print("\n✅ Prueba completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR al conectar:")
        print(f"   {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()