from db_utils import get_db_connection

def save_pronunciation(user_id, word_id, target_word, score, feedback):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO pronunciation_attempts
        (user_id, word_id, target_word, score, feedback)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, word_id, target_word, score, feedback))

    conn.commit()
    conn.close()


def save_sentence_attempt(user_id, word_id, sentence, score, is_correct, metadata=None):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO user_inputs
        (user_id, input_type, input_text, is_correct, score, word_id, metadata)
        VALUES (?, 'sentence', ?, ?, ?, ?, ?)
    """, (user_id, sentence, is_correct, score, word_id, metadata))

    conn.commit()
    conn.close()

