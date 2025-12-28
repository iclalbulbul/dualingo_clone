"""
social.py

Sosyal özellikler: Arkadaş, paylaşım, rekabet vb.
notifications ve leaderboard ile entegre.
"""

from db_utils import get_db_connection
from features.notifications import NotificationManager
from datetime import datetime
from typing import Dict, List, Any, Optional
import json


class SocialManager:
    """Sosyal özellikleri yönetir."""
    
    def __init__(self):
        self.notif_mgr = NotificationManager()
    
    # ==================== ARKADAŞ YÖNETİMİ ====================
    
    def add_friend(self, user_id: int, friend_id: int) -> dict:
        """
        Arkadaş ekle (karşılıklı).
        Returns: {'success': bool, 'message': str}
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Kendine arkadaş ekleme kontrolü
            if user_id == friend_id:
                return {'success': False, 'message': 'Kendini arkadaş olarak ekleyemezsin!'}
            
            # Tablo oluştur
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS friends (
                    friendship_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    friend_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (friend_id) REFERENCES users(user_id),
                    UNIQUE(user_id, friend_id)
                )
            """)
            
            # Zaten istek var mı kontrol et
            cursor.execute("""
                SELECT friendship_id, status FROM friends 
                WHERE user_id = ? AND friend_id = ?
            """, (user_id, friend_id))
            existing = cursor.fetchone()
            
            if existing:
                existing_id, status = existing
                if status == 'pending':
                    return {'success': False, 'message': 'Zaten arkadaş isteği gönderdin!'}
                elif status == 'confirmed':
                    return {'success': False, 'message': 'Zaten arkadaşsınız!'}
            
            # İstek gönder
            cursor.execute("""
                INSERT OR IGNORE INTO friends 
                (user_id, friend_id, status)
                VALUES (?, ?, 'pending')
            """, (user_id, friend_id))
            
            conn.commit()
            print(f"✓ Arkadaş isteği gönderildi [{user_id} -> {friend_id}]")
            
            # Bildirim gönder
            cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
            requester_data = cursor.fetchone()
            if requester_data:
                requester_name = requester_data[0]
                
                self.notif_mgr.create_notification(
                    user_id=friend_id,
                    notification_type='friend_request',
                    title='Arkadaş İsteği',
                    message=f'{requester_name} seni arkadaş olarak ekledi',
                    icon='👥',
                    action_url=f'/profile/{user_id}',
                    metadata={'from_user_id': user_id}
                )
            
            return {'success': True, 'message': 'Arkadaş isteği gönderildi!'}
        
        except Exception as e:
            print(f"❌ Arkadaş ekleme hatası: {e}")
            return {'success': False, 'message': f'Hata: {str(e)}'}
        finally:
            conn.close()
    
    def confirm_friend_request(self, friendship_id: int) -> bool:
        """
        Arkadaş isteğini onayla.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE friends 
                SET status = 'confirmed', confirmed_at = ?
                WHERE friendship_id = ?
            """, (datetime.now().isoformat(), friendship_id))
            
            conn.commit()
            print(f"✓ Arkadaş isteği onaylandı [ID: {friendship_id}]")
            return True
        
        except Exception as e:
            print(f"❌ İstek onaylama hatası: {e}")
            return False
        finally:
            conn.close()
    
    def remove_friend(self, user_id: int, friend_id: int) -> bool:
        """
        Arkadaşı sil (çift yönlü).
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM friends 
                WHERE (user_id = ? AND friend_id = ?) 
                   OR (user_id = ? AND friend_id = ?)
            """, (user_id, friend_id, friend_id, user_id))
            
            conn.commit()
            print(f"✓ Arkadaş silindi [{user_id}, {friend_id}]")
            return True
        
        except Exception as e:
            print(f"❌ Arkadaş silme hatası: {e}")
            return False
        finally:
            conn.close()
    
    def get_friends(self, user_id: int, status: str = 'confirmed') -> List[Dict[str, Any]]:
        """
        Kullanıcının arkadaşlarını al.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        friends = []
        
        try:
            cursor.execute(f"""
                SELECT 
                    f.friendship_id,
                    f.friend_id,
                    u.username,
                    u.level,
                    f.status,
                    f.confirmed_at
                FROM friends f
                JOIN users u ON f.friend_id = u.user_id
                WHERE f.user_id = ? AND f.status = ?
                ORDER BY u.username ASC
            """, (user_id, status))
            
            for row in cursor.fetchall():
                friends.append({
                    'friendship_id': row[0],
                    'friend_id': row[1],
                    'friend_username': row[2],
                    'friend_level': row[3],
                    'status': row[4],
                    'confirmed_at': row[5]
                })
            
            return friends
        
        except Exception as e:
            print(f"❌ Arkadaş alma hatası: {e}")
            return friends
        finally:
            conn.close()
    
    def get_friend_requests(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Gelen arkadaş isteklerini al.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        requests = []
        
        try:
            cursor.execute("""
                SELECT 
                    f.friendship_id,
                    f.user_id,
                    u.username,
                    f.requested_at
                FROM friends f
                JOIN users u ON f.user_id = u.user_id
                WHERE f.friend_id = ? AND f.status = 'pending'
                ORDER BY f.requested_at DESC
            """, (user_id,))
            
            for row in cursor.fetchall():
                requests.append({
                    'friendship_id': row[0],
                    'requester_id': row[1],
                    'requester_username': row[2],
                    'requested_at': row[3]
                })
            
            return requests
        
        except Exception as e:
            print(f"❌ İstek alma hatası: {e}")
            return requests
        finally:
            conn.close()
    
    # ==================== BAŞARI PAYLAŞIMI ====================
    
    def share_achievement(
        self,
        user_id: int,
        achievement_name: str,
        friends_only: bool = True
    ) -> int:
        """
        Başarıyı paylaş (duvar/akış'a).
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Paylaşım tablosu oluştur
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shares (
                    share_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    achievement_name TEXT NOT NULL,
                    friends_only BOOLEAN DEFAULT 1,
                    shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            cursor.execute("""
                INSERT INTO shares 
                (user_id, achievement_name, friends_only)
                VALUES (?, ?, ?)
            """, (user_id, achievement_name, friends_only))
            
            conn.commit()
            share_id = cursor.lastrowid
            
            # Arkadaşlara bildirim gönder
            friends = self.get_friends(user_id)
            
            cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
            user_name = cursor.fetchone()[0]
            
            for friend in friends:
                self.notif_mgr.create_notification(
                    user_id=friend['friend_id'],
                    notification_type='friend_achievement',
                    title=f'{user_name} başarısı kazandı!',
                    message=f'{user_name} "{achievement_name}" başarısını açıklarındı',
                    icon='🎉',
                    action_url=f'/profile/{user_id}',
                    metadata={'achievement': achievement_name, 'user_id': user_id}
                )
            
            print(f"✓ Başarı paylaşıldı [ID: {share_id}]")
            return share_id
        
        except Exception as e:
            print(f"❌ Başarı paylaşma hatası: {e}")
            return -1
        finally:
            conn.close()
    
    def get_friend_activity_feed(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Arkadaşların aktivite akışını al.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        feed = []
        
        try:
            # Arkadaşların son girdilerini al
            cursor.execute("""
                SELECT 
                    ui.input_id,
                    ui.user_id,
                    u.username,
                    ui.input_type,
                    ui.score,
                    ui.is_correct,
                    ui.timestamp
                FROM user_inputs ui
                JOIN users u ON ui.user_id = u.user_id
                WHERE ui.user_id IN (
                    SELECT friend_id FROM friends 
                    WHERE user_id = ? AND status = 'confirmed'
                )
                ORDER BY ui.timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            
            for row in cursor.fetchall():
                activity_type = 'Doğru cevap' if row[5] else 'Yanlış cevap'
                
                feed.append({
                    'activity_id': row[0],
                    'friend_id': row[1],
                    'friend_username': row[2],
                    'activity_type': activity_type,
                    'input_type': row[3],
                    'score': row[4],
                    'timestamp': row[6]
                })
            
            return feed
        
        except Exception as e:
            print(f"❌ Aktivite akışı alma hatası: {e}")
            return feed
        finally:
            conn.close()
    
    # ==================== GRUP ÇALIŞMA ====================
    
    def create_study_group(
        self,
        creator_id: int,
        group_name: str,
        description: Optional[str] = None,
        is_public: bool = True
    ) -> int:
        """
        Grup çalışma oluştur.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Tablo oluştur
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_groups (
                    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_id INTEGER NOT NULL,
                    group_name TEXT NOT NULL,
                    description TEXT,
                    is_public BOOLEAN DEFAULT 1,
                    member_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (creator_id) REFERENCES users(user_id)
                )
            """)
            
            cursor.execute("""
                INSERT INTO study_groups 
                (creator_id, group_name, description, is_public)
                VALUES (?, ?, ?, ?)
            """, (creator_id, group_name, description, is_public))
            
            group_id = cursor.lastrowid
            
            # Grubu tablo
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_members (
                    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT DEFAULT 'member',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES study_groups(group_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(group_id, user_id)
                )
            """)
            
            # Oluşturucuyu üye olarak ekle
            cursor.execute("""
                INSERT INTO group_members 
                (group_id, user_id, role)
                VALUES (?, ?, 'admin')
            """, (group_id, creator_id))
            
            conn.commit()
            print(f"✓ Grup oluşturuldu [ID: {group_id}]")
            return group_id
        
        except Exception as e:
            print(f"❌ Grup oluşturma hatası: {e}")
            return -1
        finally:
            conn.close()
    
    def add_to_group(self, group_id: int, user_id: int) -> bool:
        """
        Gruba kullanıcı ekle.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO group_members 
                (group_id, user_id, role)
                VALUES (?, ?, 'member')
            """, (group_id, user_id))
            
            # Grup üye sayısını güncelle
            cursor.execute("""
                UPDATE study_groups 
                SET member_count = (SELECT COUNT(*) FROM group_members WHERE group_id = ?)
                WHERE group_id = ?
            """, (group_id, group_id))
            
            conn.commit()
            print(f"✓ Gruba kullanıcı eklendi [{group_id}, {user_id}]")
            return True
        
        except Exception as e:
            print(f"❌ Gruba ekleme hatası: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_groups(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Kullanıcının ait olduğu grupları al.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        groups = []
        
        try:
            cursor.execute("""
                SELECT 
                    sg.group_id,
                    sg.group_name,
                    sg.description,
                    COALESCE(sg.member_count, 1) as member_count,
                    CASE WHEN sg.is_private = 0 THEN 1 ELSE 0 END as is_public,
                    gm.role,
                    sg.created_at
                FROM study_groups sg
                JOIN group_members gm ON sg.group_id = gm.group_id
                WHERE gm.user_id = ?
                ORDER BY sg.created_at DESC
            """, (user_id,))
            
            for row in cursor.fetchall():
                groups.append({
                    'group_id': row[0],
                    'group_name': row[1],
                    'description': row[2],
                    'member_count': row[3],
                    'is_public': bool(row[4]),
                    'user_role': row[5],
                    'created_at': row[6]
                })
            
            return groups
        
        except Exception as e:
            print(f"❌ Grup alma hatası: {e}")
            return groups
        finally:
            conn.close()
    
    def get_group_members(self, group_id: int) -> List[Dict[str, Any]]:
        """
        Grubun üyelerini al.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        members = []
        
        try:
            cursor.execute("""
                SELECT 
                    gm.member_id,
                    gm.user_id,
                    u.username,
                    gm.role,
                    gm.joined_at
                FROM group_members gm
                JOIN users u ON gm.user_id = u.user_id
                WHERE gm.group_id = ?
                ORDER BY gm.role DESC, u.username ASC
            """, (group_id,))
            
            for row in cursor.fetchall():
                members.append({
                    'member_id': row[0],
                    'user_id': row[1],
                    'username': row[2],
                    'role': row[3],
                    'joined_at': row[4]
                })
            
            return members
        
        except Exception as e:
            print(f"❌ Üye alma hatası: {e}")
            return members
        finally:
            conn.close()
    
    # ==================== PROFIL ====================
    
    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Kullanıcı profilini al (sosyal bilgileriyle).
        """
        from features.user_stats import UserStats
        from features.leaderboard import LeaderboardManager
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT user_id, username, level, created_at FROM users WHERE user_id = ?
            """, (user_id,))
            
            user_row = cursor.fetchone()
            if not user_row:
                return {}
            
            stats = UserStats()
            lb = LeaderboardManager()
            
            profile = {
                'user_id': user_row[0],
                'username': user_row[1],
                'level': user_row[2],
                'created_at': user_row[3],
                'statistics': stats.get_overall_stats(user_id),
                'score': lb.calculate_user_score(user_id),
                'rank': lb.get_user_rank(user_id),
                'friends_count': len(self.get_friends(user_id)),
                'groups_count': len(self.get_user_groups(user_id)),
                'recent_activity': stats.get_user_recent_inputs(user_id, limit=10)
            }
            
            return profile
        
        except Exception as e:
            print(f"❌ Profil alma hatası: {e}")
            return {}
        finally:
            conn.close()


# ==================== KULLANIM ÖRNEKLERİ ====================

if __name__ == "__main__":
    social = SocialManager()
    
    # Arkadaş ekle
    # social.add_friend(user_id=1, friend_id=2)
    
    # Arkadaşları al
    # friends = social.get_friends(user_id=1)
    # print(json.dumps(friends, indent=2, default=str))
    
    print("✓ SocialManager modülü hazır")
