import sqlite3

def init_db():
    conn = sqlite3.connect('db/videogames.db')
    c = conn.cursor()


    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              password_hash TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS consoles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            model TEXT NOT NULL,
            model_normalized TEXT,
            release_date INTEGER,
            manufacturer TEXT NOT NULL,
            serial_number_box TEXT,
            serial_number_console TEXT,
            complete_in_box BOOLEAN,
            condition TEXT,
            inventory INTEGER,
            sealed INTEGER
        )
    ''')
            
    c.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            release_date INTEGER,
            manufacturer TEXT NOT NULL,
            description TEXT,
            genre TEXT,
            platform TEXT,
            platform_normalized TEXT,
            score INTEGER,
            complete_in_box BOOLEAN,
            condition TEXT,
            inventory INTEGER,
            sealed INTEGER
        )
    ''')

    c.execute('CREATE INDEX IF NOT EXISTS idx_games_platform ON games(platform)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_consoles_model ON consoles(model)')

    #NORMALIZING DATA
    c.execute("UPDATE games SET platform_normalized = REPLACE(LOWER(platform), ' ', '') WHERE platform_normalized IS NULL")
    c.execute("UPDATE consoles SET model_normalized = REPLACE(LOWER(model), ' ', '') WHERE model_normalized IS NULL")
    
    conn.commit()
    conn.close()

