#!/usr/bin/env python3
"""
Test script: AI feedback fonksiyonunu test et
"""
import os
import sys
import json

# Gerekli imports
try:
    from backend.ai_utils import mistake_feedback
    from backend.ai_utils import _llm_chat
    print("✅ Imports başarılı")
except ImportError as e:
    print(f"❌ Import hatası: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("TEST 1: _llm_chat fonksiyonu (API kontrolü)")
print("="*70)

try:
    result = _llm_chat(
        prompt="Test prompt - basit cevap ver: test",
        system="You are helpful."
    )
    print(f"Result type: {type(result)}")
    print(f"Result length: {len(result) if isinstance(result, str) else 'N/A'}")
    print(f"First 200 chars: {result[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("TEST 2: mistake_feedback fonksiyonu")
print("="*70)

try:
    feedback = mistake_feedback(
        wrong_answer="I go to school yesterday",
        correct_answer="I went to school yesterday",
        context="sentence"
    )
    
    print(f"\n✅ Feedback başarıyla oluşturuldu!")
    print(f"Type: {type(feedback)}")
    print(f"Keys: {list(feedback.keys()) if isinstance(feedback, dict) else 'N/A'}")
    print(f"\nFull feedback:")
    print(json.dumps(feedback, ensure_ascii=False, indent=2))
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("TEST 3: Veritabanından hata al ve feedback üret")
print("="*70)

try:
    from db_utils import get_user_mistakes
    
    # Bir kullanıcının hatalarını al (test kullanıcısı varsa)
    # user_id=1 test amaçlı
    mistakes = get_user_mistakes(user_id=1, limit=3)
    
    if mistakes:
        print(f"✅ {len(mistakes)} hata bulundu")
        for i, mistake in enumerate(mistakes[:1], 1):
            print(f"\nHata {i}:")
            print(f"  Item: {mistake.get('item_key')}")
            print(f"  Context: {mistake.get('context')}")
            print(f"  Wrong: {mistake.get('wrong_answer')}")
            print(f"  Correct: {mistake.get('correct_answer')}")
            
            try:
                fb = mistake_feedback(
                    wrong_answer=mistake.get("wrong_answer", ""),
                    correct_answer=mistake.get("correct_answer", ""),
                    context=mistake.get("context", "sentence")
                )
                print(f"\n  Feedback:")
                print(f"    Explanation: {fb.get('explanation', 'N/A')[:100]}...")
                print(f"    Tips count: {len(fb.get('tips', []))}")
            except Exception as e:
                print(f"  ❌ Feedback hatası: {e}")
    else:
        print("⚠️ Hata bulunamadı (veritabanında hata olmayabilir)")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("Testler tamamlandı")
print("="*70)
