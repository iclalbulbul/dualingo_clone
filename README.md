# 🦉 LoroLeng - Türkçe Dil Öğrenme Platformu

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.0+-green?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-blue?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**Duolingo benzeri, yapay zeka destekli İngilizce öğrenme uygulaması**

[Özellikler](#-özellikler) • [Kurulum](#-kurulum) • [Kullanım](#-kullanım) • [Ekran Görüntüleri](#-ekran-görüntüleri) • [API](#-api)

</div>

---

## 🎯 Proje Hakkında

LoroLeng, Türkçe konuşanlar için tasarlanmış kapsamlı bir İngilizce öğrenme platformudur. CEFR (Avrupa Dil Referans Çerçevesi) standartlarına uygun A1'den B2'ye kadar seviyelerde içerik sunar.

### ✨ Neden LoroLeng?

- 🤖 **Yapay Zeka Destekli** - Google Gemini ile akıllı geri bildirim
- 🎤 **Telaffuz Pratiği** - Sesli tanıma ile konuşma egzersizleri
- 📊 **Detaylı İstatistikler** - İlerlemenizi takip edin
- 🏆 **Oyunlaştırma** - XP, taç, liderlik tablosu
- 👥 **Sosyal Özellikler** - Arkadaş ekle, çalışma grupları

---

## 🚀 Özellikler

### 📚 Kurs Sistemi
- **CEFR Seviyeleri**: A1, A2, B1, B2
- **Üniteler & Dersler**: Yapılandırılmış öğrenme yolu
- **Kelime Öğrenme**: 30+ kategoride binlerce kelime
- **Gramer Kuralları**: Kapsamlı dilbilgisi içeriği

### 🎮 Oyunlaştırma
- 🔥 **Streak Sistemi**: Ardışık gün sayacı
- ⭐ **XP Puanları**: Her aktivitede puan kazan
- ❤️ **Kalp Sistemi**: Hata yaparsan kalp kaybedersin
- 🏅 **Rozetler**: Başarılarını sergile

### 📈 İstatistikler & Raporlar
- Günlük/Haftalık/Aylık istatistikler
- Doğruluk oranı takibi
- Zayıf kelime analizi
- İlerleme grafikleri

### 🎤 Telaffuz
- Web Speech API entegrasyonu
- Sesli kelime/cümle pratiği
- Anlık geri bildirim

### 👥 Sosyal Özellikler
- Arkadaş ekleme
- Liderlik tablosu
- Bildirim sistemi

### 🎯 Hedefler
- Kişisel hedef belirleme
- Günlük/haftalık hedefler
- İlerleme takibi

---

## 🛠 Teknolojiler

| Kategori | Teknoloji |
|----------|-----------|
| **Backend** | Python 3.11+, Flask |
| **Veritabanı** | SQLite (WAL mode) |
| **Frontend** | HTML5, CSS3, JavaScript |
| **AI** | Google Gemini API |
| **Çeviri** | Deep Translator |
| **Ses** | Web Speech API |

---

## 📦 Kurulum

### Gereksinimler

- Python 3.11 veya üzeri
- pip (Python paket yöneticisi)

### Adımlar

1. **Repoyu klonlayın**
```bash
git clone https://github.com/yourusername/LoroLeng.git
cd LoroLeng
```

2. **Sanal ortam oluşturun (önerilen)**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Bağımlılıkları yükleyin**
```bash
pip install flask deep-translator google-generativeai
```

4. **Ortam değişkenlerini ayarlayın**
```bash
# Windows PowerShell
$env:SECRET_KEY="your-secret-key-here"
$env:GEMINI_API_KEY="your-gemini-api-key"

# Linux/Mac
export SECRET_KEY="your-secret-key-here"
export GEMINI_API_KEY="your-gemini-api-key"
```

5. **Veritabanını hazırlayın**
```bash
python scripts/seed_course_system.py
python scripts/import_words.py
```

6. **Uygulamayı başlatın**
```bash
python app.py
```

7. **Tarayıcıda açın**
```
http://localhost:5000
```

---

## 📁 Proje Yapısı

```
LoroLeng/
├── 📄 app.py                 # Ana Flask uygulaması
├── 📄 db_utils.py            # Veritabanı yardımcıları
├── 📄 user_db.py             # Kullanıcı veritabanı işlemleri
├── 📄 translation_utils.py   # Çeviri yardımcıları
│
├── 📁 backend/
│   ├── ai_utils.py           # Gemini AI entegrasyonu
│   ├── lesson_flow.py        # Ders akışı mantığı
│   ├── recommender.py        # Kelime öneri sistemi
│   ├── rules.py              # Gramer kuralları
│   ├── speech_utils.py       # Telaffuz yardımcıları
│   └── tracker.py            # İlerleme takibi
│
├── 📁 features/
│   ├── course_system.py      # CEFR kurs sistemi
│   ├── courses.py            # Kurs yönetimi
│   ├── goals.py              # Hedef sistemi
│   ├── leaderboard.py        # Liderlik tablosu
│   ├── notifications.py      # Bildirimler
│   ├── social.py             # Sosyal özellikler
│   └── user_stats.py         # Kullanıcı istatistikleri
│
├── 📁 templates/             # Jinja2 HTML şablonları
│   ├── base.html
│   ├── dashboard.html
│   ├── learn.html
│   ├── courses.html
│   └── ...
│
├── 📁 static/
│   ├── style.css             # Ana stil dosyası
│   └── images/               # Görseller
│
├── 📁 scripts/               # Yardımcı scriptler
│   ├── seed_course_system.py
│   ├── import_words.py
│   └── ...
│
└── 📁 database_icin_kelime/  # Kelime veritabanı
    └── data/                 # Kategori bazlı kelimeler
```

---

## 🖥 Kullanım

### İlk Adımlar

1. **Kayıt Ol**: Ana sayfadan yeni hesap oluştur
2. **Seviye Testi**: Başlangıç seviyeni belirle (opsiyonel)
3. **Kurs Seç**: CEFR seviyene uygun kursu seç
4. **Öğrenmeye Başla**: Üniteleri ve dersleri tamamla

### Öğrenme Modları

| Mod | Açıklama |
|-----|----------|
| 📖 **Ders** | Yapılandırılmış ünite dersleri |
| 🔤 **Kelime Pratiği** | Kelime kartları ile çalışma |
| ✍️ **Cümle Pratiği** | Gramer ve cümle kurma |
| 🎤 **Telaffuz** | Sesli konuşma pratiği |
| 📝 **Quiz** | Bilgini test et |

---

## 🔌 API Endpoints

### Kullanıcı
| Metod | Endpoint | Açıklama |
|-------|----------|----------|
| POST | `/login` | Giriş/Kayıt |
| GET | `/dashboard` | Ana panel |
| GET | `/profile` | Profil sayfası |

### Öğrenme
| Metod | Endpoint | Açıklama |
|-------|----------|----------|
| GET | `/learn` | Öğrenme sayfası |
| GET | `/courses` | Kurs listesi |
| POST | `/api/learn/record-mistake` | Hata kaydet |

### İstatistikler
| Metod | Endpoint | Açıklama |
|-------|----------|----------|
| GET | `/stats` | İstatistikler |
| GET | `/api/dashboard-stats` | Dashboard verileri |

---

## 🎨 Ekran Görüntüleri

```
┌─────────────────────────────────────────┐
│  🦉 LoroLeng                         │
├─────────────────────────────────────────┤
│                                         │
│   🔥 5 Gün    ⭐ 1250 XP    ❤️ 5        │
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │   A1    │  │   A2    │  │   B1    │ │
│  │ Başlangıç│ │ Temel   │  │  Orta   │ │
│  └─────────┘  └─────────┘  └─────────┘ │
│                                         │
│  📚 Günlük Hedef: 50 XP                │
│  ████████████░░░░░░  60%               │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz! 

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'i push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

---

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

## 🙏 Teşekkürler

- [Duolingo](https://duolingo.com) - İlham kaynağı
- [Google Gemini](https://ai.google.dev/) - AI desteği
- [Deep Translator](https://github.com/nidhaloff/deep-translator) - Çeviri API

---

<div align="center">

**Made with ❤️ for Turkish learners**

⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!

</div>
