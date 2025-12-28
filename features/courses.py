"""
courses.py

20 ünite kurs sistemi ve özel konu seçme özelliği.
Kullanıcılar hazır kursları takip edebilir veya kendi konularını seçebilir.
"""

from db_utils import get_db_connection
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json


class CourseManager:
    """Kurs ve ünite yönetimi."""
    
    def __init__(self):
        # 20 standart ünite
        self.default_units = [
            {"unit_num": 1, "title": "Günlük Tebrik", "description": "Temel selamlaşma ve nezaket ifadeleri", "level": "A1"},
            {"unit_num": 2, "title": "Kişisel Bilgiler", "description": "Ad, yaş, meslek sorma ve cevaplama", "level": "A1"},
            {"unit_num": 3, "title": "Günün Saatleri", "description": "Saat söyleme ve zaman ifadeleri", "level": "A1"},
            {"unit_num": 4, "title": "Haftanın Günleri", "description": "Gün ve tarih ifadeleri", "level": "A1"},
            {"unit_num": 5, "title": "Mevsimler", "description": "Mevsim adları ve hava durumu", "level": "A1"},
            {"unit_num": 6, "title": "Sayılar 1-20", "description": "Temel sayı ifadeleri", "level": "A1"},
            {"unit_num": 7, "title": "Yiyecek ve İçecek", "description": "Gıda ve içecek adları, siparişler", "level": "A1"},
            {"unit_num": 8, "title": "Ev ve Aile", "description": "Ev eşyaları, aile üyeleri", "level": "A1"},
            {"unit_num": 9, "title": "Giyim ve Aksesuar", "description": "Kıyafet ve aksesuar adları", "level": "A1"},
            {"unit_num": 10, "title": "Vücut Bölümleri", "description": "Vücut ve sağlık ile ilgili kelimeler", "level": "A1"},
            {"unit_num": 11, "title": "Şehir ve Mekanlar", "description": "Harita, yol tarifi, mekan adları", "level": "A2"},
            {"unit_num": 12, "title": "Geçmiş Zaman", "description": "Geçmiş zamanda konuşma", "level": "A2"},
            {"unit_num": 13, "title": "Geleceğin Zaman", "description": "Gelecek planları ve tahminler", "level": "A2"},
            {"unit_num": 14, "title": "İş ve Meslekler", "description": "Meslek adları ve iş ortamı", "level": "A2"},
            {"unit_num": 15, "title": "Hobi ve Sportlar", "description": "Boş zaman aktiviteleri", "level": "A2"},
            {"unit_num": 16, "title": "İletişim", "description": "Telefon, email, sosyal medya", "level": "A2"},
            {"unit_num": 17, "title": "Seyahat", "description": "Otel, ulaşım, turizm", "level": "B1"},
            {"unit_num": 18, "title": "Sağlık ve Tıp", "description": "Tıbbi durumlar ve tedavi", "level": "B1"},
            {"unit_num": 19, "title": "Eğitim", "description": "Okullar, öğrenme, sınavlar", "level": "B1"},
            {"unit_num": 20, "title": "Sanat ve Kültür", "description": "Müzik, resim, edebiyat, sinema", "level": "B1"},
        ]
    
    # ==================== KURS OLUŞTURMA ====================
    
    def create_course(
        self,
        user_id: int,
        course_name: str,
        course_type: str = "standard",  # "standard" veya "custom"
        description: Optional[str] = None
    ) -> int:
        """
        Yeni kurs oluştur (standart 20 ünite veya özel)
        
        Args:
            user_id: Kullanıcı ID
            course_name: Kurs adı
            course_type: "standard" (20 ünite) veya "custom" (kullanıcı seçimi)
            description: Açıklama
        
        Returns:
            Oluşturulan kursun ID'si
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # courses tablosu oluştur
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    course_name TEXT NOT NULL,
                    course_type TEXT DEFAULT 'standard',
                    description TEXT,
                    progress_percent REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # units tablosu oluştur
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS units (
                    unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER NOT NULL,
                    unit_num INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    level TEXT,
                    words_count INTEGER DEFAULT 0,
                    completed BOOLEAN DEFAULT 0,
                    progress REAL DEFAULT 0,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (course_id) REFERENCES courses(course_id)
                )
            """)
            
            cursor.execute("""
                INSERT INTO courses (user_id, course_name, course_type, description, status)
                VALUES (?, ?, ?, ?, 'active')
            """, (user_id, course_name, course_type, description))
            
            conn.commit()
            course_id = cursor.lastrowid
            
            # Standart kurs ise üniteleri ekle
            if course_type == "standard":
                for unit in self.default_units:
                    cursor.execute("""
                        INSERT INTO units (course_id, unit_num, title, description, level)
                        VALUES (?, ?, ?, ?, ?)
                    """, (course_id, unit["unit_num"], unit["title"], 
                          unit["description"], unit["level"]))
                
                conn.commit()
            
            print(f"✓ Kurs oluşturuldu [ID: {course_id}] - Tip: {course_type}")
            return course_id
        
        except Exception as e:
            print(f"❌ Kurs oluşturma hatası: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    # ==================== ÜNİTE EKLEME (CUSTOM KONULAR) ====================
    
    def add_custom_unit(
        self,
        course_id: int,
        unit_num: int,
        title: str,
        description: str,
        level: str = "A1"
    ) -> int:
        """
        Özel konusu olan kursa ünite ekle
        
        Args:
            course_id: Kurs ID
            unit_num: Ünite numarası
            title: Konu başlığı
            description: Açıklama
            level: CEFR seviyesi (A1, A2, B1, B2 vb.)
        
        Returns:
            Oluşturulan ünitenin ID'si
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO units (course_id, unit_num, title, description, level)
                VALUES (?, ?, ?, ?, ?)
            """, (course_id, unit_num, title, description, level))
            
            conn.commit()
            unit_id = cursor.lastrowid
            print(f"✓ Ünite eklendi [ID: {unit_id}] - '{title}'")
            return unit_id
        
        except Exception as e:
            print(f"❌ Ünite ekleme hatası: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    # ==================== ÜNİTE İLERLEMESİ ====================
    
    def get_user_courses(self, user_id: int, status: str = "active") -> List[Dict[str, Any]]:
        """
        Kullanıcının kurslarını al
        
        Args:
            user_id: Kullanıcı ID
            status: "active", "completed" veya "all"
        
        Returns:
            Kurslar listesi
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        courses = []
        
        try:
            if status == "all":
                query = "SELECT * FROM courses WHERE user_id = ? ORDER BY created_at DESC"
                cursor.execute(query, (user_id,))
            else:
                query = "SELECT * FROM courses WHERE user_id = ? AND status = ? ORDER BY created_at DESC"
                cursor.execute(query, (user_id, status))
            
            for row in cursor.fetchall():
                course_id = row[0]
                
                # Üniteleri al
                cursor.execute("""
                    SELECT COUNT(*) FROM units WHERE course_id = ?
                """, (course_id,))
                total_units = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM units WHERE course_id = ? AND completed = 1
                """, (course_id,))
                completed_units = cursor.fetchone()[0]
                
                progress = (completed_units / total_units * 100) if total_units > 0 else 0
                
                courses.append({
                    'course_id': row[0],
                    'course_name': row[2],
                    'course_type': row[3],
                    'description': row[4],
                    'progress_percent': round(progress, 2),
                    'total_units': total_units,
                    'completed_units': completed_units,
                    'status': row[7],
                    'created_at': row[6],
                    'completed_at': row[7]
                })
            
            return courses
        
        except Exception as e:
            print(f"❌ Kurs alma hatası: {e}")
            return []
        finally:
            conn.close()
    
    def get_course_units(self, course_id: int) -> List[Dict[str, Any]]:
        """
        Kursun tüm ünitelerini al
        
        Args:
            course_id: Kurs ID
        
        Returns:
            Üniteler listesi
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        units = []
        
        try:
            cursor.execute("""
                SELECT unit_id, unit_num, title, description, level, words_count, 
                       completed, progress, started_at, completed_at
                FROM units
                WHERE course_id = ?
                ORDER BY unit_num ASC
            """, (course_id,))
            
            for row in cursor.fetchall():
                units.append({
                    'unit_id': row[0],
                    'unit_num': row[1],
                    'title': row[2],
                    'description': row[3],
                    'level': row[4],
                    'words_count': row[5],
                    'completed': bool(row[6]),
                    'progress': round(row[7], 2),
                    'started_at': row[8],
                    'completed_at': row[9],
                    'status': 'completed' if row[6] else 'in_progress' if row[8] else 'not_started'
                })
            
            return units
        
        except Exception as e:
            print(f"❌ Ünite alma hatası: {e}")
            return []
        finally:
            conn.close()
    
    def start_unit(self, unit_id: int) -> bool:
        """
        Ünitye çalışmaya başla
        
        Args:
            unit_id: Ünite ID
        
        Returns:
            Başarı durumu
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE units
                SET started_at = CURRENT_TIMESTAMP
                WHERE unit_id = ? AND started_at IS NULL
            """, (unit_id,))
            
            conn.commit()
            print(f"✓ Ünite başlatıldı [ID: {unit_id}]")
            return True
        
        except Exception as e:
            print(f"❌ Ünite başlatma hatası: {e}")
            return False
        finally:
            conn.close()
    
    def update_unit_progress(self, unit_id: int, progress_percent: float) -> bool:
        """
        Ünite ilerleme yüzdesini güncelle
        
        Args:
            unit_id: Ünite ID
            progress_percent: İlerleme yüzdesi (0-100)
        
        Returns:
            Başarı durumu
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Başlatılmamışsa başlat
            cursor.execute("""
                SELECT started_at FROM units WHERE unit_id = ?
            """, (unit_id,))
            row = cursor.fetchone()
            
            if row and row[0] is None:
                cursor.execute("""
                    UPDATE units
                    SET started_at = CURRENT_TIMESTAMP
                    WHERE unit_id = ?
                """, (unit_id,))
            
            # İlerleme güncelle
            is_completed = progress_percent >= 100
            cursor.execute("""
                UPDATE units
                SET progress = ?, completed = ?, completed_at = ?
                WHERE unit_id = ?
            """, (
                progress_percent,
                1 if is_completed else 0,
                datetime.now() if is_completed else None,
                unit_id
            ))
            
            conn.commit()
            print(f"✓ Ünite ilerleme güncellendi [ID: {unit_id}] - %{progress_percent}")
            
            # Kurs ilerleme güncelle
            cursor.execute("""
                SELECT course_id FROM units WHERE unit_id = ?
            """, (unit_id,))
            course_id = cursor.fetchone()[0]
            self._update_course_progress(course_id)
            
            return True
        
        except Exception as e:
            print(f"❌ Ünite ilerleme güncelleme hatası: {e}")
            return False
        finally:
            conn.close()
    
    def _update_course_progress(self, course_id: int):
        """
        Kurs ilerleme yüzdesini hesapla ve güncelle
        
        Args:
            course_id: Kurs ID
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM units WHERE course_id = ?
            """, (course_id,))
            total = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM units WHERE course_id = ? AND completed = 1
            """, (course_id,))
            completed = cursor.fetchone()[0]
            
            progress = (completed / total * 100) if total > 0 else 0
            
            # Kursun durumunu güncelle
            is_course_completed = completed == total and total > 0
            
            cursor.execute("""
                UPDATE courses
                SET progress_percent = ?, status = ?, completed_at = ?
                WHERE course_id = ?
            """, (
                progress,
                'completed' if is_course_completed else 'active',
                datetime.now() if is_course_completed else None,
                course_id
            ))
            
            conn.commit()
        
        except Exception as e:
            print(f"❌ Kurs ilerleme güncelleme hatası: {e}")
        finally:
            conn.close()
    
    # ==================== İSTATİSTİKLER ====================
    
    def get_course_stats(self, course_id: int) -> Dict[str, Any]:
        """
        Kurs istatistiklerini al
        
        Args:
            course_id: Kurs ID
        
        Returns:
            İstatistikler sözlüğü
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Genel bilgiler
            cursor.execute("""
                SELECT course_id, course_name, status, created_at FROM courses WHERE course_id = ?
            """, (course_id,))
            course_row = cursor.fetchone()
            
            if not course_row:
                return {}
            
            # Ünite istatistikleri
            cursor.execute("""
                SELECT COUNT(*), 
                       SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END),
                       AVG(progress),
                       SUM(CASE WHEN started_at IS NOT NULL THEN 1 ELSE 0 END)
                FROM units WHERE course_id = ?
            """, (course_id,))
            
            stats = cursor.fetchone()
            total_units = stats[0] or 0
            completed_units = stats[1] or 0
            avg_progress = stats[2] or 0
            started_units = stats[3] or 0
            
            return {
                'course_id': course_id,
                'course_name': course_row[1],
                'status': course_row[2],
                'created_at': course_row[3],
                'total_units': total_units,
                'completed_units': completed_units,
                'started_units': started_units,
                'not_started_units': total_units - started_units,
                'average_progress': round(avg_progress, 2),
                'overall_progress': round(completed_units / total_units * 100, 2) if total_units > 0 else 0,
                'estimated_completion': self._estimate_completion(course_id, avg_progress)
            }
        
        except Exception as e:
            print(f"❌ İstatistik alma hatası: {e}")
            return {}
        finally:
            conn.close()
    
    def _estimate_completion(self, course_id: int, avg_progress: float) -> Optional[str]:
        """
        Kursun tahmini bitiş tarihini hesapla (heuristic)
        
        Args:
            course_id: Kurs ID
            avg_progress: Ortalama ilerleme
        
        Returns:
            Tahmini bitiş tarihi
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Son 7 gündeki ilerleme hızı
            cursor.execute("""
                SELECT MAX(progress) FROM units 
                WHERE course_id = ? 
                AND started_at >= datetime('now', '-7 days')
            """, (course_id,))
            
            recent_progress = cursor.fetchone()[0] or avg_progress
            conn.close()
            
            if recent_progress == 0:
                return None
            
            # Günde % (basit tahmin)
            daily_rate = recent_progress / 7
            if daily_rate == 0:
                return None
            
            remaining_days = (100 - avg_progress) / daily_rate
            estimated_date = datetime.now() + timedelta(days=remaining_days)
            
            return estimated_date.strftime("%Y-%m-%d")
        
        except:
            return None
    
    # ==================== ÖZEL KONU SEÇİMİ ====================
    
    def create_custom_course_from_topics(
        self,
        user_id: int,
        topics_list: List[str],
        course_name: Optional[str] = None
    ) -> int:
        """
        Kullanıcı tarafından seçilen konulardan kurs oluştur
        
        Args:
            user_id: Kullanıcı ID
            topics_list: Konu adları listesi
            course_name: Kurs adı (otomatik oluşturulabilir)
        
        Returns:
            Oluşturulan kursun ID'si
        """
        if not course_name:
            course_name = f"Özel Kurs - {', '.join(topics_list[:3])}"
        
        course_id = self.create_course(
            user_id=user_id,
            course_name=course_name,
            course_type="custom",
            description=f"Seçilen konular: {', '.join(topics_list)}"
        )
        
        if course_id == -1:
            return -1
        
        # Her konu için ünite ekle
        for idx, topic in enumerate(topics_list, 1):
            self.add_custom_unit(
                course_id=course_id,
                unit_num=idx,
                title=topic,
                description=f"{topic} konusu hakkında kelime ve ifadeler",
                level="A1"  # Başlangıç seviyesi
            )
        
        print(f"✓ Özel kurs oluşturuldu [{course_id}] - {len(topics_list)} konu")
        return course_id
    
    def get_available_topics(self) -> List[str]:
        """
        Kullanıcıların seçebileceği konuları listele
        
        Returns:
            Konu listesi
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT topic_name FROM topics ORDER BY topic_name
            """)
            
            topics = [row[0] for row in cursor.fetchall()]
            return topics
        
        except Exception as e:
            print(f"❌ Konu alma hatası: {e}")
            return []
        finally:
            conn.close()
    
    # ==================== ÜNİTE ŞARKI VE KAYNAKLAR ====================
    
    def add_unit_resources(
        self,
        unit_id: int,
        resource_type: str,  # "vocabulary", "grammar", "sentence", "audio"
        content: Dict[str, Any]
    ) -> bool:
        """
        Ünitee kaynak ekle (kelime, gramer, örnek cümleler vb.)
        
        Args:
            unit_id: Ünite ID
            resource_type: Kaynak tipi
            content: Kaynak içeriği
        
        Returns:
            Başarı durumu
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unit_resources (
                    resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unit_id INTEGER NOT NULL,
                    resource_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (unit_id) REFERENCES units(unit_id)
                )
            """)
            
            content_json = json.dumps(content, ensure_ascii=False)
            cursor.execute("""
                INSERT INTO unit_resources (unit_id, resource_type, content)
                VALUES (?, ?, ?)
            """, (unit_id, resource_type, content_json))
            
            conn.commit()
            print(f"✓ Kaynak eklendi [Ünite: {unit_id}] - Tip: {resource_type}")
            return True
        
        except Exception as e:
            print(f"❌ Kaynak ekleme hatası: {e}")
            return False
        finally:
            conn.close()
    
    def get_unit_resources(self, unit_id: int, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Ünittenin kaynağını al
        
        Args:
            unit_id: Ünite ID
            resource_type: Belirli bir kaynak tipi filtresi (isteğe bağlı)
        
        Returns:
            Kaynaklar listesi
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        resources = []
        
        try:
            if resource_type:
                cursor.execute("""
                    SELECT resource_id, resource_type, content FROM unit_resources
                    WHERE unit_id = ? AND resource_type = ?
                """, (unit_id, resource_type))
            else:
                cursor.execute("""
                    SELECT resource_id, resource_type, content FROM unit_resources
                    WHERE unit_id = ?
                """, (unit_id,))
            
            for row in cursor.fetchall():
                resources.append({
                    'resource_id': row[0],
                    'resource_type': row[1],
                    'content': json.loads(row[2])
                })
            
            return resources
        
        except Exception as e:
            print(f"❌ Kaynak alma hatası: {e}")
            return []
        finally:
            conn.close()


# ==================== KULLANIM ÖRNEKLERİ ====================

if __name__ == "__main__":
    cm = CourseManager()
    
    # Standart 20 ünite kursu oluştur
    # course_id = cm.create_course(user_id=1, course_name="İngilizce Başlangıç", course_type="standard")
    
    # Kursları al
    # courses = cm.get_user_courses(user_id=1)
    # print(json.dumps(courses, indent=2, default=str))
    
    # Özel konulardan kurs oluştur
    # custom_course = cm.create_custom_course_from_topics(
    #     user_id=1,
    #     topics_list=["Teknoloji", "Bilim", "Spor"],
    #     course_name="Benim İlgi Alanlarım"
    # )
    
    # Üniteleri al
    # units = cm.get_course_units(course_id)
    # print(json.dumps(units, indent=2, default=str))
    
    # Ünite ilerleme güncelle
    # cm.update_unit_progress(unit_id=1, progress_percent=50)
    
    # Kurs istatistikleri
    # stats = cm.get_course_stats(course_id=1)
    # print(json.dumps(stats, indent=2, default=str))
    
    print("✓ CourseManager modülü hazır")
