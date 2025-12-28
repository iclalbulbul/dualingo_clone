"""
assign_cefr_levels.py

Kelimelere CEFR seviyeleri atayıcı.

Strateji: wordfreq.zipf_frequency() kullan:
- zipf > 4.0  → A1 (çok yaygın)
- 3.5-4.0     → A2
- 3.0-3.5     → B1
- 2.5-3.0     → B2
- 2.0-2.5     → C1
- < 2.0       → C2 (nadir)

Kullanım:
    pip install wordfreq
    python scripts/assign_cefr_levels.py
"""

import sqlite3
import sys

try:
    from wordfreq import zipf_frequency
except ImportError:
    print("❌ wordfreq yüklü değil. Yüklüyorum...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "wordfreq"])
    from wordfreq import zipf_frequency

DB_PATH = "app.db"
BATCH_SIZE = 500


def get_cefr_level(word):
    """Kelimeye CEFR seviyesi ata."""
    try:
        freq = zipf_frequency(word, 'en')
        if freq > 4.0:
            return 'A1'
        elif freq > 3.5:
            return 'A2'
        elif freq > 3.0:
            return 'B1'
        elif freq > 2.5:
            return 'B2'
        elif freq > 2.0:
            return 'C1'
        else:
            return 'C2'
    except:
        # Hata varsa C1 atanır (orta-üst seviye)
        return 'C1'


def assign_levels():
    """Tüm kelimelere seviye atanır."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Seviye olmayan kelimeleri al
    cur.execute("SELECT word_id, english FROM words WHERE level IS NULL LIMIT ?", (BATCH_SIZE,))
    batch = cur.fetchall()

    total_updated = 0
    while batch:
        updates = []
        for word_id, english in batch:
            level = get_cefr_level(english)
            updates.append((level, word_id))

        # Batch update
        try:
            cur.executemany("UPDATE words SET level = ? WHERE word_id = ?", updates)
            conn.commit()
            total_updated += len(updates)
            print(f"✓ {total_updated} kelimeye seviye atandı...")
        except Exception as e:
            print(f"❌ Update hatası: {e}")
            conn.rollback()
            break

        # Sonraki batch
        cur.execute("SELECT word_id, english FROM words WHERE level IS NULL LIMIT ?", (BATCH_SIZE,))
        batch = cur.fetchall()

    conn.close()
    print(f"\n✅ Seviye atanması tamamlandı!")
    print(f"   Toplam güncellenen kelime: {total_updated}")


if __name__ == "__main__":
    assign_levels()
