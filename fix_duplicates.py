from db_utils import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

print("Duplicate kayıtları temizleniyor...")

# Duplicate olan unit progress kayıtlarını bul ve sadece birini bırak
cur.execute('''
    DELETE FROM user_course_progress 
    WHERE rowid NOT IN (
        SELECT MIN(rowid) 
        FROM user_course_progress 
        GROUP BY user_id, unit_id, lesson_id
    )
''')

deleted = cur.rowcount
conn.commit()
print(f"✓ {deleted} duplicate kayıt silindi")

# UNIQUE index oluştur (varsa güncelle)
try:
    cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_progress_unique ON user_course_progress(user_id, unit_id, lesson_id)')
    conn.commit()
    print("✓ UNIQUE index eklendi")
except Exception as e:
    print(f"Index hatası (muhtemelen zaten var): {e}")

# Kontrol et
cur.execute('SELECT user_id, unit_id, lesson_id, COUNT(*) as cnt FROM user_course_progress GROUP BY user_id, unit_id, lesson_id HAVING cnt > 1')
remaining = cur.fetchall()
print(f"Kalan duplicate: {len(remaining)}")

conn.close()
print("Temizlik tamamlandı!")
