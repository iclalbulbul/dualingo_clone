# points_manager.py
# Merkezi puanlama sistemi

class PointsManager:
    """Kullanıcı aksiyonlarına göre puan güncelleme sistemi."""
    # Aksiyon başına puanlar
    POINTS = {
        'correct_answer': 10,
        'wrong_answer': -2,
        'lesson_complete': 50,
        'unit_complete': 200,
        'daily_login': 20,
        'streak_bonus': 30,
    }

    @classmethod
    def add_points(cls, user_id, action, db_conn=None, extra=0):
        """
        Kullanıcıya aksiyona göre puan ekle.
        :param user_id: int
        :param action: str (POINTS içindeki anahtarlar)
        :param db_conn: opsiyonel, mevcut bağlantı
        :param extra: ek puan (opsiyonel)
        """
        points = cls.POINTS.get(action, 0) + extra
        import db_utils
        conn = db_conn or db_utils.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE user_course_state SET total_xp = total_xp + ? WHERE user_id = ?
        """, (points, user_id))
        if not db_conn:
            conn.commit()
            conn.close()
        return points
