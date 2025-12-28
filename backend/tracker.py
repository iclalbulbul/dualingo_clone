import json
from db_utils import get_db_connection


def _get_or_create_word_id(conn, english_word: str):
    cur = conn.cursor()
    # Önce kelimeyi ara
    cur.execute("SELECT word_id FROM words WHERE english = ?", (english_word,))
    row = cur.fetchone()
    if row and row[0]:
        return row[0]

    # Bulunamadıysa basit bir satır ekle (sadece english alanı doldurulur)
    cur.execute("INSERT INTO words (english) VALUES (?)", (english_word,))
    return cur.lastrowid


def save_pronunciation(user_id, word=None, score=None, feedback=None, word_id=None, target_word=None):
    """Uyumluluk wrapper: lesson_flow'dan gelen `word` ya da `word_id` ile çalışır.
    Eğer sadece `word` verilmişse words tablosunda arar/ekler ve `word_id` kullanır.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Tercih edilen kelime kaynakları
    english = None
    if word:
        english = word
    elif target_word:
        english = target_word

    if not word_id and english:
        word_id = _get_or_create_word_id(conn, english)

    # pronunciation_attempts.word_id schema gereği NOT NULL olabilir; bu yüzden word_id garanti edilmeli
    if not word_id:
        # fallback: ekleme yapmadan bırakma
        conn.close()
        return None

    cur.execute(
        """
        INSERT INTO pronunciation_attempts
        (user_id, word_id, target_word, score, feedback)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, word_id, english or None, score, feedback),
    )

    conn.commit()
    conn.close()


def save_sentence_attempt(user_id, word=None, sentence=None, score=None, metadata=None, word_id=None):
    """Uyumluluk wrapper: lesson_flow'dan gelen `word` veya `word_id` ile user_inputs tablosuna kaydeder.
    `is_correct` alanı score bilgisine göre belirlenebilir (None bırakılırsa NULL yazılır).
    """
    conn = get_db_connection()
    cur = conn.cursor()

    if not word_id and word:
        word_id = _get_or_create_word_id(conn, word)

    is_correct = None
    try:
        if score is not None:
            # basit eşik: 50 ve üstü doğru kabul edilsin
            is_correct = 1 if float(score) >= 50 else 0
    except Exception:
        is_correct = None

    cur.execute(
        """
        INSERT INTO user_inputs
        (user_id, input_type, input_text, is_correct, score, word_id, metadata)
        VALUES (?, 'sentence', ?, ?, ?, ?, ?)
        """,
        (user_id, sentence, is_correct, score, word_id, json.dumps(metadata) if metadata is not None else None),
    )

    conn.commit()
    conn.close()

