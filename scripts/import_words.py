"""
import_words.py

database_icin_kelime/data klasöründeki .txt dosyalarından kelimeleri oku,
SQLite words tablosuna chunked şekilde ekle (INSERT OR IGNORE ile dedup).

Kullanım:
    python scripts/import_words.py
"""

import os
import sqlite3
from pathlib import Path

# Dosya yolları
REPO_DATA_DIR = "database_icin_kelime/data"
DB_PATH = "app.db"
CHUNK_SIZE = 2000


def get_topic_id_map(conn):
    """topics tablosundan {topic_name: topic_id} mapini döndür."""
    cur = conn.cursor()
    cur.execute("SELECT topic_id, topic_name FROM topics")
    return {row[1]: row[0] for row in cur.fetchall()}


def import_words_from_repo():
    """
    Repo dosyalarını oku ve words tablosuna ekle.
    """
    if not os.path.isdir(REPO_DATA_DIR):
        print(f"❌ Repo veri dizini bulunamadı: {REPO_DATA_DIR}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # topic ID mapini al
    topic_map = get_topic_id_map(conn)
    print(f"📚 {len(topic_map)} topic bulundu")

    # .txt dosyalarını işle
    txt_files = sorted([f for f in os.listdir(REPO_DATA_DIR) if f.endswith('.txt')])
    total_imported = 0
    total_skipped = 0

    for fname in txt_files:
        file_path = os.path.join(REPO_DATA_DIR, fname)
        topic_name = os.path.splitext(fname)[0].replace('_', ' ').title()
        topic_id = topic_map.get(topic_name)

        if not topic_id:
            print(f"⚠️  Topic bulunamadı: {topic_name} (dosya: {fname})")
            continue

        # Dosya satırlarını oku
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"❌ {fname} okunurken hata: {e}")
            continue

        # Chunked insert
        for chunk_start in range(0, len(words), CHUNK_SIZE):
            chunk = words[chunk_start : chunk_start + CHUNK_SIZE]
            rows = [(w, None, None, topic_id, None, None, None, None) for w in chunk]

            try:
                cur.executemany(
                    """
                    INSERT OR IGNORE INTO words 
                    (english, turkish, level, topic_id, example_sentence, pronunciation, pos, freq)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows
                )
                chunk_imported = cur.rowcount
                total_imported += chunk_imported
            except Exception as e:
                print(f"❌ {fname} chunk insert hatası: {e}")
                continue

        print(f"✓ {fname}: {len(words)} kelime (eklenen: {min(len(words), chunk_imported or 0)})")

    conn.commit()
    conn.close()

    print(f"\n✅ İmport tamamlandı!")
    print(f"   Toplam eklenen kelime: {total_imported}")


if __name__ == "__main__":
    import_words_from_repo()
