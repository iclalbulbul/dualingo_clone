from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from backend.rules import analyze_sentence
from backend.ai_utils import grammar_feedback_json, pronunciation_feedback, generate_sentence, personalized_feedback, generate_custom_lesson, mistake_feedback
from backend.speech_stt import recognize_from_audio_file, recognize_from_blob
from db_utils import get_db_connection, get_user_id, create_or_get_user, update_review_result, record_mistake, register_user, login_user, get_user_mistakes
from backend.recommender import get_review_quiz
from translation_utils import get_translation, check_answer
from user_db import UserInputLogger
from features.user_stats import UserStats
from features.goals import GoalManager
from features.leaderboard import LeaderboardManager
from features.notifications import NotificationManager
from features.social import SocialManager
from features.courses import CourseManager
from features.course_system import course_system
import json
import random
from datetime import datetime
import time
import os


# ==================== RATE LIMITER ====================
class RateLimiter:
    """Basit rate limiter - API isteklerini sınırlar."""
    
    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    def _clean_old_requests(self):
        """Eski istekleri temizle."""
        now = time.time()
        self.requests = [r for r in self.requests if now - r < self.window_seconds]
    
    def can_request(self) -> bool:
        """İstek yapılabilir mi?"""
        self._clean_old_requests()
        return len(self.requests) < self.max_requests
    
    def add_request(self):
        """Yeni istek ekle."""
        self.requests.append(time.time())
    
    def get_remaining(self) -> int:
        """Kalan istek hakkı."""
        self._clean_old_requests()
        return max(0, self.max_requests - len(self.requests))
    
    def get_wait_time(self) -> float:
        """Yeni istek için bekleme süresi (saniye)."""
        if self.can_request():
            return 0
        self._clean_old_requests()
        if not self.requests:
            return 0
        oldest = min(self.requests)
        return max(0, self.window_seconds - (time.time() - oldest))


app = Flask(__name__)
# Secret key: Önce environment variable'dan al, yoksa fallback kullan
# Production'da mutlaka SECRET_KEY environment variable'ı set edilmeli!
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key_change_in_production_" + str(hash("dualingo_clone")))

# Rate limiter instance
rate_limiter = RateLimiter(max_requests=20, window_seconds=60)

# Managers'ı başlat
logger = UserInputLogger()
stats_manager = UserStats()
goal_manager = GoalManager()
leaderboard_manager = LeaderboardManager()
notification_manager = NotificationManager()
social_manager = SocialManager()
course_manager = CourseManager()

# ==================== API ENDPOINTS ====================

@app.route("/api/rate-limit")
def api_rate_limit():
    """API rate limit durumunu döner"""
    remaining = rate_limiter.get_remaining()
    wait_time = rate_limiter.get_wait_time()
    return jsonify({
        "remaining": remaining,
        "max": 20,
        "wait_seconds": int(wait_time),
        "can_request": remaining > 0
    })

@app.route("/api/unread-notifications")
def api_unread_notifications():
    """Okunmamış bildirim sayısını döner"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"count": 0})
    
    try:
        count = notification_manager.get_unread_notification_count(user_id)
        return jsonify({"count": count})
    except:
        return jsonify({"count": 0})

@app.route("/api/dashboard-stats")
def api_dashboard_stats():
    """Dashboard için hızlı istatistikler"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({})
    
    try:
        daily = stats_manager.get_daily_stats(user_id)
        overall = stats_manager.get_overall_stats(user_id)
        rank = leaderboard_manager.get_user_rank(user_id, 'all')
        
        return jsonify({
            "streak": daily.get("streak", 0),
            "today_correct": daily.get("correct_answers", 0),
            "words_learned": overall.get("total_words_learned", 0),
            "rank": rank.get("rank") if rank else None,
            "total_inputs": overall.get("total_inputs", 0),
            "accuracy": overall.get("accuracy", 0)
        })
    except Exception as e:
        print(f"Dashboard stats error: {e}")
        return jsonify({
            "streak": 0,
            "today_correct": 0,
            "words_learned": 0,
            "rank": None
        })

#------------LOGİN İÇİN OLUŞTURULDU--------------------#

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        action = request.form.get("action", "login")  # login veya register

        if not username:
            return render_template("login.html", error="Kullanıcı adı boş olamaz.")
        
        if not password:
            return render_template("login.html", error="Şifre boş olamaz.")

        # Kayıt veya Giriş
        if action == "register":
            result = register_user(username, password)
            if not result["success"]:
                return render_template("login.html", error=result["error"])
            user_id = result["user_id"]
        else:
            result = login_user(username, password)
            if not result["success"]:
                return render_template("login.html", error=result["error"])
            user_id = result["user_id"]
        
        session["username"] = username
        session["user_id"] = user_id
        
        # Oturum başlat ve loglama yap
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        session_id = logger.log_session_start(
            user_id=user_id,
            ip_address=ip_address,
            device_info=user_agent
        )
        session["session_id"] = session_id
        
        # Giriş aksiyonunu kaydet
        logger.log_user_action(
            user_id=user_id,
            action_type='login',
            action_details=f'Kullanıcı {username} giriş yaptı',
            page='login',
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return redirect(url_for("dashboard"))

    # GET isteğinde direkt login sayfasını göster
    return render_template("login.html")


#------DASHBOARD İÇİN OLUŞTURULDU---------#
@app.route("/dashboard")
def dashboard():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    
    # Dashboard ziyaretini kaydet
    logger.log_user_action(
        user_id=user_id,
        action_type='page_visit',
        action_details='Dashboard ziyareti',
        page='dashboard',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    # Aktif hedefleri al
    active_goals = goal_manager.get_active_goals(user_id)

    return render_template("dashboard.html", username=username, active_goals=active_goals)


#-----WORD PRACTİCE (KELİME ALIŞTIRMASI) İÇİN OLUŞTURULDU-------#
@app.route("/practice_word", methods=["GET", "POST"])

def practice_word():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    
    # Database'den random bir kelime al
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # GET: başlat, POST: kontrol et
    current_word = None
    result = None
    
    if request.method == "GET":
        # A1 seviye dari random bir kelime seç
        cursor.execute("SELECT word_id, english, topic_id FROM words WHERE level='A1' ORDER BY RANDOM() LIMIT 1")
        word_row = cursor.fetchone()
        
        if word_row:
            current_word = {
                "word_id": word_row[0],
                "english": word_row[1],
                "topic_id": word_row[2]
            }
    
    elif request.method == "POST":
        word_id = request.form.get("word_id")
        user_answer = request.form.get("answer", "").strip()
        
        # Kelimeyi database'den al
        if word_id:
            cursor.execute("SELECT english, turkish FROM words WHERE word_id = ?", (word_id,))
            word_row = cursor.fetchone()
            
            if word_row:
                english_word = word_row[0]
                
                # Çeviri al (önce DB cache, yoksa API)
                try:
                    api_translation = get_translation(english_word)
                    
                    if api_translation:
                        # Cevabı kontrol et (similarity check ile)
                        check_result = check_answer(user_answer, api_translation, threshold=0.80)
                        
                        result = {
                            "user_answer": user_answer,
                            "correct_answer": check_result["correct_answer"],
                            "is_correct": check_result["is_correct"],
                            "similarity": check_result["similarity"],
                            "feedback": check_result["feedback"],
                            "english": english_word
                        }
                    else:
                        # API hata varsa fallback
                        result = {
                            "user_answer": user_answer,
                            "correct_answer": "Çeviri API'sinden hata",
                            "is_correct": False,
                            "similarity": 0.0,
                            "feedback": "Çeviri alınamadı, lütfen tekrar deneyin",
                            "english": english_word
                        }
                
                except Exception as e:
                    print(f"[Error] Translation API: {str(e)}")
                    result = {
                        "user_answer": user_answer,
                        "correct_answer": "Hata oluştu",
                        "is_correct": False,
                        "similarity": 0.0,
                        "feedback": "Çeviri işleminde hata oluştu",
                        "english": english_word
                    }
                
                # Sonucu veritabanına kaydet
                if user_id and result:
                    cursor.execute("""
                        INSERT INTO practice_history (user_id, practice_type, word_id, is_correct, attempted_answer)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, "word_practice", word_id, 1 if result["is_correct"] else 0, user_answer))
                    conn.commit()
                    
                    # UserInputLogger ile çeviri denemesini kaydet
                    logger.log_translation_attempt(
                        user_id=user_id,
                        english_word=english_word,
                        turkish_translation=user_answer,
                        correct_translation=result["correct_answer"],
                        similarity_score=result["similarity"],
                        is_correct=result["is_correct"],
                        word_id=int(word_id),
                        attempt_number=1
                    )
                    
                    # Genel giriş logu
                    logger.log_user_input(
                        user_id=user_id,
                        input_type='word_translation',
                        input_text=user_answer,
                        response_text=result["correct_answer"],
                        is_correct=result["is_correct"],
                        score=result["similarity"] * 100,
                        word_id=int(word_id),
                        metadata={'english': english_word, 'feedback': result["feedback"]}
                    )
                    
                    # Hedef ilerlemesini senkronize et
                    goal_manager.sync_goal_progress(user_id)

                    # Eğer çeviri yanlışsa mistakes tablosuna ekle
                    try:
                        if not result.get("is_correct"):
                            record_mistake(
                                user_id=user_id,
                                item_key=english_word,
                                wrong_answer=user_answer,
                                correct_answer=result.get("correct_answer"),
                                lesson_id="practice_word",
                                context="word",
                            )
                    except Exception:
                        pass
        
        # Sonra yeni bir kelime göster
        cursor.execute("SELECT word_id, english, topic_id FROM words WHERE level='A1' ORDER BY RANDOM() LIMIT 1")
        word_row = cursor.fetchone()
        
        if word_row:
            current_word = {
                "word_id": word_row[0],
                "english": word_row[1],
                "topic_id": word_row[2]
            }
    
    conn.close()
    
    return render_template(
        "practice_word.html",
        username=username,
        word=current_word,
        result=result
    )
    

#-------SeNTENCE VE GRAMMER PRACTİCE----------------#
@app.route("/practice/sentence", methods=["GET","POST"])
def practice_sentence():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    feedback = None
    user_sentence = None
    analysis_result = None
    ai_feedback = None
    example_sentence = None
    target_word = None

    # GET isteğinde örnek kelime ve cümle oluştur
    if request.method == "GET":
        # Rastgele bir kelime seç
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT english FROM words WHERE level='A1' ORDER BY RANDOM() LIMIT 1")
        word_row = cursor.fetchone()
        conn.close()
        
        if word_row:
            target_word = word_row[0]
            # AI ile örnek cümle oluştur
            try:
                example_sentence = generate_sentence(target_word)
                # Fallback kontrolü - eğer basit mesaj dönerse düzelt
                if not example_sentence or "using the word" in example_sentence.lower():
                    example_sentence = f"Example: The {target_word} is very important in daily life."
            except Exception as e:
                print(f"generate_sentence hatası: {e}")
                example_sentence = f"Example: I like to use the word '{target_word}' in my sentences."

    if request.method == "POST":
        user_sentence = request.form.get("sentence", "").strip()
        target_word = request.form.get("target_word", "")

        if user_sentence:
            # 1. Rules-based grammar kontrol (temel kontroller - dil, yapı vb.)
            analysis_result = analyze_sentence(user_sentence)
            
            # Eğer dil hatası varsa (Türkçe yazılmış vb.) direkt rules sonucunu kullan
            has_language_error = any(err.get("rule") == "language_error" for err in analysis_result.get("errors", []))
            
            # 2. HEDEF KELİME KONTROLÜ - Cümlede hedef kelime kullanılmış mı?
            if target_word and not has_language_error:
                target_lower = target_word.lower().strip()
                sentence_lower = user_sentence.lower()
                
                # Kelimenin cümlede olup olmadığını kontrol et
                import re
                word_pattern = r'\b' + re.escape(target_lower) + r'\b'
                if not re.search(word_pattern, sentence_lower):
                    # Hedef kelime cümlede yok
                    analysis_result["errors"].append({
                        "rule": "missing_target_word",
                        "message_tr": f"Hedef kelime '{target_word}' cümlede kullanılmamış. Lütfen bu kelimeyi cümlenizde kullanın."
                    })
                    analysis_result["is_valid"] = False
                    analysis_result["score"] = max(0, analysis_result["score"] - 30)
                    analysis_result["suggestions"].append(f"'{target_word}' kelimesini cümlenizde kullanın.")
            
            # 3. AI-powered grammar feedback (asıl gramer kontrolü)
            ai_feedback = None
            if not has_language_error:
                try:
                    ai_result = grammar_feedback_json(user_sentence)
                    if ai_result:
                        ai_feedback = {
                            "corrected": ai_result.get("corrected", user_sentence),
                            "mistakes": ai_result.get("mistakes", [])
                        }
                        
                        # AI sonucu varsa, feedback'i AI'dan al
                        if ai_result.get("mistakes"):
                            # AI hata buldu - feedback'i güncelle
                            ai_errors = []
                            for mistake in ai_result.get("mistakes", []):
                                ai_errors.append({
                                    "rule": "ai_grammar",
                                    "message_tr": f"'{mistake.get('part', '')}': {mistake.get('explanation_tr', 'Gramer hatası')}"
                                })
                            
                            # AI sonucunu ana feedback'e entegre et
                            analysis_result["errors"].extend(ai_errors)
                            analysis_result["is_valid"] = False
                            # Score'u hata sayısına göre düşür
                            penalty = len(ai_errors) * 15
                            analysis_result["score"] = max(0, analysis_result["score"] - penalty)
                            analysis_result["suggestions"].append(f"Düzeltilmiş hali: {ai_result.get('corrected', user_sentence)}")
                        else:
                            # AI hata bulmadı ve rules da hata bulmadıysa başarılı
                            if analysis_result["is_valid"]:
                                analysis_result["score"] = 100
                except Exception as e:
                    print(f"AI Grammar hatası: {e}")
                    # AI başarısız olursa rules sonucuyla devam et
            
            feedback = {
                "is_valid": analysis_result["is_valid"],
                "score": analysis_result["score"],
                "errors": analysis_result["errors"],
                "suggestions": analysis_result["suggestions"]
            }
            
            # Veritabanında hataları kaydet
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                if user_id and analysis_result["errors"]:
                    timestamp = datetime.now().isoformat()
                    
                    for error in analysis_result["errors"]:
                        cursor.execute("""
                            INSERT INTO grammar_errors (user_id, sentence, error_type, error_message, score, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            user_id,
                            user_sentence,
                            error.get("rule"),
                            error.get("message_tr", ""),
                            analysis_result["score"],
                            timestamp
                        ))
                
                # UserInputLogger ile cümle analiz girdisini kaydet
                if user_id:
                    logger.log_user_input(
                        user_id=user_id,
                        input_type='sentence_analysis',
                        input_text=user_sentence,
                        response_text=json.dumps(analysis_result.get("suggestions", [])),
                        is_correct=analysis_result["is_valid"],
                        score=analysis_result["score"],
                        metadata={
                            'errors': analysis_result["errors"],
                            'suggestions': analysis_result["suggestions"],
                            'ai_feedback': ai_feedback
                        }
                    )
                    
                    # Aksiyon kaydı
                    logger.log_user_action(
                        user_id=user_id,
                        action_type='grammar_check',
                        action_details=f'Cümle kontrol: {user_sentence[:50]}...',
                        page='practice_sentence',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    
                    # Hedef ilerlemesini senkronize et
                    goal_manager.sync_goal_progress(user_id)
                
                conn.commit()
                
            except Exception as e:
                print(f"❌ DB logging hatası: {e}")
            finally:
                # Database bağlantısını her durumda kapat
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
            
            # Eğer kurallar veya LLM kontrolünde hata varsa, mistakes tablosuna ekle
            try:
                has_rules_error = analysis_result and not analysis_result.get("is_valid")
                has_llm_mistakes = ai_feedback and bool(ai_feedback.get("mistakes"))
                if user_id and (has_rules_error or has_llm_mistakes):
                    correct = (ai_feedback.get("corrected") if ai_feedback else None) or example_sentence or target_word
                    record_mistake(
                        user_id=user_id,
                        item_key=target_word or user_sentence[:30],
                        wrong_answer=user_sentence,
                        correct_answer=correct,
                        lesson_id="practice_sentence",
                        context="sentence",
                    )
            except Exception:
                pass
            
    return render_template(
        "practice_sentence.html",
        username=username,
        user_sentence=user_sentence,
        feedback=feedback,
        analysis_result=analysis_result,
        ai_feedback=ai_feedback,
        example_sentence=example_sentence,
        target_word=target_word
    )


#-------PRONUNCATİON PRACTİCE-----------#
@app.route("/pronunciation", methods=["GET", "POST"])
def pronunciation():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    
    score = None
    feedback_text = None
    recognized_text = None
    is_correct = False
    word_id = 0
    target_word = "apple"

    if request.method == "POST":
        # POST'ta kelimeyi formdan al (aynı kelimeyi değerlendir)
        target_word = request.form.get("target_word", "apple")
        word_id = int(request.form.get("word_id", 0))
        recognized_text = None
        
        # Ses dosyası geldi mi kontrol et
        if 'audio' in request.files:
            audio_file = request.files['audio']
            if audio_file and audio_file.filename:
                # speech_stt.py'deki fonksiyonu kullan
                recognized_text = recognize_from_audio_file(audio_file, language="en-US")
                print(f"🎤 STT Sonuç: {recognized_text}")
        
        # Eğer ses dosyası yoksa veya hata olduysa, text input'u kontrol et
        if not recognized_text or recognized_text.startswith("❌"):
            user_text = request.form.get("user_pronunciation", "").strip()
            if user_text:
                recognized_text = user_text
        
        # STT başarılıysa değerlendir
        if recognized_text and not recognized_text.startswith("❌"):
            try:
                # AI ile telaffuz değerlendirmesi
                pron_result = pronunciation_feedback(target_word, recognized_text)
                score = pron_result.get("score", 0)
                feedback_text = pron_result.get("feedback_tr", "Değerlendirme yapılamadı.")
                is_correct = score >= 70
            except Exception as e:
                print(f"Telaffuz değerlendirme hatası: {e}")
                # Basit benzerlik kontrolü (fallback)
                if recognized_text.lower() == target_word.lower():
                    score = 100
                    feedback_text = "Mükemmel! Doğru telaffuz."
                    is_correct = True
                elif target_word.lower() in recognized_text.lower():
                    score = 75
                    feedback_text = "İyi! Kelimeyi söyledin."
                    is_correct = True
                else:
                    score = 30
                    feedback_text = f"Tekrar dene. Hedef: {target_word}, Algılanan: {recognized_text}"
                    is_correct = False
        elif recognized_text and recognized_text.startswith("❌"):
            # STT hatası
            feedback_text = recognized_text
            score = 0
            is_correct = False
        
        # Telaffuz denemesini kaydet
        if user_id and score is not None:
            logger.log_pronunciation_attempt(
                user_id=user_id,
                word_id=word_id,
                target_word=target_word,
                score=score,
                accuracy=score,
                feedback=feedback_text,
                audio_file=None
            )
            
            logger.log_user_input(
                user_id=user_id,
                input_type='pronunciation_practice',
                input_text=f"{target_word} -> {recognized_text}",
                response_text=feedback_text,
                is_correct=is_correct,
                score=score,
                word_id=word_id,
                metadata={'accuracy': score, 'recognized': recognized_text}
            )
            
            logger.log_user_action(
                user_id=user_id,
                action_type='pronunciation_attempt',
                action_details=f'Telaffuz pratiği: {target_word}',
                page='pronunciation',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            # Eğer telaffuz yanlışsa mistakes tablosuna ekle
            try:
                if not is_correct:
                    record_mistake(
                        user_id=user_id,
                        item_key=target_word,
                        wrong_answer=recognized_text or "",
                        correct_answer=target_word,
                        lesson_id="pronunciation",
                        context="pronunciation",
                    )
            except Exception:
                pass
    
    else:
        # GET isteğinde yeni rastgele kelime al
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT word_id, english FROM words WHERE level IN ('A1', 'A2') ORDER BY RANDOM() LIMIT 1")
        word_row = cursor.fetchone()
        conn.close()
        
        if word_row:
            word_id = word_row[0]
            target_word = word_row[1]
            print(f"🎯 Yeni kelime seçildi: {target_word} (ID: {word_id})")
        else:
            print("⚠️ Veritabanından kelime bulunamadı, apple kullanılıyor")

    return render_template(
        "pronunciation.html",
        username=username,
        target_word=target_word,
        word_id=word_id,
        score=score,
        feedback=feedback_text,
        recognized=recognized_text,
        is_correct=is_correct
    )


@app.route("/review", methods=["GET"])
def review_quiz():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    quiz_items = []
    try:
        quiz_items = get_review_quiz(user_id=user_id, limit=30)
    except Exception as e:
        print(f"Review quiz load error: {e}")

    return render_template("review_quiz.html", username=username, quiz_items=quiz_items)


@app.route("/review/submit", methods=["POST"])
def review_submit():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    mistake_id = request.form.get("mistake_id")
    item_key = request.form.get("item_key")
    quality = int(request.form.get("quality", 0))

    # update_review_result expects user_id and item_key
    try:
        res = update_review_result(user_id=user_id, item_key=item_key, quality=quality)
        # kısa bir bildirim ekleyebiliriz
        notification_manager.create_notification(
            user_id=user_id,
            notification_type='review_result',
            title='Tekrar sonucu kaydedildi',
            message=f'"{item_key}" için sonuç kaydedildi.',
            icon='🔁'
        )
    except Exception as e:
        print(f"Review submit error: {e}")

    return redirect(url_for("review_quiz"))


@app.route("/review/seed", methods=["GET"]) 
def review_seed():
    """Seed some sample mistakes for the current user and redirect to /review."""
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    try:
        # A few example mistakes to display in the review UI
        record_mistake(user_id=user_id, item_key="banana", wrong_answer="bananna", correct_answer="banana", lesson_id="seed-1", context="sentence")
        record_mistake(user_id=user_id, item_key="apple", wrong_answer="appel", correct_answer="apple", lesson_id="seed-1", context="pronunciation")
        record_mistake(user_id=user_id, item_key="orange", wrong_answer="oragne", correct_answer="orange", lesson_id="seed-1", context="sentence")
    except Exception as e:
        print(f"Seed error: {e}")

    return redirect(url_for("review_quiz"))


@app.route("/my-mistakes")
def my_mistakes():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    mistakes = []
    try:
        raw_mistakes = get_user_mistakes(user_id=user_id, limit=200)
        # sqlite3.Row'ları dict'e dönüştür
        for mistake_row in raw_mistakes:
            # Row nesnesini dict'e çevir
            mistake = dict(mistake_row) if hasattr(mistake_row, 'keys') else mistake_row
            
            try:
                feedback = mistake_feedback(
                    wrong_answer=mistake.get("wrong_answer", ""),
                    correct_answer=mistake.get("correct_answer", ""),
                    context=mistake.get("context", "sentence")
                )
                mistake["ai_feedback"] = feedback
            except Exception as e:
                print(f"❌ Mistake feedback error for {mistake.get('mistake_id')}: {e}")
                # Fallback geri bildirim
                mistake["ai_feedback"] = {
                    "explanation": "Geri bildirim şu anda alınamadı, lütfen daha sonra tekrar deneyin.",
                    "tips": ["Doğru cevabı dikkatlice inceleyerek öğrenmeye devam et"],
                    "example": mistake.get("correct_answer", ""),
                    "practice_sentence": ""
                }
            
            mistakes.append(mistake)
    except Exception as e:
        print(f"❌ Get user mistakes error: {e}")
        import traceback
        traceback.print_exc()

    return render_template("my_mistakes.html", username=username, mistakes=mistakes)


# API: Hata için LLM geri bildirimi al
@app.route("/api/mistake-feedback", methods=["POST"])
def api_mistake_feedback():
    """
    JSON gövdesinden wrong_answer, correct_answer ve context alır.
    LLM'den geri bildirim üretir ve JSON olarak döndürür.
    
    Request örneği:
    {
      "wrong_answer": "I go yesterday",
      "correct_answer": "I went yesterday",
      "context": "sentence"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body"}), 400
        
        wrong_answer = data.get("wrong_answer", "")
        correct_answer = data.get("correct_answer", "")
        context = data.get("context", "sentence")
        
        if not wrong_answer or not correct_answer:
            return jsonify({"error": "Missing required fields"}), 400
        
        # LLM feedback'ini al
        feedback = mistake_feedback(
            wrong_answer=wrong_answer,
            correct_answer=correct_answer,
            context=context
        )
        
        return jsonify({
            "success": True,
            "feedback": feedback
        })
    
    except Exception as e:
        print(f"❌ Mistake feedback API error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# DEBUG: Test LLM feedback
@app.route("/api/test-feedback", methods=["GET"])
def api_test_feedback():
    """Test endpoint - feedback fonksiyonunun çalışıp çalışmadığını kontrol et"""
    try:
        import traceback
        print("\n" + "="*60)
        print("TEST: mistake_feedback fonksiyonu çağrılıyor")
        print("="*60)
        
        test_feedback = mistake_feedback(
            wrong_answer="I go to school yesterday",
            correct_answer="I went to school yesterday",
            context="sentence"
        )
        
        print(f"✅ Feedback başarıyla oluşturuldu: {type(test_feedback)}")
        print(f"Feedback data: {test_feedback}")
        
        return jsonify({
            "success": True,
            "status": "Feedback başarıyla oluşturuldu",
            "feedback": test_feedback,
            "keys": list(test_feedback.keys()) if isinstance(test_feedback, dict) else []
        })
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"❌ Hata: {e}")
        print(error_msg)
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_msg
        }), 500


# API: Ses dosyası al ve STT yap
@app.route("/api/speech-to-text", methods=["POST"])
def api_speech_to_text():
    """Web'den gelen ses dosyasını STT ile metne çevir"""
    if 'audio' not in request.files:
        return jsonify({"error": "Ses dosyası bulunamadı", "text": None})
    
    audio_file = request.files['audio']
    
    if not audio_file or not audio_file.filename:
        return jsonify({"error": "Geçersiz ses dosyası", "text": None})
    
    # speech_stt.py'deki fonksiyonu kullan
    recognized_text = recognize_from_audio_file(audio_file, language="en-US")
    
    if recognized_text.startswith("❌"):
        return jsonify({"error": recognized_text, "text": None})
    
    return jsonify({"error": None, "text": recognized_text})


#-------LOGOUT-----------#
@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    session_id = session.get("session_id")
    
    # Oturumu sonlandır ve loglama yap
    if user_id:
        logger.log_user_action(
            user_id=user_id,
            action_type='logout',
            action_details='Kullanıcı çıkış yaptı',
            page='logout',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
    
    # Oturum bitiş saati kaydı
    if session_id:
        logger.log_session_end(session_id)
    
    session.clear()
    return redirect(url_for("login"))

# ==================== YENİ ROTALAR ====================

#-------İSTATİSTİKLER------#
@app.route("/stats")
def user_stats():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    
    # İstatistikleri al
    daily = stats_manager.get_daily_stats(user_id)
    weekly = stats_manager.get_weekly_stats(user_id)
    overall = stats_manager.get_overall_stats(user_id)
    word_perf = stats_manager.get_word_stats(user_id)
    
    # Raporlar
    weekly_report = stats_manager.generate_weekly_report(user_id)
    
    return render_template(
        "stats.html",
        username=username,
        daily=daily,
        weekly=weekly,
        overall=overall,
        word_perf=word_perf,
        weekly_report=weekly_report
    )

#-------HEDEFLER------#
@app.route("/goals", methods=["GET", "POST"])
def goals():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    
    if request.method == "POST":
        # Yeni hedef oluştur
        goal_type = request.form.get("goal_type")
        target_value = float(request.form.get("target_value", 0))
        deadline = request.form.get("deadline")
        title = request.form.get("title")
        description = request.form.get("description")
        
        goal_id = goal_manager.create_goal(
            user_id=user_id,
            goal_type=goal_type,
            target_value=target_value,
            deadline=deadline,
            title=title,
            description=description
        )
        
        if goal_id > 0:
            # Bildirim gönder
            notification_manager.create_notification(
                user_id=user_id,
                notification_type='goal_created',
                title='Yeni Hedef Oluşturuldu',
                message=f'"{title}" hedefini oluşturdun!',
                icon='🎯'
            )
    
    # Tüm hedefleri al
    all_goals = goal_manager.get_all_goals(user_id)
    suggestions = goal_manager.get_goal_suggestions(user_id)
    
    return render_template(
        "goals.html",
        username=username,
        active_goals=all_goals['active'],
        completed_goals=all_goals['completed'],
        suggestions=suggestions
    )

@app.route("/delete-goal/<int:goal_id>", methods=["POST"])
def delete_goal(goal_id):
    """Hedefi sil."""
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    
    success = goal_manager.delete_goal(goal_id, user_id)
    
    if success:
        flash("Hedef başarıyla silindi.", "success")
    else:
        flash("Hedef silinirken hata oluştu.", "danger")
    
    return redirect(url_for("goals"))

#-------SİRALAMALAR------#
@app.route("/leaderboard")
def leaderboard():
    username = session.get("username")
    user_id = session.get("user_id")
    
    # Periyod parametresi al
    period = request.args.get("period", "all")
    
    if period == "weekly":
        leaderboard_data = leaderboard_manager.get_weekly_leaderboard(limit=50)
    elif period == "monthly":
        leaderboard_data = leaderboard_manager.get_monthly_leaderboard(limit=50)
    else:
        leaderboard_data = leaderboard_manager.get_global_leaderboard(limit=50)
    
    # Kullanıcının sırası
    user_rank = None
    if user_id:
        user_rank = leaderboard_manager.get_user_rank(user_id, period)
    
    # Arkadaş sıralaması
    friends_leaderboard = None
    if user_id:
        friends_leaderboard = leaderboard_manager.get_friends_leaderboard(user_id)
    
    return render_template(
        "leaderboard.html",
        username=username,
        leaderboard=leaderboard_data,
        user_rank=user_rank,
        friends_leaderboard=friends_leaderboard,
        period=period
    )

#-------BİLDİRİMLER------#
@app.route("/notifications")
def notifications():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    
    # Bildirimleri al
    notif_list = notification_manager.get_user_notifications(user_id, limit=50)
    unread_count = notification_manager.get_unread_notification_count(user_id)
    
    # DEBUG
    print(f"[DEBUG] user_id: {user_id}, notifications count: {len(notif_list)}, unread: {unread_count}")
    print(f"[DEBUG] notifications: {notif_list}")
    
    return render_template(
        "notifications.html",
        username=username,
        notifications=notif_list,
        unread_count=unread_count
    )

@app.route("/notification/<int:notification_id>/read", methods=["POST"])
def mark_notification_read(notification_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    
    notification_manager.mark_as_read(notification_id)
    
    return redirect(request.referrer or url_for("notifications"))

#-------SOSYAL------#
@app.route("/profile/<int:user_id>")
def user_profile(user_id):
    username = session.get("username")
    current_user_id = session.get("user_id")
    
    # Profil bilgileri
    profile = social_manager.get_user_profile(user_id)
    
    # Eğer kendi profiliniyse daha fazla bilgi göster
    is_own_profile = (current_user_id == user_id)
    
    return render_template(
        "profile.html",
        username=username,
        profile=profile,
        is_own_profile=is_own_profile
    )

@app.route("/friends")
def friends():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    
    # Arkadaş listeleri
    friends_list = social_manager.get_friends(user_id)
    friend_requests = social_manager.get_friend_requests(user_id)
    
    # Aktivite akışı
    activity_feed = social_manager.get_friend_activity_feed(user_id)
    
    return render_template(
        "friends.html",
        username=username,
        friends=friends_list,
        friend_requests=friend_requests,
        activity_feed=activity_feed
    )

@app.route("/add-friend/<int:friend_id>", methods=["POST"])
def add_friend(friend_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    
    # JSON isteği kontrol et
    if request.is_json:
        result = social_manager.add_friend(user_id, friend_id)
        return jsonify(result)
    else:
        # Form isteği
        result = social_manager.add_friend(user_id, friend_id)
        
        # Sonucu session'a kaydet
        if result.get('success'):
            flash(result.get('message', 'Arkadaş isteği gönderildi!'), 'success')
        else:
            flash(result.get('message', 'Arkadaş eklenemedi!'), 'error')
        
        return redirect(request.referrer or url_for("friends"))

@app.route("/friend-request/<int:friendship_id>/confirm", methods=["POST"])
def confirm_friend_request(friendship_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    
    social_manager.confirm_friend_request(friendship_id)
    
    return redirect(url_for("friends"))

# ==================== KURS ROTALAR ====================

#-------KURSLAR------#
@app.route("/courses")
def courses():
    """Tüm kursları ve kurslardaki ilerlemeyi göster"""
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    
    # Kullanıcının aktif kurslarını al
    active_courses = course_manager.get_user_courses(user_id, status="active")
    completed_courses = course_manager.get_user_courses(user_id, status="completed")
    
    return render_template(
        "courses.html",
        username=username,
        active_courses=active_courses,
        completed_courses=completed_courses
    )

#-------KURS DETAYI VE ÜNİTELER------#
@app.route("/course/<int:course_id>")
def course_detail(course_id):
    """Kurs detaylarını ve ünitelerini göster"""
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    
    # Kursun üniteleri
    units = course_manager.get_course_units(course_id)
    
    # Kurs istatistikleri
    stats = course_manager.get_course_stats(course_id)
    
    return render_template(
        "course_detail.html",
        username=username,
        course_id=course_id,
        course_name=stats.get('course_name', 'Kurs'),
        units=units,
        stats=stats
    )

#-------ÜNİTE ÇALIŞMA SAYFASI------#
@app.route("/unit/<int:unit_id>")
def unit_study(unit_id):
    """Ünite çalışma sayfası"""
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Ünite bilgileri al
    cursor.execute("""
        SELECT unit_id, title, description, level, progress, completed, started_at
        FROM units
        WHERE unit_id = ?
    """, (unit_id,))
    
    unit = cursor.fetchone()
    conn.close()
    
    if not unit:
        return redirect(url_for("courses"))
    
    # Üniteyi başlat
    course_manager.start_unit(unit_id)
    
    # Ünite kaynaklarını al
    resources_vocab = course_manager.get_unit_resources(unit_id, "vocabulary")
    resources_grammar = course_manager.get_unit_resources(unit_id, "grammar")
    resources_sentences = course_manager.get_unit_resources(unit_id, "sentence")
    
    return render_template(
        "unit_study.html",
        username=username,
        unit_id=unit_id,
        unit_title=unit[1],
        unit_description=unit[2],
        level=unit[3],
        progress=unit[4],
        is_completed=bool(unit[5]),
        resources_vocab=resources_vocab,
        resources_grammar=resources_grammar,
        resources_sentences=resources_sentences
    )

#-------YENİ KURS OLUŞTUR------#
@app.route("/course/create", methods=["GET", "POST"])
def create_course():
    """Yeni kurs oluştur (standart veya özel)"""
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    
    if request.method == "POST":
        course_type = request.form.get("course_type")  # "standard" veya "custom"
        course_name = request.form.get("course_name")
        description = request.form.get("description", "")
        
        if course_type == "standard":
            # Standart 20 ünite kursu oluştur
            course_id = course_manager.create_course(
                user_id=user_id,
                course_name=course_name or "İngilizce Başlangıç",
                course_type="standard",
                description=description or "20 ünite ile kapsamlı İngilizce öğrenme"
            )
        
        elif course_type == "custom":
            # Özel konulardan kurs oluştur
            topics_str = request.form.get("topics", "")
            topics_list = [t.strip() for t in topics_str.split(",") if t.strip()]
            
            course_id = course_manager.create_custom_course_from_topics(
                user_id=user_id,
                topics_list=topics_list,
                course_name=course_name
            )
        
        else:
            return redirect(url_for("courses"))
        
        if course_id > 0:
            # Başarı bildirimi
            notification_manager.create_notification(
                user_id=user_id,
                notification_type='course_created',
                title='Kurs Oluşturuldu',
                message=f'"{course_name}" kursunuzu başladınız!',
                icon='📚'
            )
            return redirect(url_for("course_detail", course_id=course_id))
    
    # GET isteğinde form göster
    available_topics = course_manager.get_available_topics()
    
    return render_template(
        "create_course.html",
        username=username,
        available_topics=available_topics
    )

#-------ÜNİTE İLERLEME GÜNCELLE (API)------#
@app.route("/api/unit/<int:unit_id>/progress", methods=["POST"])
def api_update_unit_progress(unit_id):
    """Ünite ilerleme yüzdesini güncelle"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    progress = data.get("progress", 0)
    
    success = course_manager.update_unit_progress(unit_id, progress)
    
    if success:
        return jsonify({"success": True, "progress": progress})
    else:
        return jsonify({"success": False, "error": "İlerleme güncellenemedi"}), 400

#-------KURS İSTATİSTİKLERİ (API)------#
@app.route("/api/course/<int:course_id>/stats", methods=["GET"])
def api_course_stats(course_id):
    """Kurs istatistiklerini al"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    stats = course_manager.get_course_stats(course_id)
    
    if stats:
        return jsonify(stats)
    else:
        return jsonify({"error": "Kurs bulunamadı"}), 404

#-------KURS SİLME------#
@app.route("/course/<int:course_id>/delete", methods=["POST"])
def delete_course(course_id):
    """Kursu sil"""
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Kursun kullanıcıya ait olduğunu kontrol et
        cursor.execute("""
            SELECT user_id FROM courses WHERE course_id = ?
        """, (course_id,))
        
        row = cursor.fetchone()
        if row and row[0] == user_id:
            # Kursun ünitelerini sil
            cursor.execute("""
                DELETE FROM units WHERE course_id = ?
            """, (course_id,))
            
            # Kursu sil
            cursor.execute("""
                DELETE FROM courses WHERE course_id = ?
            """, (course_id,))
            
            conn.commit()
            print(f"✓ Kurs silindi [ID: {course_id}]")
        
        conn.close()
    
    except Exception as e:
        print(f"❌ Kurs silme hatası: {e}")
    
    return redirect(url_for("courses"))


# ==================== KİŞİSEL GERİ BİLDİRİM ====================
@app.route("/feedback", methods=["GET", "POST"])
def personal_feedback():
    """Kişisel geri bildirim sayfası - AI ile analiz (istek üzerine)"""
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    user_id = get_user_id(username)
    feedback = None
    
    # Kullanıcı istatistiklerini al
    overall = stats_manager.get_overall_stats(user_id)
    word_stats = stats_manager.get_word_stats(user_id)
    
    # Zayıf kelimeleri bul
    weak_words = []
    if word_stats.get('weak_words'):
        weak_words = [w['english'] for w in word_stats['weak_words'][:5]]
    
    # Sadece POST isteğinde AI'dan geri bildirim al (limit aşımını önlemek için)
    if request.method == "POST":
        # AI için stats hazırla
        user_stats = {
            "correct_word_ratio": overall.get('accuracy_percent', 0) / 100,
            "pronunciation_avg": overall.get('pronunciation_avg', 0),
            "weak_words": weak_words
        }
        
        try:
            feedback = personalized_feedback(user_stats)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                feedback = "⏳ API limit aşıldı. Lütfen 30 saniye bekleyip tekrar deneyin."
            else:
                feedback = "AI geri bildirimi şu an alınamıyor. Lütfen daha sonra tekrar deneyin."
            print(f"❌ Feedback hatası: {e}")
    
    return render_template("feedback.html", 
                          username=username,
                          feedback=feedback,
                          stats=overall,
                          weak_words=weak_words)


# ==================== ÖZEL DERS OLUŞTURMA (AI) ====================
@app.route("/custom-lesson", methods=["GET", "POST"])
def custom_lesson():
    """AI ile özel ders oluşturma"""
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    lesson_content = None
    topic = None
    level = "A1-A2"
    error_message = None
    
    if request.method == "POST":
        topic = request.form.get("topic", "").strip()
        level = request.form.get("level", "A1-A2")
        
        if topic:
            try:
                # AI'dan özel ders içeriği al
                lesson_content = generate_custom_lesson(topic, level)
                print(f"✓ Özel ders oluşturuldu: {topic}")
                
                # Loglama
                user_id = get_user_id(username)
                logger.log_user_action(
                    user_id=user_id,
                    action_type='custom_lesson',
                    action_details=f'Konu: {topic}, Seviye: {level}',
                    page='custom_lesson'
                )
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    error_message = "⏳ API limit aşıldı. Lütfen 30 saniye bekleyip tekrar deneyin."
                elif "API" in error_str or "key" in error_str.lower():
                    error_message = "🔑 API bağlantı hatası. Lütfen daha sonra tekrar deneyin."
                else:
                    error_message = f"Ders oluşturulurken hata: {error_str}"
                print(f"❌ Özel ders hatası: {e}")
    
    return render_template("custom_lesson.html",
                          username=username,
                          topic=topic,
                          level=level,
                          lesson_content=lesson_content,
                          error_message=error_message)


# ==================== SEVİYE BELİRLEME TESTİ ====================

@app.route("/placement-test")
def placement_test():
    """Seviye belirleme testi sayfasi - kapsamli test."""
    if "username" not in session:
        return redirect(url_for("login"))
    
    username = session["username"]
    user_id = get_user_id(username)
    
    # Kullanıcı zaten testi yapmışsa, direkt learn sayfasına yönlendir
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT placement_test_done FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0] == 1:
        return redirect(url_for("learn"))
    
    import random
    
    # Her seviyeden farkli soru tipleri olustur
    questions = []
    levels = ['A1', 'A2', 'B1', 'B2']
    question_types = ['vocabulary', 'listening', 'translation', 'grammar', 'pronunciation']
    
    for level in levels:
        # Her seviyeden farkli tiplerden sorular
        for i, q_type in enumerate(question_types):
            try:
                # Her tipten 1 soru (pronunciation dahil)
                count = 1
                level_questions = course_system._generate_questions(q_type, level, count)
                for q in level_questions:
                    q['level'] = level
                questions.extend(level_questions)
            except Exception as e:
                print(f"Soru olusturma hatasi ({level}, {q_type}): {e}")
    
    # Soruları seviye sirasina gore grupla
    grouped = {}
    for q in questions:
        level = q.get('level', 'A1')
        if level not in grouped:
            grouped[level] = []
        grouped[level].append(q)
    
    # Her grubu kendi icinde karistir ve sirala
    final_questions = []
    for level in levels:
        if level in grouped:
            random.shuffle(grouped[level])
            final_questions.extend(grouped[level])
    
    return render_template("placement_test.html", 
                          username=username,
                          questions=final_questions)


@app.route("/placement-test/save", methods=["POST"])
def save_placement_result():
    """Seviye belirleme sonucunu kaydet."""
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    username = session["username"]
    user_id = get_user_id(username)
    
    data = request.get_json()
    level = data.get("level", "A1")
    
    # Geçerli seviye kontrolü
    if level not in ['A1', 'A2', 'B1', 'B2']:
        level = 'A1'
    
    # Kullanıcı seviyesini ve placement_test_done'u güncelle
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET level = ?, placement_test_done = 1 
        WHERE user_id = ?
    """, (level, user_id))
    conn.commit()
    conn.close()
    
    # Kurs ilerlemesini belirlenen seviyeden başlat
    course_system.init_user_progress(user_id, level)
    
    return jsonify({"success": True, "level": level})


# ==================== YENİ KURS SİSTEMİ ====================

@app.route("/learn")
def learn():
    """Ana kurs haritası sayfası (Duolingo tarzı)."""
    if "username" not in session:
        return redirect(url_for("login"))
    
    username = session["username"]
    user_id = get_user_id(username)
    
    # Placement test yapılmış mı kontrol et
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT placement_test_done FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    # Eğer placement test yapılmamışsa, teste yönlendir
    if not row or not row[0]:
        return redirect(url_for("placement_test"))
    
    # Kurs haritasını al
    course_map = course_system.get_user_course_map(user_id)
    
    return render_template("learn.html",
                          username=username,
                          course_map=course_map)


@app.route("/learn/lesson/<int:lesson_id>")
def learn_lesson(lesson_id):
    """Ders sayfası."""
    if "username" not in session:
        return redirect(url_for("login"))
    
    username = session["username"]
    user_id = get_user_id(username)
    
    # Dersin açık olup olmadığını kontrol et
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status FROM user_course_progress 
        WHERE user_id = ? AND lesson_id = ?
    """, (user_id, lesson_id))
    progress = cursor.fetchone()
    conn.close()
    
    if not progress or progress[0] == 'locked':
        return redirect(url_for("learn"))
    
    # Ders bilgilerini al
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.lesson_id, l.lesson_type, l.title, l.xp_reward, u.title as unit_title, u.level_code
        FROM course_lessons l
        JOIN course_units u ON l.unit_id = u.unit_id
        WHERE l.lesson_id = ?
    """, (lesson_id,))
    lesson_info = cursor.fetchone()
    conn.close()
    
    if not lesson_info:
        return redirect(url_for("learn"))
    
    # Soruları al
    questions = course_system.get_lesson_questions(lesson_id, user_id)
    
    return render_template("learn_lesson.html",
                          username=username,
                          lesson={
                              "id": lesson_info[0],
                              "type": lesson_info[1],
                              "title": lesson_info[2],
                              "xp": lesson_info[3],
                              "unit_title": lesson_info[4],
                              "level": lesson_info[5]
                          },
                          questions=questions)


@app.route("/api/learn/complete-lesson", methods=["POST"])
def api_complete_lesson():
    """Ders tamamlama API."""
    if "username" not in session:
        return jsonify({"success": False, "error": "Giriş yapmalısınız"})
    
    user_id = get_user_id(session["username"])
    data = request.get_json()
    
    lesson_id = data.get("lesson_id")
    score = data.get("score", 0)
    
    if not lesson_id:
        return jsonify({"success": False, "error": "Ders ID gerekli"})
    
    result = course_system.complete_lesson(user_id, lesson_id, score)
    return jsonify(result)


@app.route("/api/learn/record-mistake", methods=["POST"])
def api_record_lesson_mistake():
    """Ders sırasında yapılan hatayı kaydet."""
    if "username" not in session:
        return jsonify({"success": False, "error": "Giriş yapmalısınız"})
    
    user_id = get_user_id(session["username"])
    data = request.get_json()
    
    item_key = data.get("item_key", "")  # Soru/kelime
    wrong_answer = data.get("wrong_answer", "")
    correct_answer = data.get("correct_answer", "")
    lesson_id = data.get("lesson_id", "learn")
    context = data.get("context", "lesson")  # lesson, vocabulary, grammar, listening
    
    if not item_key or not correct_answer:
        return jsonify({"success": False, "error": "Eksik bilgi"})
    
    try:
        mistake_id = record_mistake(
            user_id=user_id,
            item_key=item_key,
            wrong_answer=wrong_answer,
            correct_answer=correct_answer,
            lesson_id=str(lesson_id),
            context=context
        )
        return jsonify({"success": True, "mistake_id": mistake_id})
    except Exception as e:
        print(f"❌ Hata kaydetme hatası: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/learn/course-map")
def api_course_map():
    """Kurs haritası API."""
    if "username" not in session:
        return jsonify({"error": "Giriş yapmalısınız"})
    
    user_id = get_user_id(session["username"])
    course_map = course_system.get_user_course_map(user_id)
    return jsonify(course_map)


@app.route("/api/check-grammar", methods=["POST"])
def api_check_grammar():
    """Kullanıcının yazdığı cümleyi LLM ile kontrol et."""
    if "username" not in session:
        return jsonify({"error": "Giriş yapmalısınız"}), 401
    
    data = request.get_json()
    sentence = data.get("sentence", "").strip()
    target_word = data.get("target_word", "").strip()
    
    if not sentence:
        return jsonify({"error": "Cümle boş olamaz"}), 400
    
    try:
        # LLM ile gramer kontrolü yap
        result = grammar_feedback_json(sentence)
        
        # Hedef kelime cümlede var mı kontrol et
        word_used = target_word.lower() in sentence.lower() if target_word else True
        
        # Sonucu döndür
        return jsonify({
            "success": True,
            "corrected": result.get("corrected", sentence),
            "mistakes": result.get("mistakes", []),
            "word_used": word_used,
            "is_correct": len(result.get("mistakes", [])) == 0 and word_used
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
if __name__ == "__main__":
    app.run(debug=True)

