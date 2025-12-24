"""
Database Utilities – SQLite Veritabanı Yönetimi

Tablolar:
- users: Kullanıcı bilgileri (user_id, username, level, created_at)
- grammar_errors: Tespit edilen grammar hataları (error_id, user_id, sentence, error_type, timestamp)
- practice_history: Pratik geçmişi (id, user_id, practice_type, score, timestamp)
"""

import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "app.db"

# ========= SCHEMA INITIALIZATION =========

def init_db():
    """
    Veritabanını başlatır ve tabloları oluşturur (varsa atlar).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # users tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            level TEXT DEFAULT 'A1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    # grammar_errors tablosu - Grammar hatalarını kaydeder
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grammar_errors (
            error_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sentence TEXT NOT NULL,
            error_type TEXT NOT NULL,  -- 'capital_letter', 'punctuation', 'subject_verb_agreement' vb.
            error_message TEXT,
            suggestion TEXT,
            score REAL,  -- 0-100
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # practice_history tablosu - Pratik geçmişi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS practice_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            practice_type TEXT NOT NULL,  -- 'word', 'sentence', 'pronunciation'
            score REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✓ Veritabanı başlatıldı: " + DB_PATH)


# ========= USER MANAGEMENT =========

def get_or_create_user(username: str) -> int:
    """
    Kullanıcıyı veritabanında bulur veya oluşturur.
    user_id döndürür.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Önce bak
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    
    if result:
        user_id = result[0]
        # son giriş zamanını güncelle
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return user_id
    
    # Yoksa oluştur
    cursor.execute(
        "INSERT INTO users (username, level, created_at, last_login) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
        (username, 'A1')
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    
    return user_id


def get_user_level(user_id: int) -> str:
    """Kullanıcının seviyesini döndürür."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT level FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 'A1'


# ========= ERROR LOGGING =========

def log_grammar_error(user_id: int, sentence: str, error_type: str, error_message: str, suggestion: str = None, score: float = 0):
    """
    Grammar hatasını veritabanında kaydeder.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO grammar_errors 
        (user_id, sentence, error_type, error_message, suggestion, score, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, sentence, error_type, error_message, suggestion, score))
    
    conn.commit()
    conn.close()


def log_all_grammar_errors(user_id: int, sentence: str, errors: list, score: float):
    """
    Bir cümleyle ilgili tüm hataları kaydeder.
    errors: analyze_sentence() tarafından döndürülen hata listesi
    """
    for error in errors:
        log_grammar_error(
            user_id=user_id,
            sentence=sentence,
            error_type=error.get('rule', 'unknown'),
            error_message=error.get('message_tr', ''),
            suggestion=None,
            score=score
        )


# ========= ERROR RETRIEVAL =========

def get_user_errors(user_id: int, limit: int = 50) -> list:
    """
    Kullanıcının son hataları döndürür.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT error_id, sentence, error_type, error_message, suggestion, score, timestamp
        FROM grammar_errors
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_error_summary(user_id: int) -> dict:
    """
    Kullanıcının hata özetini döndürür.
    {
        'total_errors': int,
        'error_types': {'capital_letter': 5, 'punctuation': 3, ...},
        'average_score': float,
        'recent_errors': list
    }
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Toplam hata sayısı
    cursor.execute("SELECT COUNT(*) FROM grammar_errors WHERE user_id = ?", (user_id,))
    total_errors = cursor.fetchone()[0]
    
    # Hata türlerinin dağılımı
    cursor.execute("""
        SELECT error_type, COUNT(*) as count
        FROM grammar_errors
        WHERE user_id = ?
        GROUP BY error_type
        ORDER BY count DESC
    """, (user_id,))
    
    error_types = {row['error_type']: row['count'] for row in cursor.fetchall()}
    
    # Ortalama skor
    cursor.execute("SELECT AVG(score) FROM grammar_errors WHERE user_id = ?", (user_id,))
    average_score = cursor.fetchone()[0] or 0
    
    # Son 10 hata
    cursor.execute("""
        SELECT sentence, error_type, error_message, score, timestamp
        FROM grammar_errors
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    """, (user_id,))
    
    recent_errors = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'total_errors': total_errors,
        'error_types': error_types,
        'average_score': round(average_score, 2),
        'recent_errors': recent_errors,
        'weak_areas': list(sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:3])  # En sık 3 hata
    }


# ========= PRACTICE HISTORY =========

def log_practice(user_id: int, practice_type: str, score: float):
    """
    Pratik oturumunu kaydeder.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO practice_history (user_id, practice_type, score, timestamp)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, practice_type, score))
    
    conn.commit()
    conn.close()


def get_practice_stats(user_id: int) -> dict:
    """
    Kullanıcının pratik istatistiklerini döndürür.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # İstatistikler
    cursor.execute("""
        SELECT 
            practice_type,
            COUNT(*) as total,
            AVG(score) as avg_score,
            MAX(score) as best_score
        FROM practice_history
        WHERE user_id = ?
        GROUP BY practice_type
    """, (user_id,))
    
    stats = {}
    for row in cursor.fetchall():
        practice_type, total, avg_score, best_score = row
        stats[practice_type] = {
            'total': total,
            'avg_score': round(avg_score, 2) if avg_score else 0,
            'best_score': best_score or 0
        }
    
    conn.close()
    return stats


# ========= DATABASE CLEANUP =========

def clear_old_errors(user_id: int, days: int = 30):
    """
    30 günden eski hataları siler (opsiyonel).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM grammar_errors
        WHERE user_id = ? AND timestamp < datetime('now', '-' || ? || ' days')
    """, (user_id, days))
    
    conn.commit()
    conn.close()


def reset_user_data(user_id: int):
    """
    Kullanıcının tüm hata verilerini siler (testing için).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM grammar_errors WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM practice_history WHERE user_id = ?", (user_id,))
    
    conn.commit()
    conn.close()


# ========= DEMO / TEST =========

if __name__ == "__main__":
    init_db()
    
    # Test
    user_id = get_or_create_user("test_user_1")
    print(f"✓ Kullanıcı ID: {user_id}")
    
    # Örnek hatalar ekle
    log_grammar_error(user_id, "she go to school.", "subject_verb_agreement", 
                      "Özne 'she' tekil olduğu için 'go' yerine 'goes' kullanılmalı", 
                      "She goes to school.", 75)
    
    log_grammar_error(user_id, "they goes to school.", "subject_verb_agreement",
                      "Özne 'they' çoğul olduğu için 'goes' yerine 'go' kullanılmalı",
                      "They go to school.", 75)
    
    log_grammar_error(user_id, "he is happy", "punctuation",
                      "Cümle noktalama işareti ile bitmelidir.",
                      "He is happy.", 90)
    
    # Özet al
    summary = get_error_summary(user_id)
    print("\n📊 Hata Özeti:")
    print(f"  Toplam Hatalar: {summary['total_errors']}")
    print(f"  Ortalama Skor: {summary['average_score']}/100")
    print(f"  Zayıf Alanlar: {summary['weak_areas']}")
    
    print("\n✓ Database test tamamlandı!")
