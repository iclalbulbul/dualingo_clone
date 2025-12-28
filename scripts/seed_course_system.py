"""
Kurs sistemi verilerini seed eder.
Bu script mevcut verilere dokunmaz, sadece yeni tablolar oluşturur ve doldurur.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from features.course_system import course_system

def main():
    print("=" * 50)
    print("🎓 KURS SİSTEMİ SEED")
    print("=" * 50)
    
    # 1. CEFR Seviyeleri
    print("\n1. CEFR Seviyeleri ekleniyor...")
    course_system.seed_levels()
    
    # 2. Üniteler
    print("\n2. Üniteler ekleniyor...")
    course_system.seed_units()
    
    # 3. Dersler
    print("\n3. Dersler ekleniyor...")
    course_system.seed_lessons()
    
    print("\n" + "=" * 50)
    print("✅ Kurs sistemi seed tamamlandı!")
    print("=" * 50)

if __name__ == "__main__":
    main()
