"""
notifications.py

Bildirim sistemi.
user_stats, goals ve leaderboard'dan tetiklenir.
"""

from db_utils import get_db_connection
from datetime import datetime
from typing import Dict, List, Any, Optional
import json


class NotificationManager:
    """Bildirim sistemi yönetir."""
    
    def __init__(self):
        self.notification_types = {
            'achievement': 'Başarı',
            'goal_progress': 'Hedef İlerlemesi',
            'goal_completed': 'Hedef Tamamlandı',
            'streak_milestone': 'Ardışık Gün Dönüm Noktası',
            'rank_change': 'Sıralama Değişikliği',
            'accuracy_improvement': 'Doğruluk İyileşmesi',
            'weak_word_reminder': 'Zayıf Kelime Hatırlatması',
            'daily_goal': 'Günlük Hedef Hatırlatması',
            'new_achievement': 'Yeni Başarı Kilidi',
            'friend_achievement': 'Arkadaş Başarısı',
            'system': 'Sistem Bildirimi'
        }
    
    # ==================== BİLDİRİM OLUŞTURMA ====================
    
    def create_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        icon: Optional[str] = None,
        action_url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Yeni bildirim oluştur.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Bildirim tablosu var mı kontrol et
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    notification_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    icon TEXT,
                    action_url TEXT,
                    metadata TEXT,
                    is_read BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO notifications 
                (user_id, notification_type, title, message, icon, action_url, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, notification_type, title, message, icon, action_url, metadata_json))
            
            conn.commit()
            notif_id = cursor.lastrowid
            print(f"✓ Bildirim oluşturuldu [ID: {notif_id}]")
            return notif_id
        
        except Exception as e:
            print(f"❌ Bildirim oluşturma hatası: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    # ==================== BİLDİRİMLERİ AL ====================
    
    def get_user_notifications(
        self,
        user_id: int,
        limit: int = 20,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Kullanıcının bildirimlerini al.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        notifications = []
        
        try:
            where_clause = "WHERE user_id = ?"
            params = [user_id]
            
            if unread_only:
                where_clause += " AND is_read = 0"
            
            cursor.execute(f"""
                SELECT notification_id, notification_type, title, message, icon, 
                       action_url, metadata, is_read, created_at, read_at
                FROM notifications 
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """, params + [limit])
            
            for row in cursor.fetchall():
                metadata = json.loads(row[6]) if row[6] else None
                
                notifications.append({
                    'notification_id': row[0],
                    'notification_type': row[1],
                    'title': row[2],
                    'message': row[3],
                    'icon': row[4],
                    'action_url': row[5],
                    'metadata': metadata,
                    'is_read': bool(row[7]),
                    'created_at': row[8],
                    'read_at': row[9]
                })
            
            return notifications
        
        except Exception as e:
            print(f"❌ Bildirim alma hatası: {e}")
            return notifications
        finally:
            conn.close()
    
    def get_unread_notification_count(self, user_id: int) -> int:
        """
        Okunmamış bildirim sayısını al.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM notifications 
                WHERE user_id = ? AND is_read = 0
            """, (user_id,))
            
            return cursor.fetchone()[0] or 0
        
        except Exception as e:
            print(f"❌ Okunmamış bildirim sayısı hatası: {e}")
            return 0
        finally:
            conn.close()
    
    # ==================== BİLDİRİMİ OKU ====================
    
    def mark_as_read(self, notification_id: int) -> bool:
        """
        Bildirimi okundu olarak işaretle.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE notifications 
                SET is_read = 1, read_at = ?
                WHERE notification_id = ?
            """, (datetime.now().isoformat(), notification_id))
            
            conn.commit()
            return True
        
        except Exception as e:
            print(f"❌ Bildirim işaretleme hatası: {e}")
            return False
        finally:
            conn.close()
    
    def mark_all_as_read(self, user_id: int) -> bool:
        """
        Tüm bildirimleri okundu olarak işaretle.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE notifications 
                SET is_read = 1, read_at = ?
                WHERE user_id = ? AND is_read = 0
            """, (datetime.now().isoformat(), user_id))
            
            conn.commit()
            return True
        
        except Exception as e:
            print(f"❌ Tüm bildirimler işaretleme hatası: {e}")
            return False
        finally:
            conn.close()
    
    # ==================== OTOMATIK BİLDİRİMLER ====================
    
    def trigger_achievement_notification(self, user_id: int, achievement_name: str) -> int:
        """
        Başarı bildirimi tetikle.
        """
        achievement_icons = {
            '100_inputs': '🎉',
            '1_week_streak': '🔥',
            '90_accuracy': '⭐',
            'goal_completed': '🏆',
            'rank_up': '📈'
        }
        
        icon = achievement_icons.get(achievement_name, '✨')
        
        return self.create_notification(
            user_id=user_id,
            notification_type='achievement',
            title=f'Yeni Başarı: {achievement_name}',
            message=f'Tebrikler! {achievement_name} başarısını kazandın!',
            icon=icon,
            metadata={'achievement': achievement_name}
        )
    
    def trigger_goal_progress_notification(
        self,
        user_id: int,
        goal_id: int,
        goal_title: str,
        progress_percent: float
    ) -> int:
        """
        Hedef ilerleme bildirimi tetikle.
        """
        return self.create_notification(
            user_id=user_id,
            notification_type='goal_progress',
            title=f'Hedef İlerlemesi',
            message=f'{goal_title}: %{progress_percent:.0f} tamamlandı',
            icon='📊',
            action_url=f'/goals/{goal_id}',
            metadata={'goal_id': goal_id, 'progress': progress_percent}
        )
    
    def trigger_goal_completed_notification(self, user_id: int, goal_title: str) -> int:
        """
        Hedef tamamlandı bildirimi tetikle.
        """
        return self.create_notification(
            user_id=user_id,
            notification_type='goal_completed',
            title='Hedef Tamamlandı! 🎯',
            message=f'Tebrikler! "{goal_title}" hedefini tamamladın!',
            icon='🏅',
            metadata={'goal_title': goal_title}
        )
    
    def trigger_streak_milestone_notification(self, user_id: int, streak_days: int) -> int:
        """
        Ardışık gün dönüm noktası bildirimi tetikle.
        """
        streak_messages = {
            3: 'İlk 3 günü yaptın! 🎉',
            7: '1 haftalık streak! 🔥',
            14: '2 haftalık streak! 🚀',
            30: '1 aylık streak! 🏆',
            60: '2 aylık streak! 👑',
            100: '100 günlük streak! 👑👑👑'
        }
        
        message = streak_messages.get(streak_days, f'{streak_days} günlük streak!')
        
        return self.create_notification(
            user_id=user_id,
            notification_type='streak_milestone',
            title=f'{streak_days} Günlük Streak',
            message=message,
            icon='🔥',
            metadata={'streak_days': streak_days}
        )
    
    def trigger_rank_change_notification(
        self,
        user_id: int,
        old_rank: int,
        new_rank: int
    ) -> int:
        """
        Sıralama değişikliği bildirimi tetikle.
        """
        if new_rank < old_rank:
            direction = 'YÜKSELDİ'
            icon = '📈'
        else:
            direction = 'düştü'
            icon = '📉'
        
        return self.create_notification(
            user_id=user_id,
            notification_type='rank_change',
            title='Sıralama Değişikliği',
            message=f"Sıralaman #{old_rank}'den #{new_rank}'ye {direction}!",
            icon=icon,
            action_url='/leaderboard',
            metadata={'old_rank': old_rank, 'new_rank': new_rank}
        )
    
    def trigger_weak_word_reminder(self, user_id: int, word: str) -> int:
        """
        Zayıf kelime hatırlatması.
        """
        return self.create_notification(
            user_id=user_id,
            notification_type='weak_word_reminder',
            title='Hatırlatma',
            message=f'"{word}" kelimesini birkaç kez yanlış yaptın, tekrar etmeyi unutma!',
            icon='💪',
            action_url='/practice_word',
            metadata={'word': word}
        )
    
    def trigger_daily_goal_reminder(self, user_id: int) -> int:
        """
        Günlük hedef hatırlatması.
        """
        return self.create_notification(
            user_id=user_id,
            notification_type='daily_goal',
            title='Günlük Hedef Hatırlatması',
            message='Bugünün hedefini tamamlamayı unutma!',
            icon='🎯',
            action_url='/dashboard',
            metadata={'date': datetime.now().strftime('%Y-%m-%d')}
        )
    
    def trigger_accuracy_improvement_notification(
        self,
        user_id: int,
        old_accuracy: float,
        new_accuracy: float
    ) -> int:
        """
        Doğruluk iyileşmesi bildirimi.
        """
        improvement = new_accuracy - old_accuracy
        
        return self.create_notification(
            user_id=user_id,
            notification_type='accuracy_improvement',
            title='Doğruluk İyileşmesi 📈',
            message=f'Doğruluk oranın %{old_accuracy:.1f}\'den %{new_accuracy:.1f}\'e yükseldi! (+%{improvement:.1f})',
            icon='⭐',
            metadata={'old_accuracy': old_accuracy, 'new_accuracy': new_accuracy}
        )
    
    # ==================== BİLDİRİM TETİKLEME ====================
    
    def check_and_trigger_notifications(self, user_id: int) -> List[int]:
        """
        Kullanıcı için otomatik bildirimleri kontrol et ve tetikle.
        """
        from features.user_stats import UserStats
        from features.goals import GoalManager
        
        triggered_notifications = []
        
        try:
            stats = UserStats()
            goal_mgr = GoalManager()
            
            # Doğruluk iyileşmesi kontrolü
            weekly_stats = stats.get_weekly_stats(user_id)
            if weekly_stats['accuracy_percent'] >= 85:
                # Bildirim tetikle
                notif_id = self.trigger_achievement_notification(
                    user_id=user_id,
                    achievement_name='accuracy_improved'
                )
                if notif_id > 0:
                    triggered_notifications.append(notif_id)
            
            # Ardışık gün kontrolü
            streak = weekly_stats['streak_days']
            if streak > 0 and streak in [3, 7, 14, 30, 60, 100]:
                notif_id = self.trigger_streak_milestone_notification(user_id, streak)
                if notif_id > 0:
                    triggered_notifications.append(notif_id)
            
            # Zayıf kelimeler kontrolü
            word_perf = stats.get_word_stats(user_id)
            if word_perf['hardest_words']:
                hardest = word_perf['hardest_words'][0]
                notif_id = self.trigger_weak_word_reminder(
                    user_id=user_id,
                    word=hardest['word']
                )
                if notif_id > 0:
                    triggered_notifications.append(notif_id)
            
            return triggered_notifications
        
        except Exception as e:
            print(f"❌ Bildirim tetikleme hatası: {e}")
            return triggered_notifications
    
    # ==================== BİLDİRİMLERİ SİL ====================
    
    def delete_notification(self, notification_id: int) -> bool:
        """
        Bildirimi sil.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM notifications WHERE notification_id = ?
            """, (notification_id,))
            
            conn.commit()
            return True
        
        except Exception as e:
            print(f"❌ Bildirim silme hatası: {e}")
            return False
        finally:
            conn.close()
    
    def delete_old_notifications(self, days: int = 30) -> int:
        """
        Eski bildirimleri sil.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute("""
                DELETE FROM notifications WHERE created_at < ?
            """, (cutoff_date,))
            
            conn.commit()
            deleted = cursor.rowcount
            print(f"✓ {deleted} eski bildirim silindi")
            return deleted
        
        except Exception as e:
            print(f"❌ Eski bildirim silme hatası: {e}")
            return 0
        finally:
            conn.close()


# ==================== KULLANIM ÖRNEKLERİ ====================

if __name__ == "__main__":
    from datetime import timedelta
    
    notif_mgr = NotificationManager()
    
    # Bildirim oluştur
    # notif_id = notif_mgr.create_notification(
    #     user_id=1,
    #     notification_type='system',
    #     title='Hoşgeldiniz',
    #     message='LoroLeng\'e hoşgeldiniz!',
    #     icon='👋'
    # )
    
    # Bildirimleri al
    # notifs = notif_mgr.get_user_notifications(user_id=1)
    # print(json.dumps(notifs, indent=2, default=str))
    
    print("✓ NotificationManager modülü hazır")
