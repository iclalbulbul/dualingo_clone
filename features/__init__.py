"""
features modülü - Gelişmiş özellikler

Bu modül aşağıdaki özellikleri içerir:
- user_stats: Kullanıcı istatistikleri ve raporlar
- goals: Hedefler ve milestones
- courses: Ders/kurs sistemi ve ilerleme takibi
- leaderboard: Sıralamalar
- notifications: Bildirim sistemi
- social: Sosyal özellikleri (arkadaş, paylaşım)

Tüm modüller user_db.py'den veri alır ve birbiriyle bağlantılıdır.
"""

from .user_stats import UserStats
from .goals import GoalManager
from .courses import CourseManager
from .leaderboard import LeaderboardManager
from .notifications import NotificationManager
from .social import SocialManager

__all__ = [
    'UserStats',
    'GoalManager',
    'CourseManager',
    'LeaderboardManager',
    'NotificationManager',
    'SocialManager'
]
