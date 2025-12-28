"""
Grammar kurallarını app.db'ye ekle.
Seviyelere göre organize edilmiş temel 15 kural.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "app.db"

RULES = [
    # A1 - Temel
    ("capital_letter", "Cümle Başında Büyük Harf", "Cümle büyük harfle başlamalıdır.", "A1"),
    ("punctuation", "Noktalama İşareti", "Cümle . ! ? işaretlerinden biriyle bitmelidir.", "A1"),
    ("minimum_words", "Minimum Kelime Sayısı", "Cümle en az 2 kelime içermelidir.", "A1"),
    
    # A2 - Temel +
    ("subject_verb_agreement", "Özne-Fiil Uyumu", "Özne ve fiil sayı bakımından uyumlu olmalıdır. (he goes, they go)", "A2"),
    ("article_usage", "Makale Kullanımı", "'a' ve 'an' İngilizce'de yazılı iletişim için çok önemlidir.", "A2"),
    
    # B1 - Orta
    ("sentence_structure", "Temel Cümle Yapısı", "İngilizce genelde Özne + Fiil + Nesne (SVO) sırasını takip eder.", "B1"),
    ("tense_consistency", "Zamanlama Tutarlılığı", "Bir cümle içinde aynı zamanda tutarlı olun (geçmiş veya şimdiki).", "B1"),
    ("adjective_order", "Sıfat Sırası", "Sıfatlar belirli bir sırada gelmelidir: quantity > quality > color > nationality", "B1"),
    
    # B2 - Orta +
    ("passive_voice", "Pasif Yapı", "Pasif yapı: be + past participle (The letter was written by John)", "B2"),
    ("conditional_structures", "Şart Cümleleri", "If + present > will + verb veya if + past > would + verb", "B2"),
    ("modal_verbs", "Modal Fiiller", "can, could, may, might, must, shall, should, will, would doğru bağlamda kullanılmalı.", "B2"),
    
    # C1 - İleri
    ("complex_sentences", "Karmaşık Cümle Yapıları", "Bağlaçlar (although, however, whereas) ile sofistike cümleler oluşturun.", "C1"),
    ("subjunctive_mood", "Dilek Kipi", "If I were... / I suggest that he be... yapıları kullanın.", "C1"),
    
    # C2 - Akıcı
    ("idiomatic_expressions", "Deyimsel İfadeler", "Native-like ifadeler ve bağlam-spesifik kullanımlar.", "C2"),
    ("register_variation", "Konu Üslup Çeşitliliği", "Resmi/gayriresmi, akademik/konuşma bağlamlarına göre dil değişikliği.", "C2"),
]

def seed_rules():
    """Kural tablosunu doldur."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # İlk önce var olan kuralları kontrol et
    cursor.execute("SELECT COUNT(*) FROM grammar_rules")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"⚠️  Zaten {count} kural mevcut. Yenileri ekleniyor...")
    
    # Kuralları ekle (IGNORE varsa atla)
    cursor.executemany(
        """INSERT OR IGNORE INTO grammar_rules (rule_key, title_tr, explanation_tr, level)
           VALUES (?, ?, ?, ?)""",
        RULES
    )
    
    conn.commit()
    
    # Sonuç
    cursor.execute("SELECT COUNT(*) FROM grammar_rules")
    total = cursor.fetchone()[0]
    
    # Seviye başına dağılım
    cursor.execute("""
        SELECT level, COUNT(*) as count
        FROM grammar_rules
        GROUP BY level
        ORDER BY level
    """)
    
    print(f"\n✅ Kural seeding tamamlandı!")
    print(f"   Toplam kural: {total}\n")
    print("   Seviye dağılımı:")
    for level, cnt in cursor.fetchall():
        print(f"   - {level}: {cnt} kural")
    
    conn.close()

if __name__ == "__main__":
    seed_rules()
