"""
leaderboard.py

Sıralamalar ve rekabet sistemi.
user_stats'den puan hesaplaması yapar.
"""

from db_utils import get_db_connection
from features.user_stats import UserStats
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json


class LeaderboardManager:
    """Sıralamalar ve rekabet sistemi yönetir."""
    
    def __init__(self):
        self.stats_manager = UserStats()
        self.point_system = {
            'correct_answer': 10,
            'accuracy_milestone_80': 50,
            'accuracy_milestone_90': 100,
            'daily_streak': 25,
            'weekly_streak': 100,
            'goal_completed': 200,
            'session_1hour': 30,
            'weak_word_mastered': 50
        }
    
    # ==================== PUAN SİSTEMİ ====================
    
    def calculate_user_score(self, user_id: int) -> float:
        """
        Kullanıcının toplam puanını hesapla.
        
        Puan kaynakları:
        - Doğru cevaplar
        - Doğruluk yüzdesi
        - Ardışık gün sayısı
        - Tamamlanmış hedefler
        - Zayıf kelimeleri ustalaştırma
        """
        stats = self.stats_manager.get_overall_stats(user_id)
        word_perf = self.stats_manager.get_word_stats(user_id)
        
        score = 0.0
        
        try:
            # Doğru cevaplar
            correct_answers = stats.get('correct_answers', 0)
            score += correct_answers * self.point_system['correct_answer']
            
            # Doğruluk milestones
            accuracy = stats.get('accuracy_percent', 0)
            if accuracy >= 90:
                score += self.point_system['accuracy_milestone_90']
            elif accuracy >= 80:
                score += self.point_system['accuracy_milestone_80']
            
            # Hedef tamamlamaları
            completed_goals = self._count_completed_goals(user_id)
            score += completed_goals * self.point_system['goal_completed']
            
            # Ardışık günler
            streak = self._calculate_streak(user_id)
            if streak >= 7:
                score += self.point_system['weekly_streak']
            elif streak >= 1:
                score += streak * self.point_system['daily_streak']
            
            # Zayıf kelimeleri ustalaştırma
            weak_words_mastered = self._count_weak_words_mastered(user_id)
            score += weak_words_mastered * self.point_system['weak_word_mastered']
            
            return round(score, 2)
        
        except Exception as e:
            print(f"❌ Puan hesaplama hatası: {e}")
            return 0.0
    
    # ==================== GLOBAL SIRALAMALAR ====================
    
    def get_global_leaderboard(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Global sıralamayı döndür (tüm kullanıcılar).
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        leaderboard = []
        
        try:
            cursor.execute("SELECT user_id FROM users ORDER BY user_id")
            users = cursor.fetchall()
            
            user_scores = []
            for user in users:
                user_id = user[0]
                score = self.calculate_user_score(user_id)
                
                cursor.execute("""
                    SELECT username FROM users WHERE user_id = ?
                """, (user_id,))
                
                username = cursor.fetchone()[0]
                user_scores.append({
                    'user_id': user_id,
                    'username': username,
                    'score': score
                })
            
            # Puanlara göre sırala
            user_scores.sort(key=lambda x: x['score'], reverse=True)
            
            for rank, user_data in enumerate(user_scores[:limit], 1):
                leaderboard.append({
                    'rank': rank,
                    'user_id': user_data['user_id'],
                    'username': user_data['username'],
                    'score': user_data['score'],
                    'medal': self._get_medal(rank)
                })
            
            return leaderboard
        
        except Exception as e:
            print(f"❌ Global sıralama alma hatası: {e}")
            return leaderboard
        finally:
            conn.close()
    
    def get_weekly_leaderboard(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Haftalık sıralamayı döndür.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        leaderboard = []
        
        try:
            cursor.execute("SELECT DISTINCT user_id FROM user_inputs")
            users = cursor.fetchall()
            
            user_scores = []
            for user in users:
                user_id = user[0]
                score = self._calculate_weekly_score(user_id, week_ago)
                
                cursor.execute("""
                    SELECT username FROM users WHERE user_id = ?
                """, (user_id,))
                
                username_row = cursor.fetchone()
                if username_row:
                    user_scores.append({
                        'user_id': user_id,
                        'username': username_row[0],
                        'score': score
                    })
            
            # Puanlara göre sırala
            user_scores.sort(key=lambda x: x['score'], reverse=True)
            
            for rank, user_data in enumerate(user_scores[:limit], 1):
                leaderboard.append({
                    'rank': rank,
                    'user_id': user_data['user_id'],
                    'username': user_data['username'],
                    'score': user_data['score'],
                    'medal': self._get_medal(rank)
                })
            
            return leaderboard
        
        except Exception as e:
            print(f"❌ Haftalık sıralama alma hatası: {e}")
            return leaderboard
        finally:
            conn.close()
    
    def get_monthly_leaderboard(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Aylık sıralamayı döndür.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        month_ago = (datetime.now() - timedelta(days=30)).isoformat()
        leaderboard = []
        
        try:
            cursor.execute("SELECT DISTINCT user_id FROM user_inputs")
            users = cursor.fetchall()
            
            user_scores = []
            for user in users:
                user_id = user[0]
                score = self._calculate_monthly_score(user_id, month_ago)
                
                cursor.execute("""
                    SELECT username FROM users WHERE user_id = ?
                """, (user_id,))
                
                username_row = cursor.fetchone()
                if username_row:
                    user_scores.append({
                        'user_id': user_id,
                        'username': username_row[0],
                        'score': score
                    })
            
            # Puanlara göre sırala
            user_scores.sort(key=lambda x: x['score'], reverse=True)
            
            for rank, user_data in enumerate(user_scores[:limit], 1):
                leaderboard.append({
                    'rank': rank,
                    'user_id': user_data['user_id'],
                    'username': user_data['username'],
                    'score': user_data['score'],
                    'medal': self._get_medal(rank)
                })
            
            return leaderboard
        
        except Exception as e:
            print(f"❌ Aylık sıralama alma hatası: {e}")
            return leaderboard
        finally:
            conn.close()
    
    # ==================== KULLANICI SIRASI ====================
    
    def get_user_rank(self, user_id: int, period: str = 'all') -> Dict[str, Any]:
        """
        Kullanıcının sıralamasındaki yerine bakı.
        
        Args:
            user_id: Kullanıcı ID
            period: 'all', 'weekly', 'monthly'
        
        Returns:
            Sıralama bilgileri
        """
        if period == 'weekly':
            leaderboard = self.get_weekly_leaderboard(limit=10000)
        elif period == 'monthly':
            leaderboard = self.get_monthly_leaderboard(limit=10000)
        else:
            leaderboard = self.get_global_leaderboard(limit=10000)
        
        for entry in leaderboard:
            if entry['user_id'] == user_id:
                return {
                    'user_id': user_id,
                    'rank': entry['rank'],
                    'score': entry['score'],
                    'medal': entry['medal'],
                    'period': period,
                    'total_participants': len(leaderboard)
                }
        
        return {
            'user_id': user_id,
            'rank': None,
            'score': 0,
            'medal': None,
            'period': period,
            'message': 'Sıralamada henüz yer almıyor'
        }
    
    # ==================== ARKADAŞ SIRALAMASI ====================
    
    def get_friends_leaderboard(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Kullanıcının arkadaşlarının sıralamasını döndür.
        social.py ile entegre olacak.
        """
        from features.social import SocialManager
        
        social_mgr = SocialManager()
        friends = social_mgr.get_friends(user_id)
        
        friend_scores = []
        
        for friend in friends:
            friend_id = friend['friend_id']
            score = self.calculate_user_score(friend_id)
            friend_scores.append({
                'user_id': friend_id,
                'username': friend['friend_username'],
                'score': score
            })
        
        # Puanlara göre sırala
        friend_scores.sort(key=lambda x: x['score'], reverse=True)
        
        leaderboard = []
        for rank, friend_data in enumerate(friend_scores, 1):
            leaderboard.append({
                'rank': rank,
                'user_id': friend_data['user_id'],
                'username': friend_data['username'],
                'score': friend_data['score'],
                'medal': self._get_medal(rank)
            })
        
        return leaderboard
    
    # ==================== ÖZ EL SIRALAMALAR ====================
    
    def get_category_leaderboard(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Kategori bazlı sıralamayı döndür.
        
        Kategoriler:
        - accuracy: Doğruluk yüksek olanlar
        - streak: En uzun ardışık gün
        - speed: En hızlı olanlar
        - improvement: En çok iyileşenler
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        leaderboard = []
        
        try:
            if category == 'accuracy':
                # Doğruluk bazlı
                cursor.execute("""
                    SELECT 
                        u.user_id,
                        u.username,
                        COUNT(ui.input_id) as total_inputs,
                        SUM(CASE WHEN ui.is_correct = 1 THEN 1 ELSE 0 END) as correct_inputs,
                        (SUM(CASE WHEN ui.is_correct = 1 THEN 1 ELSE 0 END) * 100 / 
                         COUNT(ui.input_id)) as accuracy
                    FROM users u
                    LEFT JOIN user_inputs ui ON u.user_id = ui.user_id
                    WHERE ui.input_id IS NOT NULL
                    GROUP BY u.user_id
                    ORDER BY accuracy DESC
                    LIMIT ?
                """, (limit,))
                
                for rank, row in enumerate(cursor.fetchall(), 1):
                    leaderboard.append({
                        'rank': rank,
                        'user_id': row[0],
                        'username': row[1],
                        'metric': f"{row[4]:.2f}%",
                        'total_inputs': row[2],
                        'medal': self._get_medal(rank)
                    })
            
            elif category == 'speed':
                # Hız bazlı (dakika başına input sayısı)
                cursor.execute("""
                    SELECT 
                        u.user_id,
                        u.username,
                        COUNT(ui.input_id) as total_inputs,
                        SUM(sl.session_duration_minutes) as total_minutes,
                        (COUNT(ui.input_id) * 60 / 
                         NULLIF(SUM(sl.session_duration_minutes), 0)) as speed
                    FROM users u
                    LEFT JOIN user_inputs ui ON u.user_id = ui.user_id
                    LEFT JOIN session_logs sl ON u.user_id = sl.user_id
                    WHERE ui.input_id IS NOT NULL
                    GROUP BY u.user_id
                    ORDER BY speed DESC
                    LIMIT ?
                """, (limit,))
                
                for rank, row in enumerate(cursor.fetchall(), 1):
                    leaderboard.append({
                        'rank': rank,
                        'user_id': row[0],
                        'username': row[1],
                        'metric': f"{row[4]:.2f} input/saat",
                        'total_inputs': row[2],
                        'medal': self._get_medal(rank)
                    })
            
            return leaderboard
        
        except Exception as e:
            print(f"❌ Kategori sıralaması alma hatası: {e}")
            return leaderboard
        finally:
            conn.close()
    
    # ==================== YARDIMCI METODLAR ====================
    
    def _get_medal(self, rank: int) -> str:
        """
        Sıraya göre madalya veya emoji döndür.
        """
        if rank == 1:
            return '🥇'
        elif rank == 2:
            return '🥈'
        elif rank == 3:
            return '🥉'
        elif rank <= 10:
            return '⭐'
        else:
            return None
    
    def _calculate_weekly_score(self, user_id: int, week_ago: str) -> float:
        """
        Haftalık puanı hesapla.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        score = 0.0
        
        try:
            # Haftalık doğru cevaplar
            cursor.execute("""
                SELECT COUNT(*) FROM user_inputs 
                WHERE user_id = ? AND is_correct = 1 AND timestamp > ?
            """, (user_id, week_ago))
            
            correct = cursor.fetchone()[0] or 0
            score += correct * self.point_system['correct_answer']
            
            # Haftalık doğruluk
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) * 100 / COUNT(*)
                FROM user_inputs 
                WHERE user_id = ? AND timestamp > ?
            """, (user_id, week_ago))
            
            accuracy = cursor.fetchone()[0] or 0
            if accuracy >= 90:
                score += self.point_system['accuracy_milestone_90']
            elif accuracy >= 80:
                score += self.point_system['accuracy_milestone_80']
            
            return score
        
        except Exception as e:
            print(f"❌ Haftalık puan hesaplama hatası: {e}")
            return 0.0
        finally:
            conn.close()
    
    def _calculate_monthly_score(self, user_id: int, month_ago: str) -> float:
        """
        Aylık puanı hesapla.
        """
        return self._calculate_weekly_score(user_id, month_ago)
    
    def _count_completed_goals(self, user_id: int) -> int:
        """
        Tamamlanmış hedef sayısını al.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM goals 
                WHERE user_id = ? AND status = 'completed'
            """, (user_id,))
            
            return cursor.fetchone()[0] or 0
        except:
            return 0
        finally:
            conn.close()
    
    def _calculate_streak(self, user_id: int) -> int:
        """
        Ardışık gün sayısını hesapla.
        """
        return self.stats_manager._calculate_streak(user_id)
    
    def _count_weak_words_mastered(self, user_id: int) -> int:
        """
        Zayıf kelimelerden kaç tanesini ustalaştırdığını say.
        """
        # Burada mantık: Başlangıçta zayıf kelimeler listesine alınıp
        # sonra doğruluk %90'ın üzerine çıkan kelimeler sayılacak
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT english_word
                    FROM translation_log
                    WHERE user_id = ?
                    GROUP BY english_word
                    HAVING 
                        COUNT(*) >= 3 AND
                        (SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) * 100 / COUNT(*)) >= 90
                )
            """, (user_id,))
            
            return cursor.fetchone()[0] or 0
        except:
            return 0
        finally:
            conn.close()


# ==================== KULLANIM ÖRNEKLERİ ====================

if __name__ == "__main__":
    lb = LeaderboardManager()
    
    # Global sıralama
    # global_lb = lb.get_global_leaderboard(limit=10)
    # print(json.dumps(global_lb, indent=2, default=str))
    
    # Kullanıcı sırası
    # rank = lb.get_user_rank(user_id=1)
    # print(json.dumps(rank, indent=2))
    
    print("✓ LeaderboardManager modülü hazır")
