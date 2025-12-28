"""
Demo: A1 kelimeleri için özel Türkçe çeviriler yükle.

Bu script en sık kullanılan A1 kelimelerinin Türkçe çevirilerini yükler.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "app.db"

# A1 kelimeleri ve Türkçe çeviriler (sık kullanılanlar)
TRANSLATIONS_A1 = {
    "acres": "dönüm",
    "agricultural": "tarımsal",
    "agriculture": "tarım",
    "autumn": "sonbahar",
    "bacon": "domuz eti",
    "apple": "elma",
    "book": "kitap",
    "cat": "kedi",
    "dog": "köpek",
    "water": "su",
    "house": "ev",
    "tree": "ağaç",
    "flower": "çiçek",
    "sun": "güneş",
    "moon": "ay",
    "star": "yıldız",
    "sky": "gökyüzü",
    "cloud": "bulut",
    "rain": "yağmur",
    "snow": "kar",
    "wind": "rüzgar",
    "fire": "ateş",
    "ice": "buz",
    "mountain": "dağ",
    "river": "nehir",
    "lake": "göl",
    "ocean": "okyanus",
    "beach": "plaj",
    "bird": "kuş",
    "fish": "balık",
    "animal": "hayvan",
    "plant": "bitki",
    "fruit": "meyve",
    "vegetable": "sebze",
    "food": "yemek",
    "drink": "içecek",
    "bread": "ekmek",
    "milk": "süt",
    "cheese": "peynir",
    "egg": "yumurta",
    "meat": "et",
    "chicken": "tavuk",
    "fish": "balık",
    "rice": "pirinç",
    "salt": "tuz",
    "sugar": "şeker",
    "table": "masa",
    "chair": "sandalye",
    "bed": "yatak",
    "door": "kapı",
    "window": "pencere",
    "wall": "duvar",
    "floor": "zemin",
    "roof": "çatı",
    "room": "oda",
    "kitchen": "mutfak",
    "bathroom": "banyo",
}

def load_translations():
    """A1 kelimeleri için çeviriler yükle."""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updated = 0
    
    for english, turkish in TRANSLATIONS_A1.items():
        cursor.execute(
            "UPDATE words SET turkish = ? WHERE english = ? AND level = 'A1' AND turkish IS NULL",
            (turkish, english)
        )
        updated += cursor.rowcount
    
    conn.commit()
    
    # Sonuç kontrol et
    cursor.execute("SELECT COUNT(*) FROM words WHERE level = 'A1' AND turkish IS NOT NULL")
    total_with_tr = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM words WHERE level = 'A1'")
    total = cursor.fetchone()[0]
    
    print(f"✅ Çeviri yükleme tamamlandı!")
    print(f"   Güncellenen: {updated}")
    print(f"   A1 seviyesi:")
    print(f"     - Türkçesi olan: {total_with_tr}")
    print(f"     - Toplam: {total}")
    print(f"     - Kapsama: %{(total_with_tr*100)//total}")
    
    conn.close()

if __name__ == "__main__":
    print("=" * 70)
    print("A1 KELİMELERİ ÇEVİRİ YÜKLE")
    print("=" * 70)
    load_translations()
