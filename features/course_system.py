"""
course_system.py

Duolingo tarzı kur-kur ilerlenebilir kurs sistemi.
CEFR seviyelerine göre organize edilmiş üniteler ve dersler.

Bu modül mevcut courses.py'yi BOZMAZ, ayrı bir sistem olarak çalışır.
"""

from db_utils import get_db_connection
from translation_utils import get_translation
from datetime import datetime
from typing import Dict, List, Any, Optional
import json


class CourseSystem:
    """CEFR tabanlı kurs ilerleme sistemi."""
    
    def __init__(self):
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Gerekli tabloları oluştur (varsa dokunma)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # CEFR Seviyeleri
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cefr_levels (
                    level_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    order_num INTEGER NOT NULL,
                    icon TEXT DEFAULT '📚',
                    color TEXT DEFAULT '#58cc02',
                    units_count INTEGER DEFAULT 5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Kurs Üniteleri
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS course_units (
                    unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level_code TEXT NOT NULL,
                    order_num INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    icon TEXT DEFAULT '📖',
                    words_target INTEGER DEFAULT 15,
                    xp_reward INTEGER DEFAULT 50,
                    is_bonus BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(level_code, order_num)
                )
            """)
            
            # Ders Tipleri (her ünitede 5 ders)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS course_lessons (
                    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unit_id INTEGER NOT NULL,
                    order_num INTEGER NOT NULL,
                    lesson_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    xp_reward INTEGER DEFAULT 10,
                    questions_count INTEGER DEFAULT 10,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (unit_id) REFERENCES course_units(unit_id),
                    UNIQUE(unit_id, order_num)
                )
            """)
            
            # Ders İçerikleri (sorular)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lesson_questions (
                    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lesson_id INTEGER NOT NULL,
                    question_type TEXT NOT NULL,
                    question_text TEXT NOT NULL,
                    correct_answer TEXT NOT NULL,
                    wrong_options TEXT,
                    hint TEXT,
                    audio_url TEXT,
                    image_url TEXT,
                    word_id INTEGER,
                    order_num INTEGER DEFAULT 0,
                    FOREIGN KEY (lesson_id) REFERENCES course_lessons(lesson_id),
                    FOREIGN KEY (word_id) REFERENCES words(word_id)
                )
            """)
            
            # Kullanıcı Kurs İlerlemesi
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_course_progress (
                    progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    level_code TEXT NOT NULL,
                    unit_id INTEGER NOT NULL,
                    lesson_id INTEGER,
                    status TEXT DEFAULT 'locked',
                    crowns INTEGER DEFAULT 0,
                    best_score INTEGER DEFAULT 0,
                    attempts INTEGER DEFAULT 0,
                    completed_at TIMESTAMP,
                    last_activity TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (unit_id) REFERENCES course_units(unit_id),
                    UNIQUE(user_id, unit_id, lesson_id)
                )
            """)
            
            # Kullanıcı Genel Kurs Durumu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_course_state (
                    state_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    current_level TEXT DEFAULT 'A1',
                    current_unit_id INTEGER,
                    total_xp INTEGER DEFAULT 0,
                    total_crowns INTEGER DEFAULT 0,
                    hearts INTEGER DEFAULT 5,
                    hearts_updated_at TIMESTAMP,
                    streak_days INTEGER DEFAULT 0,
                    last_lesson_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            conn.commit()
            print("✓ Kurs sistemi tabloları hazır")
            
        except Exception as e:
            print(f"❌ Tablo oluşturma hatası: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    # ==================== SEVİYE YÖNETİMİ ====================
    
    def seed_levels(self):
        """CEFR seviyelerini ekle (zaten varsa atla)."""
        levels = [
            {"code": "A1", "name": "Başlangıç", "description": "Temel kelimeler ve basit cümleler", "order_num": 1, "icon": "🌱", "color": "#58cc02"},
            {"code": "A2", "name": "Temel", "description": "Günlük konuşmalar ve temel gramer", "order_num": 2, "icon": "🌿", "color": "#1cb0f6"},
            {"code": "B1", "name": "Orta-Alt", "description": "Karmaşık cümleler ve daha fazla kelime", "order_num": 3, "icon": "🌳", "color": "#ff9600"},
            {"code": "B2", "name": "Orta-Üst", "description": "Akıcı konuşma ve ileri gramer", "order_num": 4, "icon": "🎄", "color": "#a855f7"},
            {"code": "C1", "name": "İleri", "description": "Akademik ve profesyonel İngilizce", "order_num": 5, "icon": "🏆", "color": "#ff4b4b"},
            {"code": "C2", "name": "Uzman", "description": "Ana dil seviyesinde hakimiyet", "order_num": 6, "icon": "👑", "color": "#ffd700"},
        ]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        added = 0
        
        try:
            for level in levels:
                cursor.execute("SELECT 1 FROM cefr_levels WHERE code = ?", (level["code"],))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO cefr_levels (code, name, description, order_num, icon, color)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (level["code"], level["name"], level["description"], 
                          level["order_num"], level["icon"], level["color"]))
                    added += 1
            
            conn.commit()
            print(f"✓ {added} seviye eklendi")
            return added
            
        except Exception as e:
            print(f"❌ Seviye ekleme hatası: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def seed_units(self):
        """Her seviye için 5 ünite ekle."""
        units_data = {
            "A1": [
                {"order": 1, "title": "Selamlaşma", "desc": "Merhaba, günaydın, hoşça kal", "icon": "👋"},
                {"order": 2, "title": "Kendini Tanıtma", "desc": "Ad, yaş, ülke, meslek", "icon": "🙋"},
                {"order": 3, "title": "Sayılar", "desc": "1-100 arası sayılar", "icon": "🔢"},
                {"order": 4, "title": "Renkler", "desc": "Temel renkler ve tanımlar", "icon": "🎨"},
                {"order": 5, "title": "Aile", "desc": "Aile üyeleri ve ilişkiler", "icon": "👨‍👩‍👧‍👦"},
            ],
            "A2": [
                {"order": 1, "title": "Günlük Rutinler", "desc": "Sabah, akşam aktiviteleri", "icon": "🌅"},
                {"order": 2, "title": "Yiyecek-İçecek", "desc": "Restoran, market, yemek", "icon": "🍕"},
                {"order": 3, "title": "Hava Durumu", "desc": "Mevsimler ve hava", "icon": "🌤️"},
                {"order": 4, "title": "Ulaşım", "desc": "Araçlar ve yol tarifi", "icon": "🚗"},
                {"order": 5, "title": "Alışveriş", "desc": "Mağaza, fiyat, ödeme", "icon": "🛒"},
            ],
            "B1": [
                {"order": 1, "title": "İş Hayatı", "desc": "Ofis, toplantı, iş başvurusu", "icon": "💼"},
                {"order": 2, "title": "Sağlık", "desc": "Hastane, doktor, hastalıklar", "icon": "🏥"},
                {"order": 3, "title": "Seyahat", "desc": "Otel, havalimanı, tatil", "icon": "✈️"},
                {"order": 4, "title": "Eğitim", "desc": "Okul, üniversite, dersler", "icon": "🎓"},
                {"order": 5, "title": "Teknoloji", "desc": "Bilgisayar, internet, sosyal medya", "icon": "💻"},
            ],
            "B2": [
                {"order": 1, "title": "Medya ve Haberler", "desc": "Gazete, TV, haberler", "icon": "📰"},
                {"order": 2, "title": "Çevre", "desc": "Doğa, iklim değişikliği", "icon": "🌍"},
                {"order": 3, "title": "Kültür ve Sanat", "desc": "Müze, sinema, müzik", "icon": "🎭"},
                {"order": 4, "title": "Ekonomi", "desc": "Para, banka, yatırım", "icon": "📈"},
                {"order": 5, "title": "Politika", "desc": "Hükümet, seçim, yasalar", "icon": "🏛️"},
            ],
        }
        
        conn = get_db_connection()
        cursor = conn.cursor()
        added = 0
        
        try:
            for level_code, units in units_data.items():
                for unit in units:
                    cursor.execute("""
                        SELECT 1 FROM course_units WHERE level_code = ? AND order_num = ?
                    """, (level_code, unit["order"]))
                    
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO course_units (level_code, order_num, title, description, icon)
                            VALUES (?, ?, ?, ?, ?)
                        """, (level_code, unit["order"], unit["title"], unit["desc"], unit["icon"]))
                        added += 1
            
            conn.commit()
            print(f"✓ {added} ünite eklendi")
            return added
            
        except Exception as e:
            print(f"❌ Ünite ekleme hatası: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def seed_lessons(self):
        """Her ünite için 5 ders ekle."""
        lesson_types = [
            {"order": 1, "type": "vocabulary", "title": "Kelime Öğren", "desc": "Yeni kelimeler öğren", "xp": 10},
            {"order": 2, "type": "translation", "title": "Çeviri Yap", "desc": "Kelimeleri çevir", "xp": 10},
            {"order": 3, "type": "listening", "title": "Dinleme", "desc": "Dinle ve anla", "xp": 15},
            {"order": 4, "type": "grammar", "title": "Gramer", "desc": "Cümle kur", "xp": 15},
            {"order": 5, "type": "quiz", "title": "Test", "desc": "Bilgini test et", "xp": 20},
        ]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        added = 0
        
        try:
            # Tüm üniteleri al
            cursor.execute("SELECT unit_id, title FROM course_units")
            units = cursor.fetchall()
            
            for unit_id, unit_title in units:
                for lesson in lesson_types:
                    cursor.execute("""
                        SELECT 1 FROM course_lessons WHERE unit_id = ? AND order_num = ?
                    """, (unit_id, lesson["order"]))
                    
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO course_lessons (unit_id, order_num, lesson_type, title, description, xp_reward)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (unit_id, lesson["order"], lesson["type"], 
                              lesson["title"], lesson["desc"], lesson["xp"]))
                        added += 1
            
            conn.commit()
            print(f"✓ {added} ders eklendi")
            return added
            
        except Exception as e:
            print(f"❌ Ders ekleme hatası: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    # ==================== İLERLEME YÖNETİMİ ====================
    
    def init_user_progress(self, user_id: int, start_level: str = 'A1'):
        """Kullanıcı için kurs ilerlemesini belirtilen seviyeden başlat."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Seviye sıralaması
        level_order = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4}
        start_order = level_order.get(start_level, 1)
        
        try:
            # Mevcut progress kayıtlarını temizle (yeni baştan başlatma)
            cursor.execute("DELETE FROM user_course_progress WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM user_course_state WHERE user_id = ?", (user_id,))
            
            # Kullanıcı durumu oluştur (belirtilen seviyeden)
            cursor.execute("""
                INSERT INTO user_course_state (user_id, current_level, total_xp, hearts)
                VALUES (?, ?, 0, 5)
            """, (user_id, start_level))
            
            # Önceki seviyelerin tüm ünitelerini ve derslerini tamamlanmış olarak işaretle
            for level_code, order in level_order.items():
                if order < start_order:
                    # Bu seviyedeki tüm üniteleri al
                    cursor.execute("""
                        SELECT unit_id FROM course_units WHERE level_code = ?
                    """, (level_code,))
                    units = cursor.fetchall()
                    
                    for (unit_id,) in units:
                        # Üniteyi tamamlanmış olarak işaretle
                        cursor.execute("""
                            INSERT INTO user_course_progress 
                            (user_id, level_code, unit_id, status, crowns)
                            VALUES (?, ?, ?, 'completed', 3)
                        """, (user_id, level_code, unit_id))
                        
                        # Bu ünitedeki dersleri de tamamlanmış olarak işaretle
                        cursor.execute("""
                            SELECT lesson_id FROM course_lessons WHERE unit_id = ?
                        """, (unit_id,))
                        lessons = cursor.fetchall()
                        
                        for (lesson_id,) in lessons:
                            cursor.execute("""
                                INSERT INTO user_course_progress 
                                (user_id, level_code, unit_id, lesson_id, status, best_score)
                                VALUES (?, ?, ?, ?, 'completed', 100)
                            """, (user_id, level_code, unit_id, lesson_id))
            
            # Başlangıç seviyesinin ilk ünitesini aç
            cursor.execute("""
                SELECT unit_id FROM course_units WHERE level_code = ? AND order_num = 1
            """, (start_level,))
            first_unit = cursor.fetchone()
            
            if first_unit:
                cursor.execute("""
                    INSERT INTO user_course_progress 
                    (user_id, level_code, unit_id, status)
                    VALUES (?, ?, ?, 'unlocked')
                """, (user_id, start_level, first_unit[0]))
                
                # İlk dersi de aç
                cursor.execute("""
                    SELECT lesson_id FROM course_lessons WHERE unit_id = ? AND order_num = 1
                """, (first_unit[0],))
                first_lesson = cursor.fetchone()
                
                if first_lesson:
                    cursor.execute("""
                        INSERT INTO user_course_progress 
                        (user_id, level_code, unit_id, lesson_id, status)
                        VALUES (?, ?, ?, ?, 'unlocked')
                    """, (user_id, start_level, first_unit[0], first_lesson[0]))
            
            conn.commit()
            print(f"✓ Kullanıcı {user_id} için kurs ilerlemesi {start_level} seviyesinden başlatıldı")
            return True
            
        except Exception as e:
            print(f"❌ İlerleme başlatma hatası: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_user_course_map(self, user_id: int) -> Dict[str, Any]:
        """Kullanıcının kurs haritasını getir (Duolingo tarzı görünüm için)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Kullanıcı durumunu al
            cursor.execute("""
                SELECT current_level, total_xp, total_crowns, hearts, streak_days
                FROM user_course_state WHERE user_id = ?
            """, (user_id,))
            state = cursor.fetchone()
            
            if not state:
                # Kullanıcının users tablosundaki seviyesini al
                cursor.execute("SELECT level FROM users WHERE user_id = ?", (user_id,))
                user_level_row = cursor.fetchone()
                user_level = user_level_row[0] if user_level_row and user_level_row[0] else 'A1'
                conn.close()  # init_user_progress kendi bağlantısını kullanacak
                
                self.init_user_progress(user_id, user_level)
                
                # Tekrar bağlan ve state'i al
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT current_level, total_xp, total_crowns, hearts, streak_days
                    FROM user_course_state WHERE user_id = ?
                """, (user_id,))
                state = cursor.fetchone()
                if not state:
                    state = (user_level, 0, 0, 5, 0)
            
            current_level, total_xp, total_crowns, hearts, streak = state
            
            # Seviyeleri al
            cursor.execute("""
                SELECT code, name, icon, color, order_num FROM cefr_levels ORDER BY order_num
            """)
            levels = []
            
            for level_row in cursor.fetchall():
                level_code, level_name, level_icon, level_color, level_order = level_row
                
                # Bu seviyedeki üniteleri al
                cursor.execute("""
                    SELECT u.unit_id, u.order_num, u.title, u.description, u.icon,
                           COALESCE(p.status, 'locked') as status,
                           COALESCE(p.crowns, 0) as crowns
                    FROM course_units u
                    LEFT JOIN user_course_progress p ON u.unit_id = p.unit_id AND p.user_id = ? AND p.lesson_id IS NULL
                    WHERE u.level_code = ?
                    ORDER BY u.order_num
                """, (user_id, level_code))
                
                units = []
                for unit_row in cursor.fetchall():
                    unit_id, order_num, title, desc, icon, status, crowns = unit_row
                    
                    # Ünite derslerini al
                    cursor.execute("""
                        SELECT l.lesson_id, l.order_num, l.lesson_type, l.title, l.xp_reward,
                               COALESCE(p.status, 'locked') as status,
                               COALESCE(p.best_score, 0) as best_score
                        FROM course_lessons l
                        LEFT JOIN user_course_progress p ON l.lesson_id = p.lesson_id AND p.user_id = ? AND p.lesson_id IS NOT NULL
                        WHERE l.unit_id = ?
                        ORDER BY l.order_num
                    """, (user_id, unit_id))
                    
                    lessons = []
                    for lesson_row in cursor.fetchall():
                        lessons.append({
                            "lesson_id": lesson_row[0],
                            "order": lesson_row[1],
                            "type": lesson_row[2],
                            "title": lesson_row[3],
                            "xp": lesson_row[4],
                            "status": lesson_row[5],
                            "best_score": lesson_row[6]
                        })
                    
                    units.append({
                        "unit_id": unit_id,
                        "order": order_num,
                        "title": title,
                        "description": desc,
                        "icon": icon,
                        "status": status,
                        "crowns": crowns,
                        "lessons": lessons
                    })
                
                levels.append({
                    "code": level_code,
                    "name": level_name,
                    "icon": level_icon,
                    "color": level_color,
                    "units": units
                })
            
            return {
                "user_id": user_id,
                "current_level": current_level,
                "total_xp": total_xp,
                "total_crowns": total_crowns,
                "hearts": hearts,
                "streak": streak,
                "levels": levels
            }
            
        except Exception as e:
            print(f"❌ Kurs haritası hatası: {e}")
            return {}
        finally:
            conn.close()
    
    def complete_lesson(self, user_id: int, lesson_id: int, score: int) -> Dict[str, Any]:
        """Ders tamamla ve sonraki dersi aç."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Ders bilgisini al
            cursor.execute("""
                SELECT l.unit_id, l.order_num, l.xp_reward, u.level_code
                FROM course_lessons l
                JOIN course_units u ON l.unit_id = u.unit_id
                WHERE l.lesson_id = ?
            """, (lesson_id,))
            lesson_info = cursor.fetchone()
            
            if not lesson_info:
                return {"success": False, "error": "Ders bulunamadı"}
            
            unit_id, lesson_order, xp_reward, level_code = lesson_info
            
            # İlerlemeyi güncelle
            cursor.execute("""
                INSERT INTO user_course_progress 
                (user_id, level_code, unit_id, lesson_id, status, best_score, attempts, completed_at, last_activity)
                VALUES (?, ?, ?, ?, 'completed', ?, 1, ?, ?)
                ON CONFLICT(user_id, unit_id, lesson_id) DO UPDATE SET
                    status = 'completed',
                    best_score = MAX(best_score, ?),
                    attempts = attempts + 1,
                    last_activity = ?
            """, (user_id, level_code, unit_id, lesson_id, score, 
                  datetime.now(), datetime.now(), score, datetime.now()))
            
            # XP ekle
            earned_xp = xp_reward * (score / 100)

            cursor.execute("""
                UPDATE user_course_state SET total_xp = total_xp + ?, last_lesson_at = ?
                WHERE user_id = ?
            """, (int(earned_xp), datetime.now(), user_id))
            
            # Sonraki dersi aç
            cursor.execute("""
                SELECT lesson_id FROM course_lessons 
                WHERE unit_id = ? AND order_num = ?
            """, (unit_id, lesson_order + 1))
            next_lesson = cursor.fetchone()
            
            unlocked_next = False
            if next_lesson:
                cursor.execute("""
                    INSERT OR IGNORE INTO user_course_progress 
                    (user_id, level_code, unit_id, lesson_id, status)
                    VALUES (?, ?, ?, ?, 'unlocked')
                """, (user_id, level_code, unit_id, next_lesson[0]))
                unlocked_next = True
            else:
                # Ünite bitti, üniteyi tamamla ve sonraki üniteyi aç
                cursor.execute("""
                    UPDATE user_course_progress SET status = 'completed', crowns = crowns + 1
                    WHERE user_id = ? AND unit_id = ? AND lesson_id IS NULL
                """, (user_id, unit_id))
                
                # Sonraki üniteyi bul
                cursor.execute("""
                    SELECT u2.unit_id FROM course_units u1
                    JOIN course_units u2 ON u1.level_code = u2.level_code AND u2.order_num = u1.order_num + 1
                    WHERE u1.unit_id = ?
                """, (unit_id,))
                next_unit = cursor.fetchone()
                
                if next_unit:
                    cursor.execute("""
                        INSERT OR IGNORE INTO user_course_progress 
                        (user_id, level_code, unit_id, status)
                        VALUES (?, ?, ?, 'unlocked')
                    """, (user_id, level_code, next_unit[0]))
                    
                    # İlk dersini de aç
                    cursor.execute("""
                        SELECT lesson_id FROM course_lessons WHERE unit_id = ? AND order_num = 1
                    """, (next_unit[0],))
                    first_lesson = cursor.fetchone()
                    if first_lesson:
                        cursor.execute("""
                            INSERT OR IGNORE INTO user_course_progress 
                            (user_id, level_code, unit_id, lesson_id, status)
                            VALUES (?, ?, ?, ?, 'unlocked')
                        """, (user_id, level_code, next_unit[0], first_lesson[0]))
            
            conn.commit()
            
            return {
                "success": True,
                "xp_earned": int(earned_xp),
                "score": score,
                "unlocked_next": unlocked_next
            }
            
        except Exception as e:
            print(f"❌ Ders tamamlama hatası: {e}")
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def get_lesson_questions(self, lesson_id: int, user_id: int) -> List[Dict]:
        """Ders için soruları getir."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Önce ders tipini ve ünite başlığını al
            cursor.execute("""
                SELECT l.lesson_type, l.unit_id, u.level_code, u.title
                FROM course_lessons l
                JOIN course_units u ON l.unit_id = u.unit_id
                WHERE l.lesson_id = ?
            """, (lesson_id,))
            lesson_info = cursor.fetchone()
            
            if not lesson_info:
                return []
            
            lesson_type, unit_id, level_code, unit_title = lesson_info
            
            # Hazır sorular varsa getir
            cursor.execute("""
                SELECT question_id, question_type, question_text, correct_answer, 
                       wrong_options, hint, word_id
                FROM lesson_questions
                WHERE lesson_id = ?
                ORDER BY order_num
            """, (lesson_id,))
            
            questions = []
            for row in cursor.fetchall():
                q = {
                    "question_id": row[0],
                    "type": row[1],
                    "question": row[2],
                    "answer": row[3],
                    "options": json.loads(row[4]) if row[4] else [],
                    "hint": row[5],
                    "word_id": row[6]
                }
                questions.append(q)
            
            # Hazır soru yoksa, words tablosundan dinamik oluştur (ünite konusuna göre)
            if not questions:
                questions = self._generate_questions(lesson_type, level_code, 10, unit_title)
            
            return questions
            
        except Exception as e:
            print(f"❌ Soru getirme hatası: {e}")
            return []
        finally:
            conn.close()
    
    def _generate_questions(self, lesson_type: str, level_code: str, count: int = 10, unit_title: str = None) -> List[Dict]:
        """Words tablosundan dinamik soru oluştur."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        questions = []
        
        # Ünite → Kategori eşleştirmesi
        unit_categories = {
            # A1
            "Selamlaşma": ["greetings", "introduction"],
            "Kendini Tanıtma": ["introduction", "greetings"],
            "Sayılar": ["numbers", "time"],
            "Renkler": ["colors", "descriptive"],
            "Aile": ["family", "introduction"],
            
            # A2
            "Günlük Rutinler": ["daily_routine", "time", "actions"],
            "Yiyecek-İçecek": ["food", "shopping"],
            "Hava Durumu": ["weather", "nature"],
            "Ulaşım": ["transport", "travel"],
            "Alışveriş": ["shopping", "clothing", "numbers"],
            
            # B1
            "İş Hayatı": ["work", "communication", "technology"],
            "Sağlık": ["health", "body", "emotions"],
            "Seyahat": ["travel", "transport", "culture"],
            "Eğitim": ["education", "communication"],
            "Teknoloji": ["technology", "communication"],
            
            # B2
            "Medya ve Haberler": ["media", "communication"],
            "Çevre": ["environment", "nature", "animals"],
            "Kültür ve Sanat": ["culture", "emotions"],
            "Ekonomi": ["economy", "work"],
            "Politika": ["politics", "communication"],
        }
        
        try:
            # Üniteye ait kategorileri al
            categories = []
            if unit_title and unit_title in unit_categories:
                categories = unit_categories[unit_title]
            
            # Önce kategoriye göre kelime ara (SEVİYE FİLTRESİ İLE)
            words = []
            if categories:
                placeholders = ",".join(["?" for _ in categories])
                cursor.execute(f"""
                    SELECT word_id, english, turkish, example_sentence
                    FROM words
                    WHERE category IN ({placeholders})
                    AND level = ?
                    AND turkish IS NOT NULL AND turkish != ''
                    ORDER BY RANDOM()
                    LIMIT ?
                """, (*categories, level_code, count))
                words = cursor.fetchall()
            
            # Eğer kategoride yeterli kelime yoksa, aynı seviyeden genel kelimelerden tamamla
            if len(words) < count:
                remaining = count - len(words)
                existing_ids = [w[0] for w in words]
                
                if existing_ids:
                    placeholders = ",".join(["?" for _ in existing_ids])
                    cursor.execute(f"""
                        SELECT word_id, english, turkish, example_sentence
                        FROM words
                        WHERE turkish IS NOT NULL AND turkish != ''
                        AND level = ?
                        AND category != 'other'
                        AND word_id NOT IN ({placeholders})
                        ORDER BY RANDOM()
                        LIMIT ?
                    """, (level_code, *existing_ids, remaining))
                else:
                    cursor.execute("""
                        SELECT word_id, english, turkish, example_sentence
                        FROM words
                        WHERE turkish IS NOT NULL AND turkish != ''
                        AND level = ?
                        AND category != 'other'
                        ORDER BY RANDOM()
                        LIMIT ?
                    """, (level_code, remaining))
                
                words.extend(cursor.fetchall())
            
            # Hala yeterli kelime yoksa, bir alt veya üst seviyeden al
            if len(words) < count:
                remaining = count - len(words)
                existing_ids = [w[0] for w in words]
                
                # Seviye sırası
                level_order = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
                current_idx = level_order.index(level_code) if level_code in level_order else 0
                
                # Yakın seviyeleri dene (önce bir alt, sonra bir üst)
                nearby_levels = []
                if current_idx > 0:
                    nearby_levels.append(level_order[current_idx - 1])
                if current_idx < len(level_order) - 1:
                    nearby_levels.append(level_order[current_idx + 1])
                
                if existing_ids and nearby_levels:
                    id_placeholders = ",".join(["?" for _ in existing_ids])
                    level_placeholders = ",".join(["?" for _ in nearby_levels])
                    cursor.execute(f"""
                        SELECT word_id, english, turkish, example_sentence
                        FROM words
                        WHERE turkish IS NOT NULL AND turkish != ''
                        AND level IN ({level_placeholders})
                        AND word_id NOT IN ({id_placeholders})
                        ORDER BY RANDOM()
                        LIMIT ?
                    """, (*nearby_levels, *existing_ids, remaining))
                elif nearby_levels:
                    level_placeholders = ",".join(["?" for _ in nearby_levels])
                    cursor.execute(f"""
                        SELECT word_id, english, turkish, example_sentence
                        FROM words
                        WHERE turkish IS NOT NULL AND turkish != ''
                        AND level IN ({level_placeholders})
                        ORDER BY RANDOM()
                        LIMIT ?
                    """, (*nearby_levels, remaining))
                
                words.extend(cursor.fetchall())
            
            for i, word in enumerate(words):
                word_id, english, turkish, example = word
                
                # Türkçe çevirisi yoksa, API'den al (cache sistemi ile)
                if not turkish or turkish.strip() == '':
                    turkish = get_translation(english)
                    if not turkish:
                        continue  # Çeviri alınamazsa bu kelimeyi atla
                
                # Yanlış seçenekler için aynı seviyeden başka kelimeler al
                cursor.execute("""
                    SELECT turkish FROM words 
                    WHERE word_id != ? AND turkish IS NOT NULL AND turkish != ''
                    AND level = ?
                    ORDER BY RANDOM() LIMIT 5
                """, (word_id, level_code))
                wrong_options = [r[0] for r in cursor.fetchall()]
                
                # Eğer aynı seviyeden yeterli seçenek bulunamazsa, yakın seviyelerden tamamla
                if len(wrong_options) < 3:
                    level_order = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
                    current_idx = level_order.index(level_code) if level_code in level_order else 0
                    nearby_levels = []
                    if current_idx > 0:
                        nearby_levels.append(level_order[current_idx - 1])
                    if current_idx < len(level_order) - 1:
                        nearby_levels.append(level_order[current_idx + 1])
                    
                    if nearby_levels:
                        level_placeholders = ",".join(["?" for _ in nearby_levels])
                        cursor.execute(f"""
                            SELECT turkish FROM words 
                            WHERE word_id != ? AND turkish IS NOT NULL AND turkish != ''
                            AND level IN ({level_placeholders})
                            ORDER BY RANDOM() LIMIT ?
                        """, (word_id, *nearby_levels, 5 - len(wrong_options)))
                        wrong_options.extend([r[0] for r in cursor.fetchall()])
                
                # Yanlış seçeneklerde doğru cevap varsa çıkar
                wrong_options = [opt for opt in wrong_options if opt.lower() != turkish.lower()][:3]
                # Tüm seçenekleri karıştır
                import random
                all_options = wrong_options + [turkish]
                random.shuffle(all_options)
                
                if lesson_type == "vocabulary":
                    q = {
                        "question_id": i + 1,
                        "type": "word_to_turkish",
                        "question": english,
                        "answer": turkish,
                        "options": all_options,
                        "hint": example,
                        "word_id": word_id
                    }
                elif lesson_type == "translation":
                    q = {
                        "question_id": i + 1,
                        "type": "turkish_to_word",
                        "question": turkish,
                        "answer": english,
                        "options": [],  # Yazarak cevap
                        "hint": f"{english[:1] if len(english) <= 2 else english[:2]}...",
                        "word_id": word_id
                    }
                elif lesson_type == "listening":
                    q = {
                        "question_id": i + 1,
                        "type": "listen_select",
                        "question": f"🔊 '{english}' kelimesini dinle",
                        "answer": turkish,
                        "options": all_options,
                        "hint": None,
                        "word_id": word_id,
                        "audio_text": english
                    }
                elif lesson_type == "grammar":
                    q = {
                        "question_id": i + 1,
                        "type": "grammar",
                        "question": english,
                        "answer": english,
                        "options": [],
                        "hint": None,
                        "word_id": word_id
                    }
                elif lesson_type == "pronunciation":
                    q = {
                        "question_id": i + 1,
                        "type": "pronunciation",
                        "question": f"'{english}' kelimesini telaffuz et",
                        "answer": english,
                        "options": [],
                        "hint": turkish,
                        "word_id": word_id,
                        "audio_text": english
                    }
                else:  # quiz - karışık
                    q = {
                        "question_id": i + 1,
                        "type": "word_to_turkish" if i % 2 == 0 else "turkish_to_word",
                        "question": english if i % 2 == 0 else turkish,
                        "answer": turkish if i % 2 == 0 else english,
                        "options": all_options if i % 2 == 0 else [],
                        "hint": example,
                        "word_id": word_id
                    }
                
                questions.append(q)
            
            return questions
            
        except Exception as e:
            print(f"❌ Soru oluşturma hatası: {e}")
            return []
        finally:
            conn.close()


# Singleton instance
course_system = CourseSystem()
