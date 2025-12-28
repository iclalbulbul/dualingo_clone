# 📚 Kurs Sistemi - Tam Rehber

## Genel Bakış

Uygulamaya **20 ünite ile oluşturulmuş standart kurs sistemi** ve **kullanıcı tarafından seçilen konularla özel kurs oluşturma** özellikleri eklenmiştir.

---

## 1️⃣ Standart Kurs (20 Ünite)

Hazır olarak 20 ünitelik kapsamlı bir İngilizce kursu sunulmaktadır:

### A1 Seviyesi (10 ünite)
1. **Günlük Tebrik** - Temel selamlaşma ve nezaket ifadeleri
2. **Kişisel Bilgiler** - Ad, yaş, meslek sorma ve cevaplama
3. **Günün Saatleri** - Saat söyleme ve zaman ifadeleri
4. **Haftanın Günleri** - Gün ve tarih ifadeleri
5. **Mevsimler** - Mevsim adları ve hava durumu
6. **Sayılar 1-20** - Temel sayı ifadeleri
7. **Yiyecek ve İçecek** - Gıda ve içecek adları, siparişler
8. **Ev ve Aile** - Ev eşyaları, aile üyeleri
9. **Giyim ve Aksesuar** - Kıyafet ve aksesuar adları
10. **Vücut Bölümleri** - Vücut ve sağlık ile ilgili kelimeler

### A2-B1 Seviyesi (10 ünite)
11. **Şehir ve Mekanlar** - Harita, yol tarifi, mekan adları
12. **Geçmiş Zaman** - Geçmiş zamanda konuşma
13. **Gelecek Zaman** - Gelecek planları ve tahminler
14. **İş ve Meslekler** - Meslek adları ve iş ortamı
15. **Hobi ve Sportlar** - Boş zaman aktiviteleri
16. **İletişim** - Telefon, email, sosyal medya
17. **Seyahat** - Otel, ulaşım, turizm
18. **Sağlık ve Tıp** - Tıbbi durumlar ve tedavi
19. **Eğitim** - Okullar, öğrenme, sınavlar
20. **Sanat ve Kültür** - Müzik, resim, edebiyat, sinema

---

## 2️⃣ Özel Kurs Oluşturma

Kullanıcılar kendi ilgi alanlarına göre özel kurs oluşturabilirler.

### Örnek Özel Kurslar:
- "İş İngilizçesi" (Business, Meeting, Presentation, Email)
- "Turizm" (Hotel, Travel, Transportation, Food)
- "Teknoloji" (Computer, Software, Internet, Phone)
- "Tıp" (Health, Medicine, Hospital, Doctor)

---

## 📂 Dosya Yapısı

### Yeni Dosyalar

```
features/
├── courses.py              # ✨ Yeni - Kurs yönetim sistemi
│
├── __init__.py            # Güncellendi - CourseManager eklendi
```

### Güncellenmiş Dosyalar

```
app.py                     # Güncellendi - Kurs rotaları eklendi

templates/
├── courses.html           # ✨ Yeni - Kurslar sayfası
├── course_detail.html     # ✨ Yeni - Kurs detay sayfası
├── unit_study.html        # ✨ Yeni - Ünite çalışma sayfası
├── create_course.html     # ✨ Yeni - Kurs oluştur sayfası
├── base.html              # Güncellendi - Kurs linki eklendi
```

---

## 🔗 API Uçları (Rotalar)

### Kurs Yönetimi

| Rota | Metod | Açıklama |
|------|-------|----------|
| `/courses` | GET | Tüm kursları listele (aktif ve tamamlanan) |
| `/course/create` | GET/POST | Yeni kurs oluştur |
| `/course/<id>` | GET | Kurs detaylarını ve ünitelerini gör |
| `/course/<id>/delete` | POST | Kursu sil |

### Ünite Yönetimi

| Rota | Metod | Açıklama |
|------|-------|----------|
| `/unit/<id>` | GET | Üniteyi çalış |
| `/api/unit/<id>/progress` | POST | Ünite ilerleme yüzdesini güncelle |
| `/api/course/<id>/stats` | GET | Kurs istatistiklerini al |

---

## 💻 Python API Kullanımı

### CourseManager Sınıfı

#### 1. Standart Kurs Oluştur

```python
from features.courses import CourseManager

cm = CourseManager()

# 20 ünite ile standart kurs oluştur
course_id = cm.create_course(
    user_id=1,
    course_name="İngilizce Başlangıç",
    course_type="standard",
    description="20 ünite ile kapsamlı İngilizce öğrenme"
)
```

#### 2. Özel Kurs Oluştur

```python
# Kullanıcının seçtiği konulardan kurs oluştur
custom_course = cm.create_custom_course_from_topics(
    user_id=1,
    topics_list=["Teknoloji", "Bilim", "Spor"],
    course_name="Benim İlgi Alanlarım"
)
```

#### 3. Kursları Al

```python
# Aktif kursları al
active_courses = cm.get_user_courses(user_id=1, status="active")

# Tamamlanan kursları al
completed_courses = cm.get_user_courses(user_id=1, status="completed")

# Tüm kursları al
all_courses = cm.get_user_courses(user_id=1, status="all")

print(active_courses)
# Çıkış:
# [
#     {
#         'course_id': 1,
#         'course_name': 'İngilizce Başlangıç',
#         'course_type': 'standard',
#         'progress_percent': 25.0,
#         'total_units': 20,
#         'completed_units': 5,
#         'status': 'active',
#         'created_at': '2025-12-25 10:30:00'
#     }
# ]
```

#### 4. Kursun Ünitelerini Al

```python
# Kursun tüm ünitelerini al
units = cm.get_course_units(course_id=1)

print(units[0])
# {
#     'unit_id': 1,
#     'unit_num': 1,
#     'title': 'Günlük Tebrik',
#     'description': 'Temel selamlaşma ve nezaket ifadeleri',
#     'level': 'A1',
#     'words_count': 0,
#     'completed': False,
#     'progress': 0.0,
#     'status': 'not_started'
# }
```

#### 5. Üniteyi Başlat

```python
# Ünite çalışmasına başla
cm.start_unit(unit_id=1)
# Çıkış: ✓ Ünite başlatıldı [ID: 1]
```

#### 6. Ünite İlerleme Güncelle

```python
# Ünite ilerleme yüzdesini güncelle
cm.update_unit_progress(unit_id=1, progress_percent=50)
# Çıkış: ✓ Ünite ilerleme güncellendi [ID: 1] - %50
```

#### 7. Kurs İstatistikleri

```python
# Kurs istatistiklerini al
stats = cm.get_course_stats(course_id=1)

print(stats)
# {
#     'course_id': 1,
#     'course_name': 'İngilizce Başlangıç',
#     'status': 'active',
#     'total_units': 20,
#     'completed_units': 5,
#     'started_units': 8,
#     'not_started_units': 12,
#     'average_progress': 32.5,
#     'overall_progress': 25.0,
#     'estimated_completion': '2026-01-15'
# }
```

#### 8. Özel Ünite Ekle

```python
# Özel kursa ünite ekle
unit_id = cm.add_custom_unit(
    course_id=2,
    unit_num=1,
    title="Teknoloji Temel Kavramlar",
    description="Bilgisayar ve yazılım ile ilgili temel kavramlar",
    level="A1"
)
```

#### 9. Üniteye Kaynak Ekle

```python
# Kelime kaynağı ekle
cm.add_unit_resources(
    unit_id=1,
    resource_type="vocabulary",
    content={
        "english": "Hello",
        "turkish": "Merhaba",
        "pronunciation": "/həˈloʊ/",
        "example": "Hello, how are you?"
    }
)

# Gramer kaynağı ekle
cm.add_unit_resources(
    unit_id=1,
    resource_type="grammar",
    content={
        "title": "Simple Present Tense",
        "explanation": "Habitual actions ve facts için kullanılır...",
        "examples": [
            "I play football every day.",
            "She works in an office."
        ]
    }
)
```

#### 10. Ünite Kaynaklarını Al

```python
# Tüm kaynakları al
all_resources = cm.get_unit_resources(unit_id=1)

# Sadece kelime kaynaklarını al
vocab_resources = cm.get_unit_resources(unit_id=1, resource_type="vocabulary")

# Sadece gramer kaynaklarını al
grammar_resources = cm.get_unit_resources(unit_id=1, resource_type="grammar")
```

#### 11. Mevcut Konuları Al

```python
# Veritabanında kayıtlı tüm konuları al
available_topics = cm.get_available_topics()

print(available_topics)
# ['Agriculture', 'Anthropology', 'Archaeology', ...]
```

---

## 🗄️ Veritabanı Şeması

### `courses` Tablosu

```sql
CREATE TABLE courses (
    course_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    course_name TEXT NOT NULL,
    course_type TEXT,              -- 'standard' veya 'custom'
    description TEXT,
    progress_percent REAL DEFAULT 0,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT DEFAULT 'active',  -- 'active' veya 'completed'
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

### `units` Tablosu

```sql
CREATE TABLE units (
    unit_id INTEGER PRIMARY KEY,
    course_id INTEGER NOT NULL,
    unit_num INTEGER,              -- Ünite numarası
    title TEXT NOT NULL,
    description TEXT,
    level TEXT,                    -- 'A1', 'A2', 'B1', vb.
    words_count INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT 0,
    progress REAL DEFAULT 0,       -- 0-100
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
)
```

### `unit_resources` Tablosu

```sql
CREATE TABLE unit_resources (
    resource_id INTEGER PRIMARY KEY,
    unit_id INTEGER NOT NULL,
    resource_type TEXT,           -- 'vocabulary', 'grammar', 'sentence', 'audio'
    content TEXT,                 -- JSON format
    created_at TIMESTAMP,
    FOREIGN KEY (unit_id) REFERENCES units(unit_id)
)
```

---

## 🎯 İşlevler

### Ünite İlerleme Takibi

- Her ünite için % bazında ilerleme takibi yapılır
- Ünite başlatıldığında `started_at` zamanı kaydedilir
- İlerleme %100 olduğunda ünite otomatik tamamlanır
- Kurs ilerleme, ünitelere göre otomatik hesaplanır

### Otomatik Bitiş Tarihi Tahmini

```python
# Son 7 gündeki ilerleme hızına göre tahmini bitiş tarihini hesapla
estimated_date = cm._estimate_completion(course_id=1, avg_progress=32.5)
```

### İstatistikler

- ✅ Tamamlanan ünite sayısı
- 🔄 Başlanan ünite sayısı
- 🔒 Başlanmamış ünite sayısı
- 📊 Ortalama ilerleme yüzdesi
- 📅 Tahmini bitiş tarihi

---

## 🌐 Web Arayüzü

### Kurslar Sayfası (`/courses`)
- Aktif kursları listele
- Tamamlanan kursları göster
- Her kursa ilerleme bar
- Yeni kurs oluştur butonu
- Kurs silme seçeneği

### Kurs Detay Sayfası (`/course/<id>`)
- Genel ilerleme gösterimi
- 20 üniteyi listele
- Her ünite için durum (tamamlandı/devam ediyor/başlanmadı)
- Ünite başlatma linki
- İstatistikler

### Ünite Çalışma Sayfası (`/unit/<id>`)
- Ünite başlığı ve açıklaması
- Kelime listesi (sesli dinleme)
- Gramer kuralları
- Örnek cümleler
- Ilerleme bar
- Pratik seçenekleri (kelime, cümle, telaffuz)
- Üniteyi tamamla butonu

### Kurs Oluştur Sayfası (`/course/create`)
- Standart kurs seçeneği (20 ünite hazır)
- Özel kurs seçeneği (konuları seç)
- Mevcut konuları listele
- Özel konuları yazma seçeneği

---

## 📊 Entegrasyon

### GoalManager ile Entegrasyon
- "Ünite Tamamlama" hedefi türü eklenebilir
- Kurs tamamlama başarı bildirim gönderilir

### NotificationManager ile Entegrasyon
- Kurs oluşturulduğunda bildirim
- Ünite tamamlandığında bildirim
- Kurs tamamlandığında başarı bildirim

### UserStats ile Entegrasyon
- Kurs ünitelerinde harcanan zaman takibi
- Kurs başına doğru cevap oranı
- Kurs ilerleme grafiği

---

## 🚀 Başlangıç

### 1. Standart Kurs Oluştur
```python
from features.courses import CourseManager
cm = CourseManager()
course_id = cm.create_course(1, "İngilizce Başlangıç", "standard")
```

### 2. Web Arayüzünden Kurs Oluştur
- `/courses` sayfasına git
- "Yeni Kurs" butonuna tıkla
- Standart veya Özel seç
- Kurs bilgilerini doldur
- Oluştur butonuna tıkla

### 3. Üniteyi Çalış
- Kurs detay sayfasındaki ünitelerinden birine tıkla
- Ünite materyallerini gözden geçir
- Pratik yap (kelime, cümle, telaffuz)
- İlerleme otomatik güncellenir

---

## 💡 İpuçları

1. **Kurs Silmeden Önce:** Dikkat! Kurs silinirse tüm üniteler ve ilerleme silinir.

2. **İlerleme Hesaplanması:** 
   - Ünite ilerleme: Yapılan pratiklere göre otomatik
   - Kurs ilerleme: Tamamlanan ünite sayısı / toplam ünite sayısı

3. **Özel Kurs:** En az 1 konu seçmek gereklidir.

4. **Bitiş Tarihi:** Tahmin, son 7 gündeki ortalama ilerleme hızına dayanır.

---

## 🔧 Sorun Giderme

### Kurs bulunamadı hatası
- Kursu oluşturdunuz mu kontrol edin
- Doğru `course_id` kullanıp kullanmadığınızı kontrol edin

### İlerleme güncellenmiyor
- JavaScript konsolunda hata var mı kontrol edin
- API uç noktasının doğru olduğundan emin olun

### Üniteye materyel eklenmedi
- JSON formatında içeriği gönderin
- `add_unit_resources` metodu kullanın

---

## 📞 Destek

Sorularınız veya sorunlarınız için iletişime geçebilirsiniz.

---

**Son Güncelleme:** 25 Aralık 2025
**Versiyon:** 1.0
