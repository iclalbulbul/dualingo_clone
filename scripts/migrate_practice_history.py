"""
Database migration: practice_history'ye word_id ve attempted_answer ekle
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "app.db"

def migrate_practice_history():
    """practice_history tablosuna eksik kolonları ekle."""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Kontrol et: word_id var mı?
        cursor.execute("PRAGMA table_info(practice_history)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print("Current columns in practice_history:")
        for col in columns:
            print(f"  - {col}")
        
        # Eksik kolonları ekle
        if "word_id" not in columns:
            print("\n  Adding word_id column...")
            cursor.execute("ALTER TABLE practice_history ADD COLUMN word_id INTEGER")
        
        if "is_correct" not in columns:
            print("  Adding is_correct column...")
            cursor.execute("ALTER TABLE practice_history ADD COLUMN is_correct INTEGER DEFAULT 0")
        
        if "attempted_answer" not in columns:
            print("  Adding attempted_answer column...")
            cursor.execute("ALTER TABLE practice_history ADD COLUMN attempted_answer TEXT")
        
        conn.commit()
        print("\n✅ Migration tamamlandı!")
        
        # Kontrol et
        cursor.execute("PRAGMA table_info(practice_history)")
        columns = [col[1] for col in cursor.fetchall()]
        print("\nNew columns:")
        for col in columns:
            print(f"  - {col}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_practice_history()
