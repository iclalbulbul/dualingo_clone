# 🚀 Features Modülü - Hızlı Başlangıç Rehberi

Tüm dosyalar birbiriyle bağlantılı şekilde oluşturulmuştur. İşte kullanım rehberi:

## 📁 Dosya Yapısı

```
features/
├── __init__.py              # Modül başlatma
├── user_stats.py           # İstatistikler & Raporlar
├── goals.py                # Hedefler & Milestones
├── leaderboard.py          # Sıralamalar & Puanlar
├── notifications.py        # Bildirim Sistemi
└── social.py              # Arkadaş & Grup Yönetimi
```

## 🔗 Bağlantı Haritası

```
app.py (routes)
  ├→ user_stats.py (istatistik hesaplama)
  │   └→ user_db.py (veri kaynaği)
  │
  ├→ goals.py (hedef yönetimi)
  │   └→ user_stats.py (ilerleme takibi)
  │       └→ notifications.py (bildirimleri tetikle)
  │
  ├→ leaderboard.py (sıramalar)
  │   ├→ user_stats.py (puan hesabı)
  │   └→ social.py (arkadaş sıralaması)
  │       └→ notifications.py (rütbe değişimi bildirimi)
  │
  ├→ notifications.py (bildirimler)
  │   ├→ user_stats.py (hedef bildirimleri)
  │   └→ goals.py (hedef tamamlama bildirimi)
  │
  └→ social.py (sosyal)
      ├→ notifications.py (arkadaş bildirimleri)
      ├→ user_stats.py (profil verileri)
      └→ leaderboard.py (arkadaş sıralaması)
```

## 📱 Rotalar (app.py'de)

### İstatistikler
- `GET /stats` - Günlük, haftalık, aylık istatistikler

### Hedefler
- `GET /goals` - Aktif ve tamamlanmış hedefler
- `POST /goals` - Yeni hedef oluştur

### Sıralamalar
- `GET /leaderboard` - Global sıralama
- `GET /leaderboard?period=weekly` - Haftalık sıralama
- `GET /leaderboard?period=monthly` - Aylık sıralama

### Bildirimler
- `GET /notifications` - Tüm bildirimler
- `POST /notification/<id>/read` - Bildirimi oku

### Sosyal
- `GET /profile/<user_id>` - Kullanıcı profili
- `GET /friends` - Arkadaşlar ve istek listesi
- `POST /add-friend/<friend_id>` - Arkadaş ekle
- `POST /friend-request/<id>/confirm` - İstek onayla

## 💻 Python Kullanımı

### UserStats - İstatistikler
```python
from features.user_stats import UserStats

stats = UserStats()

# Günlük istatistikler
daily = stats.get_daily_stats(user_id=1)

# Haftalık rapor
weekly_report = stats.generate_weekly_report(user_id=1)

# Kelime performansı
word_perf = stats.get_word_stats(user_id=1)
```

### GoalManager - Hedefler
```python
from features.goals import GoalManager

goal_mgr = GoalManager()

# Yeni hedef
goal_id = goal_mgr.create_goal(
    user_id=1,
    goal_type='daily_inputs',
    target_value=50,
    deadline='2026-01-15',
    title='Günlük 50 input'
)

# İlerleme güncelle
goal_mgr.update_goal_progress(goal_id, 35)

# Hedefleri al
all_goals = goal_mgr.get_all_goals(user_id=1)
```

### LeaderboardManager - Sıralamalar
```python
from features.leaderboard import LeaderboardManager

lb = LeaderboardManager()

# Global sıralama
leaderboard = lb.get_global_leaderboard(limit=50)

# Kullanıcı puanı
score = lb.calculate_user_score(user_id=1)

# Kullanıcının sırası
rank = lb.get_user_rank(user_id=1, period='all')

# Arkadaş sıralaması
friends_lb = lb.get_friends_leaderboard(user_id=1)
```

### NotificationManager - Bildirimler
```python
from features.notifications import NotificationManager

notif = NotificationManager()

# Bildirim oluştur
notif_id = notif.create_notification(
    user_id=1,
    notification_type='achievement',
    title='Başarı Kazandın!',
    message='100 doğru cevap!',
    icon='🎉'
)

# Bildirimleri al
user_notifications = notif.get_user_notifications(user_id=1)

# Otomatik bildirimleri tetikle
notif.check_and_trigger_notifications(user_id=1)
```

### SocialManager - Sosyal
```python
from features.social import SocialManager

social = SocialManager()

# Arkadaş ekle
social.add_friend(user_id=1, friend_id=2)

# Arkadaş isteğini onayla
social.confirm_friend_request(friendship_id=5)

# Arkadaşları al
friends = social.get_friends(user_id=1)

# Profil al
profile = social.get_user_profile(user_id=1)

# Grup oluştur
group_id = social.create_study_group(
    creator_id=1,
    group_name='İngilizce Çalışma Grubu',
    is_public=True
)
```

## 🎯 Örnek Workflow'lar

### 1. Kullanıcı Giriş Yaptığında
```python
# app.py'deki login route'unda:
logger.log_session_start(user_id)
notification_manager.check_and_trigger_notifications(user_id)
```

### 2. Kullanıcı Çeviri Yaptığında
```python
# app.py'deki practice_word route'unda:
logger.log_translation_attempt(...)
goal_manager.update_goal_progress(...)  # Hedef ilerle
notification_manager.check_and_trigger_notifications(...)  # Bildirim kontrol
```

### 3. Haftayı Gözlemle
```python
stats = stats_manager.get_weekly_stats(user_id)
weekly_report = stats_manager.generate_weekly_report(user_id)
# Raporun önerilerini kullanıcıya göster
```

### 4. Arkadaş Aktivitesini Takip Et
```python
activity = social_manager.get_friend_activity_feed(user_id)
# Aktiviteyi göster
```

## 🔧 Veri Tabanı Tabloları

Otomatik olarak oluşturulan tablolar:

1. **goals** - Hedefler
2. **milestones** - Hedef alt görevleri
3. **notifications** - Bildirimler
4. **friends** - Arkadaş ilişkileri
5. **shares** - Başarı paylaşımları
6. **study_groups** - Çalışma grupları
7. **group_members** - Grup üyelikleri

## 📊 HTML Templates

Oluşturulan sayfalar:

- `stats.html` - İstatistikler
- `goals.html` - Hedefler
- `leaderboard.html` - Sıralamalar
- `notifications.html` - Bildirimler
- `friends.html` - Arkadaşlar
- `profile.html` - Profil

## 🐛 Sorun Giderme

**Eğer import hatası alırsan:**
```python
# features/ klasöründe __init__.py olduğundan emin ol
# app.py'de import'ları kontrol et
from features.user_stats import UserStats
from features.goals import GoalManager
# vs.
```

**Eğer tablo hatası alırsan:**
```python
# Tabloları manuel oluştur:
from db_utils import init_db
init_db()
```

**Eğer veri bulamazsan:**
```python
# user_db.py ile veri kaydedildiğinden emin ol
logger.log_user_input(user_id, ...)
logger.log_user_action(user_id, ...)
```

## 🚀 Sonraki Adımlar

1. ✅ Features modülü tamamlandı
2. ⬜ API endpoints'leri (REST API)
3. ⬜ Grafikler (Chart.js / Plotly)
4. ⬜ Email bildirimleri
5. ⬜ Mobile app API'sı

---

**Tüm modüller birbiriyle bağlantılı ve senkronize çalışmaktadır! 🎉**
