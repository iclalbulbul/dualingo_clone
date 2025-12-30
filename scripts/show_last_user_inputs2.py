import os
import sqlite3

# Scriptin bulunduğu klasöre göre app.db yolunu bul
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
db_path = os.path.join(parent_dir, "app.db")

print(f"Veritabanı yolu: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT input_id, user_id, input_type, input_text, is_correct, word_id, timestamp FROM user_inputs ORDER BY input_id DESC LIMIT 10")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
