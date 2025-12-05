from connection import get_sqlserver_connection

def check_schema():
    conn = get_sqlserver_connection()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("ESTRUCTURA DE TABLA 'games' EN AZURE SQL")
    print("=" * 60)
    
    cursor.execute("""
        SELECT 
            COLUMN_NAME, 
            DATA_TYPE, 
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'games'
        ORDER BY ORDINAL_POSITION
    """)
    
    columns = cursor.fetchall()
    for col in columns:
        length = f"({col[2]})" if col[2] else ""
        print(f"{col[0]:25} {col[1]}{length:15} NULL: {col[3]}")
    
    print("\n" + "=" * 60)
    print("ESTRUCTURA DE TABLA 'consoles' EN AZURE SQL")
    print("=" * 60)
    
    cursor.execute("""
        SELECT 
            COLUMN_NAME, 
            DATA_TYPE, 
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'consoles'
        ORDER BY ORDINAL_POSITION
    """)
    
    columns = cursor.fetchall()
    for col in columns:
        length = f"({col[2]})" if col[2] else ""
        print(f"{col[0]:25} {col[1]}{length:15} NULL: {col[3]}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_schema()