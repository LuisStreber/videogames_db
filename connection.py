import os
import sqlite3
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """
    Establece conexión con la base de datos SQLite.
    Retorna una conexión con Row factory para acceso por nombre de columna.
    """
    database_path = os.getenv('DATABASE_PATH', 'db/videogames.db')

    try:
        connection = sqlite3.connect(database_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
        return connection
    except sqlite3.Error as e:
        print(f"Error connecting to the SQLite database: {e}")
        raise

class DictCursor:
    """Wrapper para pyodbc cursor que retorna diccionarios"""
    def __init__(self, cursor):
        self.cursor = cursor
        self._last_description = None

    def execute(self, query, params=None):
        if params is None:
            params = ()
        # pyodbc acepta tuplas/listas; sqlite3 también en su API cursors
        self.cursor.execute(query, params)
        # Guardar descripción para fetch
        self._last_description = self.cursor.description
        return self  # permite chaining: conn.execute(...).fetchone()

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        if not self._last_description:
            # si no hay descripción, devolver tuple
            return row
        columns = [column[0] for column in self._last_description]
        return dict(zip(columns, row))

    def fetchall(self):
        rows = self.cursor.fetchall()
        if not rows:
            return []
        if not self._last_description:
            return rows
        columns = [column[0] for column in self._last_description]
        return [dict(zip(columns, row)) for row in rows]

    def close(self):
        try:
            self.cursor.close()
        except Exception:
            pass

class DictConnection:
    """Wrapper para pyodbc connection que usa DictCursor"""
    def __init__(self, connection):
        self.connection = connection
        self._cursor = None

    def execute(self, query, params=None):
        # Crear un cursor nuevo y ejecutar; almacenar como _cursor para close()
        cur = self.connection.cursor()
        dict_cur = DictCursor(cur)
        dict_cur.execute(query, params)
        # almacenar el cursor activo (para close() posterior)
        self._cursor = dict_cur
        return dict_cur

    def cursor(self):
        return DictCursor(self.connection.cursor())

    def commit(self):
        try:
            self.connection.commit()
        except Exception:
            pass

    def rollback(self):
        try:
            self.connection.rollback()
        except Exception:
            pass

    def close(self):
        try:
            if self._cursor:
                self._cursor.close()
            self.connection.close()
        except Exception:
            pass

    # Soporte para uso con "with"
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                self.rollback()
        finally:
            self.close()

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
        raise ValueError("Azure SQL Server credentials are not configuradas en .env")

    conn_str = (
        f'DRIVER={driver};SERVER={server};DATABASE={database};'
        f'UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30'
    )

    try:
        connection = pyodbc.connect(conn_str, autocommit=False)
        return DictConnection(connection)
    except pyodbc.Error as e:
        print(f"Error connecting to Azure SQL Server: {e}")
        raise

if __name__ == "__main__":
    conn = get_db_connection()
    print("SQLite connection successful!")
    conn.close()
