from typing import List, Dict
from db_utils import get_db_connection, get_due_mistakes
import random


def get_weak_words(user_id, min_attempts=3, threshold=60):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT word_id, english as target_word, AVG(score) as avg_score, COUNT(*) as cnt
        FROM pronunciation_attempts
        JOIN words USING(word_id)
        WHERE user_id = ?
        GROUP BY word_id
        HAVING cnt >= ? AND avg_score < ?
        ORDER BY avg_score ASC
    """, (user_id, min_attempts, threshold))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_review_quiz(user_id: int, limit: int = 20) -> List[Dict]:
    """Kullanıcının `mistakes` tablosuna göre tekrar quizi hazırlar.

    Dönen liste her bir öğe için en az şunları içerir:
    - `mistake_id`, `item_key`, `context`, `prompt`, `correct_answer`, `meta`

    Basit mantık:
    - `get_due_mistakes()` ile next_review zamanı gelen hataları al
    - `count`, `repetition` gibi alanlara göre öncelik ver
    - `context`'e göre prompt oluştur ("Daha önce telaffuz hatası" veya "Cümle hatası")
    """
    rows = get_due_mistakes(user_id=user_id, limit=limit)
    quiz_items = []

    for r in rows:
        # r is sqlite3.Row via get_db_connection row_factory
        item_key = r.get("item_key")
        context = r.get("context") or "general"
        mistake_id = r.get("mistake_id")
        correct = r.get("correct_answer")
        wrong_example = r.get("wrong_answer")
        count = r.get("count") or 1

        if context == "pronunciation":
            prompt = f"Bu kelimeyi doğru telaffuz et: {item_key}"
            qtype = "pronunciation"
        elif context == "sentence":
            prompt = f"Daha önce bu kelimeyle yazdığın yanlış cümleyi düzelt: {wrong_example or item_key}"
            qtype = "sentence"
        else:
            prompt = f"Tekrar et: {item_key}"
            qtype = "fill"

        # Basit öncelik skoru: daha çok tekrar yapanlara + count
        priority = count + (r.get("repetition") or 0)

        quiz_items.append({
            "mistake_id": mistake_id,
            "item_key": item_key,
            "context": context,
            "prompt": prompt,
            "correct_answer": correct,
            "wrong_example": wrong_example,
            "priority": priority,
            "meta": {
                "next_review": r.get("next_review"),
                "last_seen": r.get("last_seen"),
                "easiness": r.get("easiness"),
            },
        })

    # Shuffle with priority bias (higher priority => appear earlier)
    quiz_items.sort(key=lambda x: (-x["priority"], x["meta"]["next_review"] or ""))

    return quiz_items[:limit]

