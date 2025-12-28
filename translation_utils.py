"""
Translation Utilities - Deep Translator API ile İngilizce-Türkçe çeviri
Cache sistemi: Önce DB'den kontrol, yoksa API'den al ve DB'ye kaydet
"""

from deep_translator import GoogleTranslator
from difflib import SequenceMatcher
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")


def _get_db_connection():
    """Veritabanı bağlantısı oluşturur."""
    return sqlite3.connect(DB_PATH)


def get_translation(english_word: str) -> str:
    """
    İngilizce kelimeyi Türkçeye çevirir (Cache sistemi ile).
    
    Akış:
    1. DB'de var mı kontrol et (words.turkish)
    2. Varsa → DB'den dön (hızlı)
    3. Yoksa → API'den al (Deep Translator)
    4. API sonucunu DB'ye kaydet (cache)
    5. Sonucu dön
    
    Args:
        english_word: Çevrilecek İngilizce kelime
    
    Returns:
        Türkçe çeviri veya None (hata durumunda)
    """
    if not english_word:
        return None
    
    english_word = english_word.strip().lower()
    
    # 1. DB'de var mı kontrol et
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT turkish FROM words WHERE LOWER(english) = ? AND turkish IS NOT NULL LIMIT 1",
            (english_word,)
        )
        row = cursor.fetchone()
        
        if row and row[0]:
            # DB'de var, hızlıca dön
            conn.close()
            return row[0]
        
        conn.close()
    except Exception as e:
        print(f"DB okuma hatası: {e}")
    
    # 2. DB'de yok, API'den al
    api_translation = translate_to_turkish(english_word)
    
    if not api_translation:
        return None
    
    # 3. API sonucunu DB'ye kaydet (cache)
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        # Kelime DB'de var mı kontrol et
        cursor.execute(
            "SELECT word_id FROM words WHERE LOWER(english) = ? LIMIT 1",
            (english_word,)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Mevcut kelimeyi güncelle
            cursor.execute(
                "UPDATE words SET turkish = ? WHERE word_id = ?",
                (api_translation, existing[0])
            )
        else:
            # Yeni kelime ekle
            cursor.execute(
                "INSERT INTO words (english, turkish, level) VALUES (?, ?, 'A1')",
                (english_word, api_translation)
            )
        
        conn.commit()
        conn.close()
        print(f"✓ Cache'e eklendi: {english_word} → {api_translation}")
        
    except Exception as e:
        print(f"DB yazma hatası: {e}")
    
    return api_translation


def translate_to_turkish(english_word: str) -> str:
    """
    İngilizce kelimeyi Deep Translator API ile Türkçeye çevirir.
    
    Args:
        english_word: Çevrilecek İngilizce kelime
    
    Returns:
        Türkçe çeviri veya None (hata durumunda)
    """
    try:
        translator = GoogleTranslator(source='en', target='tr')
        result = translator.translate(english_word)
        return result.strip() if result else None
    except Exception as e:
        print(f"Çeviri hatası: {e}")
        return None


def similarity_ratio(str1: str, str2: str) -> float:
    """
    İki string arasındaki benzerlik oranını hesaplar.
    
    Args:
        str1: İlk string
        str2: İkinci string
    
    Returns:
        0.0-1.0 arası benzerlik oranı
    """
    if not str1 or not str2:
        return 0.0
    
    s1 = str1.strip().lower()
    s2 = str2.strip().lower()
    
    return SequenceMatcher(None, s1, s2).ratio()


def check_answer(user_answer: str, correct_turkish: str, threshold: float = 0.80) -> dict:
    """
    Kullanıcı cevabını kontrol et (exact + similarity match).
    
    Args:
        user_answer: Kullanıcının verdiği Türkçe cevap
        correct_turkish: API'den alınan doğru Türkçe çeviri
        threshold: Benzerlik eşiği (0.0-1.0, default 0.80 = %80)
    
    Returns:
        {
            "is_correct": bool,
            "similarity": float (0.0-1.0),
            "correct_answer": str,
            "feedback": str
        }
    """
    
    if not correct_turkish:
        return {
            "is_correct": False,
            "similarity": 0.0,
            "correct_answer": "Çeviri bulunamadı",
            "feedback": "Çeviri API'sinden hata oluştu"
        }
    
    # Benzerlik hesapla
    similarity = similarity_ratio(user_answer, correct_turkish)
    
    # Eşik değerinin üzerinde ise doğru kabul et
    is_correct = similarity >= threshold
    
    # Feedback oluştur
    if is_correct:
        if similarity >= 0.95:
            feedback = f"Harika! %{int(similarity*100)} doğru"
        else:
            feedback = f"Yaklaştın! %{int(similarity*100)} eşleşme"
    else:
        if similarity >= 0.60:
            feedback = f"Neredeyse! Benzerlik: %{int(similarity*100)}"
        else:
            feedback = f"Biraz farklı. Benzerlik: %{int(similarity*100)}"
    
    return {
        "is_correct": is_correct,
        "similarity": similarity,
        "correct_answer": correct_turkish,
        "feedback": feedback
    }
