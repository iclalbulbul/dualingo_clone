"""
Migration helper: ensures `mistakes` tablosu ve index'i veritabanında bulunur.
Çalıştırma: python scripts/migrate_mistakes.py
"""
from db_utils import get_db_connection

DDL = """
CREATE TABLE IF NOT EXISTS mistakes (
    mistake_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_key TEXT NOT NULL,
    lesson_id TEXT,
    context TEXT,
    wrong_answer TEXT,
    correct_answer TEXT,
    count INTEGER DEFAULT 1,
    repetition INTEGER DEFAULT 0,
    interval INTEGER DEFAULT 0,
    easiness REAL DEFAULT 2.5,
    next_review TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""

INDEX = """
CREATE INDEX IF NOT EXISTS idx_mistakes_user_next ON mistakes (user_id, next_review);
"""


def migrate():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.executescript(DDL + "\n" + INDEX)
    conn.commit()
    conn.close()
    print("✓ migration: mistakes table ensured")


if __name__ == '__main__':
    migrate()
