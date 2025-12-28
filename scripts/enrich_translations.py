"""
Kelimeler için Google Translate API kullanarak Türkçe çeviriler ekle.

Bu script veritabanındaki kelimeleri Türkçe'ye çevirir.
Yavaş ama etkili. Batch'ler halinde çalışır ve progress gösterir.
"""

import sqlite3
from pathlib import Path
import time

# google-translate-new kullanacağız (googletrans daha stabil)
try:
    from google_trans_new import google_translator
    translator = google_translator()
except ImportError:
    print("❌ google-trans-new gerekli. İnstall ediliyor...")
    import subprocess
    subprocess.run(["pip", "install", "google-trans-new", "-q"], check=True)
    from google_trans_new import google_translator
    translator = google_translator()

DB_PATH = Path(__file__).parent / "app.db"
BATCH_SIZE = 10  # Küçük batch Google'ın rate limiting'inden kaçınmak için

def enrich_turkish_translations():
    """Veritabanındaki kelimeleri Türkçe'ye çevir ve ekle."""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Türkçe çevirisi olmayan kelimeleri al
    cursor.execute("SELECT word_id, english FROM words WHERE turkish IS NULL LIMIT 500")
    words_to_translate = cursor.fetchall()
    
    if not words_to_translate:
        print("✅ Tüm kelimeler zaten çevrilmiş!")
        conn.close()
        return
    
    print(f"📚 {len(words_to_translate)} kelime çevirilecek...\n")
    
    translated = 0
    failed = 0
    
    for i, (word_id, english) in enumerate(words_to_translate):
        try:
            # Google Translate API ile çevir
            turkish = translator.translate(english, lang_src='en', lang_tgt='tr')
            
            if turkish and len(turkish) > 0:
                # Veritabanını güncelle
                cursor.execute(
                    "UPDATE words SET turkish = ? WHERE word_id = ?",
                    (turkish, word_id)
                )
                translated += 1
            else:
                failed += 1
            
            # Progress göster (her 10'de bir)
            if (i + 1) % BATCH_SIZE == 0:
                print(f"  ✓ {i + 1}/{len(words_to_translate)} kelime işlendi (çevrilen: {translated})")
                time.sleep(0.5)  # Rate limit öncesi biraz bekle
            
        except Exception as e:
            failed += 1
            print(f"  ❌ '{english}' çevrilemedi: {str(e)[:50]}")
            time.sleep(1)  # Hata sonrası biraz daha bekle
    
    # Commit et
    conn.commit()
    
    print(f"\n✅ Çeviri tamamlandı!")
    print(f"   Çevrilen: {translated}")
    print(f"   Başarısız: {failed}")
    
    # Sonuç kontrol et
    cursor.execute("SELECT COUNT(*) FROM words WHERE turkish IS NOT NULL")
    total_with_tr = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM words")
    total = cursor.fetchone()[0]
    
    print(f"   Toplam Türkçe çeviri: {total_with_tr}/{total}")
    
    conn.close()

if __name__ == "__main__":
    print("=" * 70)
    print("KELIME ÇEVİRİ ENRİCHMENT")
    print("=" * 70)
    enrich_turkish_translations()
