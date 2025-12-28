"""
goals.py

Kullanıcı hedefler ve milestones yönetimi.
user_stats'den ilerleme bilgisi alır.
"""

from db_utils import get_db_connection
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json


class GoalManager:
    """Kullanıcı hedeflerini ve milestones'ları yönetir."""
    
    def __init__(self):
        self.goal_types = {
            'daily_inputs': 'Günlük Input Sayısı',
            'weekly_inputs': 'Haftalık Input Sayısı',
            'accuracy': 'Doğruluk Yüzdesi',
            'streak_days': 'Ardışık Gün Sayısı',
            'study_hours': 'Çalışma Saati',
            'word_category': 'Kategori Tamamlama'
        }
    
    # ==================== HEDEF OLUŞTURMA ====================
    
    def create_goal(
        self,
        user_id: int,
        goal_type: str,
        target_value: float,
        deadline: str,  # YYYY-MM-DD
        title: str,
        description: Optional[str] = None
    ) -> int:
        """
        Yeni hedef oluştur.
        
        Args:
            user_id: Kullanıcı ID
            goal_type: Hedef tipi (daily_inputs, weekly_inputs vb.)
            target_value: Hedef değer
            deadline: Son tarih
            title: Hedef başlığı
            description: Açıklama
        
        Returns:
            Oluşturulan hedefin ID'si
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # goals tablosu var mı kontrol et
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    goal_type TEXT NOT NULL,
                    target_value REAL NOT NULL,
                    current_progress REAL DEFAULT 0,
                    title TEXT NOT NULL,
                    description TEXT,
                    deadline TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            cursor.execute("""
                INSERT INTO goals 
                (user_id, goal_type, target_value, title, description, deadline, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            """, (user_id, goal_type, target_value, title, description, deadline))
            
            conn.commit()
            goal_id = cursor.lastrowid
            print(f"✓ Hedef oluşturuldu [ID: {goal_id}]")
            return goal_id
        
        except Exception as e:
            print(f"❌ Hedef oluşturma hatası: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    # ==================== İLERLEME GÜNCELLE ====================
    
    def update_goal_progress(self, goal_id: int, new_progress: float) -> bool:
        """
        Hedefin ilerleme değerini güncelle.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT target_value, status FROM goals WHERE goal_id = ?
            """, (goal_id,))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            target_value, status = row
            
            # Hedef tamamlandı mı?
            new_status = status
            completed_at = None
            
            if new_progress >= target_value and status == 'active':
                new_status = 'completed'
                completed_at = datetime.now().isoformat()
                print(f"🎉 Hedef tamamlandı! [ID: {goal_id}]")
            
            cursor.execute("""
                UPDATE goals 
                SET current_progress = ?, status = ?, completed_at = ?
                WHERE goal_id = ?
            """, (new_progress, new_status, completed_at, goal_id))
            
            conn.commit()
            return True
        
        except Exception as e:
            print(f"❌ İlerleme güncelleme hatası: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # ==================== HEDEFLERİ AL ====================
    
    def get_active_goals(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Kullanıcının aktif hedeflerini al.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        goals = []
        
        try:
            cursor.execute("""
                SELECT goal_id, goal_type, target_value, current_progress, 
                       title, description, deadline, status, created_at
                FROM goals 
                WHERE user_id = ? AND status = 'active'
                ORDER BY deadline ASC
            """, (user_id,))
            
            for row in cursor.fetchall():
                progress_percent = (row[3] / row[2] * 100) if row[2] > 0 else 0
                
                goals.append({
                    'goal_id': row[0],
                    'goal_type': row[1],
                    'target_value': row[2],
                    'current_progress': row[3],
                    'progress_percent': round(progress_percent, 2),
                    'title': row[4],
                    'description': row[5],
                    'deadline': row[6],
                    'status': row[7],
                    'created_at': row[8],
                    'days_remaining': self._days_until_deadline(row[6])
                })
            
            return goals
        
        except Exception as e:
            print(f"❌ Aktif hedef alma hatası: {e}")
            return goals
        finally:
            conn.close()
    
    def get_completed_goals(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Kullanıcının tamamlanmış hedeflerini al.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        goals = []
        
        try:
            cursor.execute("""
                SELECT goal_id, goal_type, target_value, current_progress, 
                       title, deadline, status, completed_at
                FROM goals 
                WHERE user_id = ? AND status = 'completed'
                ORDER BY completed_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            for row in cursor.fetchall():
                goals.append({
                    'goal_id': row[0],
                    'goal_type': row[1],
                    'target_value': row[2],
                    'current_progress': row[3],
                    'title': row[4],
                    'deadline': row[5],
                    'status': row[6],
                    'completed_at': row[7]
                })
            
            return goals
        
        except Exception as e:
            print(f"❌ Tamamlanmış hedef alma hatası: {e}")
            return goals
        finally:
            conn.close()
    
    def get_all_goals(self, user_id: int) -> Dict[str, List]:
        """
        Kullanıcının tüm hedeflerini al (aktif + tamamlanmış).
        """
        return {
            'active': self.get_active_goals(user_id),
            'completed': self.get_completed_goals(user_id)
        }
    
    def delete_goal(self, goal_id: int, user_id: int) -> bool:
        """
        Hedefi sil (sadece kendi hedefini silebilir).
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Önce hedefin bu kullanıcıya ait olduğunu kontrol et
            cursor.execute("""
                SELECT user_id FROM goals WHERE goal_id = ?
            """, (goal_id,))
            
            row = cursor.fetchone()
            if not row or row[0] != user_id:
                print(f"❌ Hedef bulunamadı veya yetki yok [ID: {goal_id}]")
                return False
            
            # İlgili milestones'ları sil
            cursor.execute("DELETE FROM milestones WHERE goal_id = ?", (goal_id,))
            
            # Hedefi sil
            cursor.execute("DELETE FROM goals WHERE goal_id = ?", (goal_id,))
            
            conn.commit()
            print(f"✓ Hedef silindi [ID: {goal_id}]")
            return True
        
        except Exception as e:
            print(f"❌ Hedef silme hatası: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # ==================== MILESTONES ====================
    
    def get_milestones_for_goal(self, goal_id: int) -> List[Dict[str, Any]]:
        """
        Hedef için milestones'ları al.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        milestones = []
        
        try:
            # milestones tablosu oluştur
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS milestones (
                    milestone_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_id INTEGER NOT NULL,
                    milestone_value REAL NOT NULL,
                    milestone_label TEXT,
                    achieved BOOLEAN DEFAULT 0,
                    achieved_at TIMESTAMP,
                    FOREIGN KEY (goal_id) REFERENCES goals(goal_id)
                )
            """)
            
            cursor.execute("""
                SELECT milestone_id, milestone_value, milestone_label, achieved, achieved_at
                FROM milestones 
                WHERE goal_id = ?
                ORDER BY milestone_value ASC
            """, (goal_id,))
            
            for row in cursor.fetchall():
                milestones.append({
                    'milestone_id': row[0],
                    'milestone_value': row[1],
                    'milestone_label': row[2],
                    'achieved': bool(row[3]),
                    'achieved_at': row[4]
                })
            
            return milestones
        
        except Exception as e:
            print(f"❌ Milestone alma hatası: {e}")
            return milestones
        finally:
            conn.close()
    
    def create_milestone(
        self,
        goal_id: int,
        milestone_value: float,
        label: str
    ) -> int:
        """
        Hedef için milestone oluştur.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO milestones 
                (goal_id, milestone_value, milestone_label)
                VALUES (?, ?, ?)
            """, (goal_id, milestone_value, label))
            
            conn.commit()
            return cursor.lastrowid
        
        except Exception as e:
            print(f"❌ Milestone oluşturma hatası: {e}")
            return -1
        finally:
            conn.close()
    
    # ==================== ÖZELLİKLERİ ====================
    
    def get_goal_suggestions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Kullanıcı istatistiklerine göre hedef önerileri yap.
        """
        # user_stats'ten veri almak için
        from features.user_stats import UserStats
        
        stats_manager = UserStats()
        daily_stats = stats_manager.get_daily_stats(user_id)
        weekly_stats = stats_manager.get_weekly_stats(user_id)
        overall_stats = stats_manager.get_overall_stats(user_id)
        
        suggestions = []
        
        # Günlük input hedefi
        if daily_stats['total_inputs'] > 0:
            suggestions.append({
                'type': 'daily_inputs',
                'title': f"Bugün {daily_stats['total_inputs'] + 10} input yap",
                'description': 'Bugünkü performansını %5 oranında artır',
                'suggested_value': daily_stats['total_inputs'] + 10,
                'deadline': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            })
        
        # Haftalık input hedefi
        if weekly_stats['total_inputs'] > 0:
            suggestions.append({
                'type': 'weekly_inputs',
                'title': f"Bu hafta {weekly_stats['total_inputs'] + 50} input yap",
                'description': 'Haftalık çalışmanı biraz daha arttır',
                'suggested_value': weekly_stats['total_inputs'] + 50,
                'deadline': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            })
        
        # Doğruluk hedefi
        current_accuracy = overall_stats.get('accuracy_percent', 0)
        if current_accuracy < 90:
            suggestions.append({
                'type': 'accuracy',
                'title': f"Doğruluk oranını %{current_accuracy + 10} yap",
                'description': 'Kaliteye daha çok odaklan',
                'suggested_value': current_accuracy + 10,
                'deadline': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            })
        
        # Streak hedefi
        suggestions.append({
            'type': 'streak_days',
            'title': '7 gün ardışık giriş yap',
            'description': '1 hafta boyunca her gün en az bir çalışma oturumu',
            'suggested_value': 7,
            'deadline': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        })
        
        return suggestions
    
    # ==================== YARDIMCI METODLAR ====================
    
    def _days_until_deadline(self, deadline_str: str) -> int:
        """
        Deadline'a kalan gün sayısını hesapla.
        """
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            today = datetime.now().date()
            return (deadline - today).days
        except:
            return 0
    
    def sync_goal_progress(self, user_id: int) -> int:
        """
        Kullanıcının aktif hedeflerinin ilerleme değerlerini güncelle.
        Kullanıcı her pratik yaptığında çağrılmalı.
        
        Returns:
            Güncellenen hedef sayısı
        """
        from features.user_stats import UserStats
        
        stats = UserStats()
        daily = stats.get_daily_stats(user_id)
        weekly = stats.get_weekly_stats(user_id)
        overall = stats.get_overall_stats(user_id)
        
        active_goals = self.get_active_goals(user_id)
        updated = 0
        
        for goal in active_goals:
            new_progress = goal['current_progress']
            
            if goal['goal_type'] == 'daily_inputs':
                new_progress = daily.get('total_inputs', 0)
            elif goal['goal_type'] == 'weekly_inputs':
                new_progress = weekly.get('total_inputs', 0)
            elif goal['goal_type'] == 'accuracy':
                new_progress = overall.get('accuracy_percent', 0)
            elif goal['goal_type'] == 'word_count':
                new_progress = overall.get('total_inputs', 0)
            
            if new_progress != goal['current_progress']:
                self.update_goal_progress(goal['goal_id'], new_progress)
                updated += 1
        
        return updated


# ==================== KULLANIM ÖRNEKLERİ ====================

if __name__ == "__main__":
    goal_mgr = GoalManager()
    
    # Hedef oluştur
    # goal_id = goal_mgr.create_goal(
    #     user_id=1,
    #     goal_type='daily_inputs',
    #     target_value=50,
    #     deadline='2026-01-01',
    #     title='Günlük 50 input',
    #     description='Her gün 50 input yap'
    # )
    
    # Hedefler al
    # all_goals = goal_mgr.get_all_goals(user_id=1)
    # print(json.dumps(all_goals, indent=2, default=str))
    
    print("✓ GoalManager modülü hazır")
