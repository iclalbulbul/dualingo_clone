import sqlite3
from db_utils import DB_PATH

# Son 10 user_inputs kaydını gösterir
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT input_id, user_id, input_type, input_text, is_correct, word_id, timestamp FROM user_inputs ORDER BY input_id DESC LIMIT 10")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
