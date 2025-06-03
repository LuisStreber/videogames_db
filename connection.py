import pyodbc

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=nombre-servidor.database.windows.net;'
    'DATABASE=nombre-base-datos;'
    'UID=luiss;'
    'PWD=12345'
)
