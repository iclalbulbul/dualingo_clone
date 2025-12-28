"""
user_stats.py

Kullanıcı istatistikleri ve raporlar.
user_db modülünden veri alır ve analiz eder.
"""

from user_db import UserInputLogger
from db_utils import get_db_connection
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json


class UserStats:
    """Kullanıcı istatistikleri ve raporları yönetir."""
    
    def __init__(self):
        self.logger = UserInputLogger()
        self.db_path = None
    
    # ==================== GÜNLÜK İSTATİSTİKLER ====================
    
    def get_daily_stats(self, user_id: int, date: str = None) -> Dict[str, Any]:
        """
        Belirli bir gün için istatistikleri döndür.
        
        Args:
            user_id: Kullanıcı ID
            date: Tarih (YYYY-MM-DD formatı). None ise bugün
        
        Returns:
            Günlük istatistikler
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {
            'date': date,
            'total_inputs': 0,
            'correct_answers': 0,
            'accuracy_percent': 0,
            'total_sessions': 0,
            'total_minutes': 0,
            'input_types': {},
            'sessions': []
        }
        
        try:
            # O gün başlangıcı ve bitişi
            start_date = f"{date}T00:00:00"
            end_date = f"{date}T23:59:59"
            
            # Günlük girişler
            cursor.execute("""
                SELECT COUNT(*), SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END)
                FROM user_inputs 
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
            """, (user_id, start_date, end_date))
            
            row = cursor.fetchone()
            if row:
                stats['total_inputs'] = row[0] or 0
                correct = row[1] or 0
                stats['correct_answers'] = correct
                if stats['total_inputs'] > 0:
                    stats['accuracy_percent'] = round((correct / stats['total_inputs']) * 100, 2)
            
            # Giriş türlerine göre dağılım
            cursor.execute("""
                SELECT input_type, COUNT(*) as count
                FROM user_inputs 
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
                GROUP BY input_type
            """, (user_id, start_date, end_date))
            
            for row in cursor.fetchall():
                stats['input_types'][row[0]] = row[1]
            
            # Oturum bilgileri
            cursor.execute("""
                SELECT session_id, login_time, session_duration_minutes
                FROM session_logs 
                WHERE user_id = ? AND DATE(login_time) = ?
            """, (user_id, date))
            
            sessions = cursor.fetchall()
            stats['total_sessions'] = len(sessions)
            stats['total_minutes'] = sum([s[2] or 0 for s in sessions])
            
            for session in sessions:
                stats['sessions'].append({
                    'session_id': session[0],
                    'login_time': session[1],
                    'duration_minutes': session[2]
                })
            
            # Streak hesapla
            stats['streak'] = self._calculate_streak(user_id)
            
            return stats
        
        except Exception as e:
            print(f"❌ Günlük istatistik hatası: {e}")
            return stats
        finally:
            conn.close()
    
    # ==================== HAFTALIK İSTATİSTİKLER ====================
    
    def get_weekly_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Son 7 günlük istatistikleri döndür.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        stats = {
            'week_start': week_ago,
            'week_end': datetime.now().isoformat(),
            'total_inputs': 0,
            'correct_answers': 0,
            'accuracy_percent': 0,
            'total_minutes': 0,
            'daily_breakdown': {},
            'best_day': None,
            'streak_days': 0,
            'most_practiced_type': None
        }
        
        try:
            # Haftalık toplam girişler
            cursor.execute("""
                SELECT COUNT(*), SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END)
                FROM user_inputs 
                WHERE user_id = ? AND timestamp > ?
            """, (user_id, week_ago))
            
            row = cursor.fetchone()
            if row:
                stats['total_inputs'] = row[0] or 0
                correct = row[1] or 0
                stats['correct_answers'] = correct
                if stats['total_inputs'] > 0:
                    stats['accuracy_percent'] = round((correct / stats['total_inputs']) * 100, 2)
            
            # Günlere göre dağılım
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                daily = self.get_daily_stats(user_id, date)
                stats['daily_breakdown'][date] = {
                    'inputs': daily['total_inputs'],
                    'accuracy': daily['accuracy_percent'],
                    'minutes': daily['total_minutes']
                }
            
            # En iyi gün
            best_date = max(stats['daily_breakdown'].items(), 
                          key=lambda x: x[1]['inputs'])
            stats['best_day'] = best_date[0]
            
            # Toplam dakika
            cursor.execute("""
                SELECT SUM(session_duration_minutes)
                FROM session_logs 
                WHERE user_id = ? AND login_time > ?
            """, (user_id, week_ago))
            
            minutes = cursor.fetchone()[0]
            stats['total_minutes'] = minutes or 0
            
            # Giriş tipi dağılımı
            cursor.execute("""
                SELECT input_type, COUNT(*) as count
                FROM user_inputs 
                WHERE user_id = ? AND timestamp > ?
                GROUP BY input_type
                ORDER BY count DESC
                LIMIT 1
            """, (user_id, week_ago))
            
            row = cursor.fetchone()
            if row:
                stats['most_practiced_type'] = row[0]
            
            # Ardışık gün sayısı (Streak)
            stats['streak_days'] = self._calculate_streak(user_id)
            
            return stats
        
        except Exception as e:
            print(f"❌ Haftalık istatistik hatası: {e}")
            return stats
        finally:
            conn.close()
    
    # ==================== AYLIK İSTATİSTİKLER ====================
    
    def get_monthly_stats(self, user_id: int, year: int = None, month: int = None) -> Dict[str, Any]:
        """
        Aylık istatistikleri döndür.
        """
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ay başlangıcı ve bitişi
        if month == 12:
            next_month = (datetime(year, month, 1) + timedelta(days=32)).replace(day=1)
        else:
            next_month = datetime(year, month + 1, 1)
        
        month_start = datetime(year, month, 1).isoformat()
        month_end = next_month.isoformat()
        
        stats = {
            'year': year,
            'month': month,
            'total_inputs': 0,
            'correct_answers': 0,
            'accuracy_percent': 0,
            'total_minutes': 0,
            'total_sessions': 0,
            'daily_data': []
        }
        
        try:
            cursor.execute("""
                SELECT COUNT(*), SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END)
                FROM user_inputs 
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
            """, (user_id, month_start, month_end))
            
            row = cursor.fetchone()
            if row:
                stats['total_inputs'] = row[0] or 0
                correct = row[1] or 0
                stats['correct_answers'] = correct
                if stats['total_inputs'] > 0:
                    stats['accuracy_percent'] = round((correct / stats['total_inputs']) * 100, 2)
            
            # Toplam dakika
            cursor.execute("""
                SELECT SUM(session_duration_minutes)
                FROM session_logs 
                WHERE user_id = ? AND login_time BETWEEN ? AND ?
            """, (user_id, month_start, month_end))
            
            minutes = cursor.fetchone()[0]
            stats['total_minutes'] = minutes or 0
            
            # Oturum sayısı
            cursor.execute("""
                SELECT COUNT(*) FROM session_logs 
                WHERE user_id = ? AND login_time BETWEEN ? AND ?
            """, (user_id, month_start, month_end))
            
            stats['total_sessions'] = cursor.fetchone()[0] or 0
            
            # Günlere göre veri
            for day in range(1, 32):
                try:
                    date = datetime(year, month, day).strftime('%Y-%m-%d')
                    daily = self.get_daily_stats(user_id, date)
                    stats['daily_data'].append({
                        'date': date,
                        'inputs': daily['total_inputs'],
                        'accuracy': daily['accuracy_percent'],
                        'minutes': daily['total_minutes']
                    })
                except:
                    break
            
            return stats
        
        except Exception as e:
            print(f"❌ Aylık istatistik hatası: {e}")
            return stats
        finally:
            conn.close()
    
    # ==================== GENEL İSTATİSTİKLER ====================
    
    def get_overall_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Tüm zamanın istatistiklerini döndür.
        """
        return self.logger.get_user_statistics(user_id)
    
    def get_word_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Kelime performans istatistikleri.
        """
        return self.logger.get_word_performance(user_id)
    
    def get_user_recent_inputs(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Kullanıcının son aktivitelerini döndür.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        activities = []
        
        try:
            cursor.execute("""
                SELECT input_type, input_text, is_correct, score, timestamp
                FROM user_inputs 
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            
            for row in cursor.fetchall():
                activities.append({
                    'type': row[0],
                    'input': row[1][:50] if row[1] else '',
                    'is_correct': bool(row[2]),
                    'score': row[3],
                    'timestamp': row[4]
                })
            
            return activities
        
        except Exception as e:
            print(f"❌ Aktivite alma hatası: {e}")
            return activities
        finally:
            conn.close()
    
    # ==================== RAPORLAR ====================
    
    def generate_weekly_report(self, user_id: int) -> Dict[str, Any]:
        """
        Haftalık rapor oluştur.
        """
        weekly = self.get_weekly_stats(user_id)
        overall = self.get_overall_stats(user_id)
        word_perf = self.get_word_stats(user_id)
        
        report = {
            'type': 'weekly_report',
            'generated_at': datetime.now().isoformat(),
            'user_id': user_id,
            
            'summary': {
                'total_inputs': weekly['total_inputs'],
                'accuracy': weekly['accuracy_percent'],
                'total_hours': round(weekly['total_minutes'] / 60, 1),
                'streak_days': weekly['streak_days'],
                'improvement': self._calculate_improvement(user_id, 7)
            },
            
            'detailed_stats': weekly,
            
            'word_performance': {
                'total_translations': word_perf['total_translations'],
                'accuracy': word_perf['accuracy'],
                'hardest_words': word_perf['hardest_words'][:3],
                'easiest_words': word_perf['easiest_words'][:3]
            },
            
            'achievements': self._get_weekly_achievements(user_id),
            'recommendations': self._generate_recommendations(user_id)
        }
        
        return report
    
    def generate_monthly_report(self, user_id: int, year: int = None, month: int = None) -> Dict[str, Any]:
        """
        Aylık rapor oluştur.
        """
        monthly = self.get_monthly_stats(user_id, year, month)
        overall = self.get_overall_stats(user_id)
        word_perf = self.get_word_stats(user_id)
        
        report = {
            'type': 'monthly_report',
            'generated_at': datetime.now().isoformat(),
            'user_id': user_id,
            
            'summary': {
                'total_inputs': monthly['total_inputs'],
                'accuracy': monthly['accuracy_percent'],
                'total_hours': round(monthly['total_minutes'] / 60, 1),
                'total_sessions': monthly['total_sessions'],
                'improvement': self._calculate_improvement(user_id, 30)
            },
            
            'detailed_stats': monthly,
            
            'word_performance': {
                'total_translations': word_perf['total_translations'],
                'accuracy': word_perf['accuracy'],
                'most_practiced': word_perf['most_practiced_words'][:5],
                'hardest_words': word_perf['hardest_words'][:5]
            },
            
            'achievements': self._get_monthly_achievements(user_id),
            'recommendations': self._generate_recommendations(user_id)
        }
        
        return report
    
    # ==================== YARDIMCI METODLAR ====================
    
    def _calculate_streak(self, user_id: int) -> int:
        """
        Ardışık giriş yapılan gün sayısını hesapla.
        user_inputs tablosundan kontrol eder.
        
        Mantık:
        - Bugün aktivite varsa, bugünden geriye say
        - Bugün aktivite yoksa ama dün varsa, dünden geriye say (streak devam ediyor)
        - Her ikisi de yoksa streak = 0
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            streak = 0
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            # Bugün aktivite var mı?
            cursor.execute("""
                SELECT COUNT(*) FROM user_inputs 
                WHERE user_id = ? AND DATE(timestamp) = ?
            """, (user_id, today.isoformat()))
            today_has_activity = cursor.fetchone()[0] > 0
            
            # Dün aktivite var mı?
            cursor.execute("""
                SELECT COUNT(*) FROM user_inputs 
                WHERE user_id = ? AND DATE(timestamp) = ?
            """, (user_id, yesterday.isoformat()))
            yesterday_has_activity = cursor.fetchone()[0] > 0
            
            # Başlangıç gününü belirle
            if today_has_activity:
                # Bugün aktivite var, bugünden başla
                start_offset = 0
            elif yesterday_has_activity:
                # Bugün yok ama dün var, dünden başla (streak kırılmamış)
                start_offset = 1
            else:
                # Ne bugün ne dün aktivite yok, streak 0
                return 0
            
            # Ardışık günleri say
            for i in range(start_offset, 365):
                check_date = (today - timedelta(days=i)).isoformat()
                
                cursor.execute("""
                    SELECT COUNT(*) FROM user_inputs 
                    WHERE user_id = ? AND DATE(timestamp) = ?
                """, (user_id, check_date))
                
                if cursor.fetchone()[0] == 0:
                    break
                streak += 1
            
            return streak
        finally:
            conn.close()
    
    def _calculate_improvement(self, user_id: int, days: int) -> float:
        """
        Belirli gün içinde doğruluk iyileşmesini hesapla (%).
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            # İlk gün ve son gün doğruluk oranı
            cursor.execute("""
                SELECT accuracy_percent 
                FROM (
                    SELECT 
                        (SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) / 
                         COUNT(*) * 100) as accuracy_percent,
                        DATE(timestamp) as date
                    FROM user_inputs 
                    WHERE user_id = ? AND timestamp > ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date ASC
                )
                LIMIT 1
            """, (user_id, cutoff))
            
            first_day = cursor.fetchone()
            
            cursor.execute("""
                SELECT accuracy_percent 
                FROM (
                    SELECT 
                        (SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) / 
                         COUNT(*) * 100) as accuracy_percent,
                        DATE(timestamp) as date
                    FROM user_inputs 
                    WHERE user_id = ? AND timestamp > ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                )
                LIMIT 1
            """, (user_id, cutoff))
            
            last_day = cursor.fetchone()
            
            if first_day and last_day and first_day[0]:
                improvement = ((last_day[0] - first_day[0]) / first_day[0]) * 100
                return round(improvement, 2)
            
            return 0.0
        finally:
            conn.close()
    
    def _get_weekly_achievements(self, user_id: int) -> List[str]:
        """
        Bu hafta kazanılan başarıları döndür.
        """
        weekly = self.get_weekly_stats(user_id)
        achievements = []
        
        if weekly['total_inputs'] >= 100:
            achievements.append('🎉 100 Input Başarısı')
        
        if weekly['accuracy_percent'] >= 90:
            achievements.append('⭐ %90 Doğruluk')
        
        if weekly['streak_days'] >= 7:
            achievements.append('🔥 1 Haftalık Streak')
        
        if weekly['total_minutes'] >= 420:  # 7 saat
            achievements.append('⏰ 7 Saatlik Çalışma')
        
        return achievements
    
    def _get_monthly_achievements(self, user_id: int) -> List[str]:
        """
        Bu ay kazanılan başarıları döndür.
        """
        monthly = self.get_monthly_stats(user_id)
        achievements = []
        
        if monthly['total_inputs'] >= 500:
            achievements.append('🏆 500 Input Başarısı')
        
        if monthly['accuracy_percent'] >= 85:
            achievements.append('💎 %85 Doğruluk')
        
        if monthly['total_sessions'] >= 20:
            achievements.append('📚 20 Oturum')
        
        if monthly['total_minutes'] >= 3000:  # 50 saat
            achievements.append('🚀 50 Saatlik Çalışma')
        
        return achievements
    
    def _generate_recommendations(self, user_id: int) -> List[str]:
        """
        Kullanıcıya öneriler üret.
        """
        word_perf = self.get_word_stats(user_id)
        stats = self.get_overall_stats(user_id)
        
        recommendations = []
        
        # Zayıf kelimeler
        if word_perf['hardest_words']:
            hardest = word_perf['hardest_words'][0]['word']
            recommendations.append(f"💪 '{hardest}' kelimesini daha çok pratik yap")
        
        # Doğruluk
        if stats['accuracy_percent'] < 70:
            recommendations.append("📖 Hızlı olmaktan ziyade kaliteye odaklan")
        elif stats['accuracy_percent'] >= 90:
            recommendations.append("⚡ Hızını arttırarak zorluk seviyesini yükselt")
        
        # Telaffuz
        if stats['average_pronunciation_score'] < 75:
            recommendations.append("🎤 Telaffuz pratiğine daha fazla zaman ayır")
        
        return recommendations


# ==================== KULLANIM ÖRNEKLERİ ====================

if __name__ == "__main__":
    stats = UserStats()
    
    # Günlük istatistikler
    # daily = stats.get_daily_stats(user_id=1)
    # print(json.dumps(daily, indent=2))
    
    # Haftalık rapor
    # report = stats.generate_weekly_report(user_id=1)
    # print(json.dumps(report, indent=2))
    
    print("✓ UserStats modülü hazır")
