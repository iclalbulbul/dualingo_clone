"""
user_db.py

Kullanıcı girişlerini ve aktivitelerini saklamak için veritabanı işlemleri.
Bu modul:
- Kullanıcı girişlerini (kelime çevirisi, cümle analizi, telaffuz vb.) kaydeder
- Kullanıcı aksiyonlarını ve oturum bilgilerini takip eder
- İstatistikler ve raporlar oluşturur
"""

import sqlite3
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta
import json
from db_utils import DB_PATH, get_db_connection


class UserInputLogger:
    """Kullanıcı girişlerini ve aksiyonlarını loglayan sınıf."""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    # ==================== USER INPUT LOG ====================
    
    def log_user_input(
        self,
        user_id: int,
        input_type: str,
        input_text: str,
        response_text: Optional[str] = None,
        is_correct: Optional[bool] = None,
        score: Optional[float] = None,
        word_id: Optional[int] = None,
        sentence_id: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Kullanıcı girdisini kaydı.
        
        Args:
            user_id: Kullanıcı ID
            input_type: Giriş tipi (word_translation, sentence_analysis, pronunciation vb.)
            input_text: Kullanıcının yazdığı/söylediği metin
            response_text: Sistem yanıtı
            is_correct: Doğru mu yanlış mı
            score: Puan (0-100)
            word_id: İlgili kelime ID
            sentence_id: İlgili cümle ID
            metadata: Ek bilgiler (JSON)
        
        Returns:
            Kaydedilen input'un ID'si
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        try:
            cursor.execute("""
                INSERT INTO user_inputs 
                (user_id, input_type, input_text, response_text, is_correct, score, 
                 word_id, sentence_id, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, input_type, input_text, response_text, 
                is_correct, score, word_id, sentence_id, 
                datetime.now().isoformat(), metadata_json
            ))
            
            conn.commit()
            input_id = cursor.lastrowid
            print(f"✓ Input kaydedildi [ID: {input_id}]")
            return input_id
        
        except Exception as e:
            print(f"❌ Input kaydetme hatası: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    # ==================== USER ACTION LOG ====================
    
    def log_user_action(
        self,
        user_id: int,
        action_type: str,
        action_details: Optional[str] = None,
        page: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> int:
        """
        Kullanıcı aksiyonunu kaydı (sayfa ziyareti, buton tıklama vb.).
        
        Args:
            user_id: Kullanıcı ID
            action_type: Aksiyon tipi (page_visit, button_click, file_upload vb.)
            action_details: Aksiyon detayları
            page: Sayfanın adı
            ip_address: Kullanıcı IP adresi
            user_agent: Tarayıcı bilgisi
        
        Returns:
            Kaydedilen aksiyon ID'si
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO user_actions 
                (user_id, action_type, action_details, page, ip_address, user_agent, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, action_type, action_details, page, 
                ip_address, user_agent, datetime.now().isoformat()
            ))
            
            conn.commit()
            action_id = cursor.lastrowid
            return action_id
        
        except Exception as e:
            print(f"❌ Aksiyon kaydetme hatası: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    # ==================== SESSION LOG ====================
    
    def log_session_start(
        self,
        user_id: int,
        ip_address: Optional[str] = None,
        device_info: Optional[str] = None
    ) -> int:
        """
        Kullanıcı oturum açışını kaydı.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO session_logs 
                (user_id, login_time, ip_address, device_info)
                VALUES (?, ?, ?, ?)
            """, (
                user_id, datetime.now().isoformat(), 
                ip_address, device_info
            ))
            
            conn.commit()
            session_id = cursor.lastrowid
            print(f"✓ Oturum başladı [Session ID: {session_id}]")
            return session_id
        
        except Exception as e:
            print(f"❌ Oturum kaydetme hatası: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    def log_session_end(
        self,
        session_id: int
    ) -> bool:
        """
        Kullanıcı oturumunu sonlandırır ve süresi hesaplayır.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Session bilgilerini al
            cursor.execute("""
                SELECT login_time FROM session_logs WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if not row:
                print(f"❌ Oturum bulunamadı: {session_id}")
                return False
            
            login_time = datetime.fromisoformat(row[0])
            logout_time = datetime.now()
            duration_minutes = int((logout_time - login_time).total_seconds() / 60)
            
            # Session güncelle
            cursor.execute("""
                UPDATE session_logs 
                SET logout_time = ?, session_duration_minutes = ?
                WHERE session_id = ?
            """, (logout_time.isoformat(), duration_minutes, session_id))
            
            conn.commit()
            print(f"✓ Oturum kapandı [Süre: {duration_minutes} dakika]")
            return True
        
        except Exception as e:
            print(f"❌ Oturum kapatma hatası: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # ==================== PRONUNCIATION LOG ====================
    
    def log_pronunciation_attempt(
        self,
        user_id: int,
        word_id: int,
        target_word: str,
        score: float,
        accuracy: Optional[float] = None,
        feedback: Optional[str] = None,
        audio_file: Optional[str] = None
    ) -> int:
        """
        Telaffuz denemesini kaydı.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO pronunciation_attempts 
                (user_id, word_id, target_word, audio_file, score, accuracy, feedback, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, word_id, target_word, audio_file, 
                score, accuracy, feedback, datetime.now().isoformat()
            ))
            
            conn.commit()
            attempt_id = cursor.lastrowid
            print(f"✓ Telaffuz kaydedildi [ID: {attempt_id}]")
            return attempt_id
        
        except Exception as e:
            print(f"❌ Telaffuz kaydetme hatası: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    # ==================== TRANSLATION LOG ====================
    
    def log_translation_attempt(
        self,
        user_id: int,
        english_word: str,
        turkish_translation: str,
        correct_translation: str,
        similarity_score: float,
        is_correct: bool,
        word_id: Optional[int] = None,
        attempt_number: int = 1
    ) -> int:
        """
        Çeviri denemesini kaydı.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO translation_log 
                (user_id, english_word, turkish_translation, correct_translation, 
                 similarity_score, is_correct, attempt_number, word_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, english_word, turkish_translation, correct_translation,
                similarity_score, is_correct, attempt_number, word_id,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            translation_id = cursor.lastrowid
            print(f"✓ Çeviri kaydedildi [ID: {translation_id}]")
            return translation_id
        
        except Exception as e:
            print(f"❌ Çeviri kaydetme hatası: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    # ==================== İSTATİSTİKLER ====================
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Kullanıcının genel istatistiklerini döndür.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        try:
            # Toplam girişler
            cursor.execute("""
                SELECT COUNT(*) FROM user_inputs WHERE user_id = ?
            """, (user_id,))
            stats['total_inputs'] = cursor.fetchone()[0] or 0
            
            # Doğru cevap sayısı
            cursor.execute("""
                SELECT COUNT(*) FROM user_inputs WHERE user_id = ? AND is_correct = 1
            """, (user_id,))
            correct_count = cursor.fetchone()[0] or 0
            stats['correct_answers'] = correct_count
            
            # Doğru cevap yüzdesi
            total = stats['total_inputs']
            stats['accuracy_percent'] = (correct_count / total * 100) if total > 0 else 0
            
            # Ortalama skor
            cursor.execute("""
                SELECT AVG(score) FROM user_inputs WHERE user_id = ? AND score IS NOT NULL
            """, (user_id,))
            avg_score = cursor.fetchone()[0]
            stats['average_score'] = round(avg_score, 2) if avg_score else 0
            
            # Telaffuz denemelerinin ortalaması
            cursor.execute("""
                SELECT AVG(score) FROM pronunciation_attempts WHERE user_id = ?
            """, (user_id,))
            avg_pronunciation = cursor.fetchone()[0]
            stats['average_pronunciation_score'] = round(avg_pronunciation, 2) if avg_pronunciation else 0
            
            # En zayıf kelimeler
            cursor.execute("""
                SELECT english_word, COUNT(*) as attempt_count, 
                       AVG(similarity_score) as avg_similarity
                FROM translation_log 
                WHERE user_id = ? AND is_correct = 0
                GROUP BY english_word
                ORDER BY attempt_count DESC
                LIMIT 5
            """, (user_id,))
            weak_words = cursor.fetchall()
            stats['weak_words'] = [
                {'word': w[0], 'attempts': w[1], 'avg_similarity': round(w[2], 2)} 
                for w in weak_words
            ]
            
            # Son 7 gün etkinlik sayısı
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM user_inputs WHERE user_id = ? AND timestamp > ?
            """, (user_id, week_ago))
            stats['last_7_days_inputs'] = cursor.fetchone()[0] or 0
            
            # Öğrenilen kelime sayısı (doğru cevaplanan benzersiz kelimeler)
            cursor.execute("""
                SELECT COUNT(DISTINCT word_id) FROM user_inputs 
                WHERE user_id = ? AND is_correct = 1 AND word_id IS NOT NULL
            """, (user_id,))
            stats['total_words_learned'] = cursor.fetchone()[0] or 0
            
            # Alternatif: translation_log'dan doğru cevaplanan kelimeler
            cursor.execute("""
                SELECT COUNT(DISTINCT english_word) FROM translation_log 
                WHERE user_id = ? AND is_correct = 1
            """, (user_id,))
            words_from_translation = cursor.fetchone()[0] or 0
            
            # İkisinden büyük olanı al
            if words_from_translation > stats['total_words_learned']:
                stats['total_words_learned'] = words_from_translation
            
            return stats
        
        except Exception as e:
            print(f"❌ İstatistik alma hatası: {e}")
            return stats
        finally:
            conn.close()
    
    def get_user_session_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Kullanıcının son oturum geçmişini döndür.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sessions = []
        
        try:
            cursor.execute("""
                SELECT session_id, login_time, logout_time, session_duration_minutes, 
                       ip_address, device_info
                FROM session_logs 
                WHERE user_id = ?
                ORDER BY login_time DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            for row in rows:
                sessions.append({
                    'session_id': row[0],
                    'login_time': row[1],
                    'logout_time': row[2],
                    'duration_minutes': row[3],
                    'ip_address': row[4],
                    'device_info': row[5]
                })
            
            return sessions
        
        except Exception as e:
            print(f"❌ Oturum geçmişi alma hatası: {e}")
            return sessions
        finally:
            conn.close()
    
    def get_user_recent_inputs(self, user_id: int, limit: int = 20) -> List[Dict]:
        """
        Kullanıcının son girişlerini döndür.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        inputs = []
        
        try:
            cursor.execute("""
                SELECT input_id, input_type, input_text, response_text, is_correct, 
                       score, timestamp
                FROM user_inputs 
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            for row in rows:
                inputs.append({
                    'input_id': row[0],
                    'input_type': row[1],
                    'input_text': row[2],
                    'response_text': row[3],
                    'is_correct': row[4],
                    'score': row[5],
                    'timestamp': row[6]
                })
            
            return inputs
        
        except Exception as e:
            print(f"❌ Son girişler alma hatası: {e}")
            return inputs
        finally:
            conn.close()
    
    def get_word_performance(self, user_id: int) -> Dict[str, Any]:
        """
        Kelime çeviri performansını analiz et.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        performance = {
            'total_translations': 0,
            'correct_translations': 0,
            'accuracy': 0,
            'average_similarity': 0,
            'most_practiced_words': [],
            'easiest_words': [],
            'hardest_words': []
        }
        
        try:
            # Toplam ve doğru çeviriler
            cursor.execute("""
                SELECT COUNT(*), SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END)
                FROM translation_log 
                WHERE user_id = ?
            """, (user_id,))
            
            total, correct = cursor.fetchone()
            performance['total_translations'] = total or 0
            performance['correct_translations'] = correct or 0
            
            if total and total > 0:
                performance['accuracy'] = round((correct / total) * 100, 2)
            
            # Ortalama benzerlik puanı
            cursor.execute("""
                SELECT AVG(similarity_score)
                FROM translation_log 
                WHERE user_id = ?
            """, (user_id,))
            
            avg_sim = cursor.fetchone()[0]
            performance['average_similarity'] = round(avg_sim, 2) if avg_sim else 0
            
            # En çok pratik yapılan kelimeler
            cursor.execute("""
                SELECT english_word, COUNT(*) as practice_count, 
                       AVG(similarity_score) as avg_score
                FROM translation_log 
                WHERE user_id = ?
                GROUP BY english_word
                ORDER BY practice_count DESC
                LIMIT 5
            """, (user_id,))
            
            performance['most_practiced_words'] = [
                {'word': w[0], 'count': w[1], 'avg_score': round(w[2], 2)} 
                for w in cursor.fetchall()
            ]
            
            # En kolay kelimeler (yüksek doğruluk)
            cursor.execute("""
                SELECT english_word, COUNT(*) as count,
                       SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
                FROM translation_log 
                WHERE user_id = ?
                GROUP BY english_word
                HAVING COUNT(*) > 1
                ORDER BY (CAST(correct AS FLOAT) / COUNT(*)) DESC
                LIMIT 5
            """, (user_id,))
            
            performance['easiest_words'] = [
                {'word': w[0], 'accuracy': round((w[2] / w[1]) * 100, 2)} 
                for w in cursor.fetchall()
            ]
            
            # En zor kelimeler (düşük doğruluk)
            cursor.execute("""
                SELECT english_word, COUNT(*) as count,
                       SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
                FROM translation_log 
                WHERE user_id = ?
                GROUP BY english_word
                HAVING COUNT(*) > 1
                ORDER BY (CAST(correct AS FLOAT) / COUNT(*)) ASC
                LIMIT 5
            """, (user_id,))
            
            performance['hardest_words'] = [
                {'word': w[0], 'accuracy': round((w[2] / w[1]) * 100, 2)} 
                for w in cursor.fetchall()
            ]
            
            return performance
        
        except Exception as e:
            print(f"❌ Kelime performansı alma hatası: {e}")
            return performance
        finally:
            conn.close()
    
    # ==================== CLEANUP ====================
    
    def delete_old_logs(self, days: int = 30) -> int:
        """
        Eski günlükleri sil.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        deleted_count = 0
        
        try:
            tables = ['user_inputs', 'user_actions', 'session_logs', 
                     'pronunciation_attempts', 'translation_log']
            
            for table in tables:
                cursor.execute(f"""
                    DELETE FROM {table} WHERE timestamp < ?
                """, (cutoff_date,))
                deleted_count += cursor.rowcount
            
            conn.commit()
            print(f"✓ {deleted_count} eski kayıt silindi")
            return deleted_count
        
        except Exception as e:
            print(f"❌ Eski kayıt silme hatası: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def export_user_data(self, user_id: int) -> Dict[str, Any]:
        """
        Kullanıcı verilerini JSON formatında döndür.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        data = {
            'user_id': user_id,
            'exported_at': datetime.now().isoformat(),
            'statistics': {},
            'recent_inputs': [],
            'session_history': [],
            'word_performance': {}
        }
        
        try:
            # İstatistikler
            data['statistics'] = self.get_user_statistics(user_id)
            
            # Son girişler
            data['recent_inputs'] = self.get_user_recent_inputs(user_id, limit=100)
            
            # Oturum geçmişi
            data['session_history'] = self.get_user_session_history(user_id, limit=50)
            
            # Kelime performansı
            data['word_performance'] = self.get_word_performance(user_id)
            
            return data
        
        except Exception as e:
            print(f"❌ Veri dışa aktarma hatası: {e}")
            return data
        finally:
            conn.close()


# ==================== KULLANIM ÖRNEKLERİ ====================

if __name__ == "__main__":
    logger = UserInputLogger()
    
    # Örnek: Kullanıcı girdisi kaydet
    # input_id = logger.log_user_input(
    #     user_id=1,
    #     input_type='word_translation',
    #     input_text='apple',
    #     response_text='elma',
    #     is_correct=True,
    #     score=95.0
    # )
    
    # Örnek: İstatistikler al
    # stats = logger.get_user_statistics(user_id=1)
    # print(json.dumps(stats, indent=2))
    
    print("✓ UserInputLogger modülü hazır")
