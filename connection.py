import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():

    database_path = os.getenv('DATABASE_PATH', 'db/videogames.db')

    try:
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        return connection
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        raise

def get_sqlserver_connection():

    import pyodbc

    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DATABASE')
    username = os.getenv('AZURE_SQL_USER')
    password = os.getenv('AZURE_SQL_PASSWORD')
    driver = '{ODBC Driver 18 for SQL Server}'

    if not all ([server, database, username, password]):
        raise ValueError("Azure SQL Server credentials are not configured in .env file")

    conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    
    try:
        connection = pyodbc.connect(conn_str)
        return connection
    except pyodbc.Error as e:
        print(f"Error connecting to the database: {e}")
        raise

if __name__ == "__main__":
    conn = get_db_connection()
    print("SQLite connection succesful!")
    conn.close()