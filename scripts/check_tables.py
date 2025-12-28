import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("Mevcut tablolar:")
for t in tables:
    print(f"  - {t[0]}")

conn.close()
