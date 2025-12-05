import os
import sqlite3
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """
    Establece conexión con la base de datos SQLite.
    Retorna una conexión con Row factory para acceso por nombre de columna.
    """
    database_path = os.getenv('DATABASE_PATH', 'db/videogames.db')
    
    try:
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
        return connection
    except sqlite3.Error as e:
        print(f"Error connecting to the database: {e}")
        raise

class DictCursor:
    """Wrapper para pyodbc cursor que retorna diccionarios"""
    def __init__(self, cursor):
        self.cursor = cursor
    
    def execute(self, query, params=()):
        return self.cursor.execute(query, params)
    
    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        columns = [column[0] for column in self.cursor.description]
        return dict(zip(columns, row))
    
    def fetchall(self):
        rows = self.cursor.fetchall()
        if not rows:
            return []
        columns = [column[0] for column in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    
    def close(self):
        self.cursor.close()

class DictConnection:
    """Wrapper para pyodbc connection que usa DictCursor"""
    def __init__(self, connection):
        self.connection = connection
        self._cursor = None
    
    def execute(self, query, params=()):
        """Ejecuta query directamente (compatibilidad con SQLite)"""
        if self._cursor is None:
            self._cursor = DictCursor(self.connection.cursor())
        self._cursor.execute(query, params)
        return self._cursor
    
    def cursor(self):
        """Retorna un DictCursor"""
        return DictCursor(self.connection.cursor())
    
    def commit(self):
        self.connection.commit()
    
    def rollback(self):
        self.connection.rollback()
    
    def close(self):
        if self._cursor:
            self._cursor.close()
        self.connection.close()

def get_sqlserver_connection():
    """
    Conexión a Azure SQL Server con soporte para acceso por nombre de columna.
    """
    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DATABASE')
    username = os.getenv('AZURE_SQL_USER')
    password = os.getenv('AZURE_SQL_PASSWORD')
    driver = '{ODBC Driver 18 for SQL Server}'

    if not all([server, database, username, password]):
        raise ValueError("Azure SQL Server credentials are not configured in .env file")

    conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30'
    
    try:
        connection = pyodbc.connect(conn_str)
        # Envolver la conexión para que retorne diccionarios
        return DictConnection(connection)
    except pyodbc.Error as e:
        print(f"Error connecting to Azure SQL Server: {e}")
        raise

# Example usage (optional)
if __name__ == "__main__":
    conn = get_db_connection()
    print("SQLite connection successful!")
    conn.close()