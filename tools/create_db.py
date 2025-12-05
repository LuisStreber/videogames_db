import os
from models import init_db

os.makedirs('db', exist_ok=True)

init_db()

print("Database initialized successfully.")