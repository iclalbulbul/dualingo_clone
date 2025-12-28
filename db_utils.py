"""
db_utils.py

SQLite tabanlı temel şema ve yardımcı seed fonksiyonları.

Bu dosya şunları yapar:
- `init_db()` : gerekli tabloları oluşturur
- `seed_topics_from_repo()` : `database_icin_kelime/data` içindeki .txt dosyalarını okuyup `topics` tablosuna ekler

NOT: Büyük kelime importları ayrı bir importer script'i ile yapılmalı (chunking önerilir).
"""

import os
import sqlite3
from typing import List
import threading
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

# Thread-safe bağlantı için lock
_db_lock = threading.Lock()


def _connect():
	conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
	# WAL mode - daha iyi eşzamanlılık için
	conn.execute("PRAGMA journal_mode=WAL")
	conn.execute("PRAGMA busy_timeout=30000")
	return conn


def init_db():
	"""Veritabanı ve tabloları oluşturur."""
	conn = _connect()
	cur = conn.cursor()

	# users
	cur.execute("""
	CREATE TABLE IF NOT EXISTS users (
		user_id INTEGER PRIMARY KEY AUTOINCREMENT,
		username TEXT UNIQUE NOT NULL,
		level TEXT DEFAULT 'A1',
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		last_login TIMESTAMP
	)
	""")

	# topics
	cur.execute("""
	CREATE TABLE IF NOT EXISTS topics (
		topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
		topic_name TEXT UNIQUE NOT NULL,
		description TEXT,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	)
	""")

	# words
	cur.execute("""
	CREATE TABLE IF NOT EXISTS words (
		word_id INTEGER PRIMARY KEY AUTOINCREMENT,
		english TEXT NOT NULL,
		turkish TEXT,
		level TEXT,
		topic_id INTEGER,
		example_sentence TEXT,
		pronunciation TEXT,
		pos TEXT,
		freq REAL,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
	)
	""")

	# grammar_rules
	cur.execute("""
	CREATE TABLE IF NOT EXISTS grammar_rules (
		rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
		rule_key TEXT UNIQUE NOT NULL,
		title_tr TEXT,
		description_tr TEXT,
		description_en TEXT,
		level TEXT,
		example_correct TEXT,
		example_incorrect TEXT,
		explanation_tr TEXT,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	)
	""")

	# practice_history
	cur.execute("""
	CREATE TABLE IF NOT EXISTS practice_history (
		history_id INTEGER PRIMARY KEY AUTOINCREMENT,
		user_id INTEGER NOT NULL,
		practice_type TEXT NOT NULL,
		score REAL,
		timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES users(user_id)
	)
	""")

	# grammar_errors
	cur.execute("""
	CREATE TABLE IF NOT EXISTS grammar_errors (
		error_id INTEGER PRIMARY KEY AUTOINCREMENT,
		user_id INTEGER NOT NULL,
		sentence TEXT NOT NULL,
		error_type TEXT NOT NULL,
		error_message TEXT,
		suggestion TEXT,
		score REAL,
		timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES users(user_id)
	)
	""")

	# test_results
	cur.execute("""
	CREATE TABLE IF NOT EXISTS test_results (
		result_id INTEGER PRIMARY KEY AUTOINCREMENT,
		user_id INTEGER NOT NULL,
		test_type TEXT NOT NULL,
		level TEXT,
		topic_id INTEGER,
		score REAL,
		total_questions INTEGER,
		correct_answers INTEGER,
		timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES users(user_id),
		FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
	)
	""")

	# user_inputs - Tüm kullanıcı girişlerini kaydı (kelime, cümle, telaffuz vb.)
	cur.execute("""
	CREATE TABLE IF NOT EXISTS user_inputs (
		input_id INTEGER PRIMARY KEY AUTOINCREMENT,
		user_id INTEGER NOT NULL,
		input_type TEXT NOT NULL,
		input_text TEXT NOT NULL,
		response_text TEXT,
		is_correct BOOLEAN,
		score REAL,
		word_id INTEGER,
		sentence_id INTEGER,
		timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		metadata TEXT,
		FOREIGN KEY (user_id) REFERENCES users(user_id),
		FOREIGN KEY (word_id) REFERENCES words(word_id)
	)
	""")

	# mistakes - Kullanıcının yaptığı hataların kaydı ve SRS alanları
	cur.execute("""
CREATE TABLE IF NOT EXISTS mistakes (
    mistake_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_key TEXT NOT NULL,
    lesson_id TEXT,
    context TEXT,
    wrong_answer TEXT,
    correct_answer TEXT,
    count INTEGER DEFAULT 1,
    repetition INTEGER DEFAULT 0,
    interval INTEGER DEFAULT 0,
    easiness REAL DEFAULT 2.5,
    next_review TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")

	cur.execute("""
CREATE INDEX IF NOT EXISTS idx_mistakes_user_next ON mistakes (user_id, next_review)
""")

	# user_actions - Kullanıcı aksiyonlarını kaydı (sayfa ziyareti, buton tıklama vb.)
	cur.execute("""
	CREATE TABLE IF NOT EXISTS user_actions (
		action_id INTEGER PRIMARY KEY AUTOINCREMENT,
		user_id INTEGER NOT NULL,
		action_type TEXT NOT NULL,
		action_details TEXT,
		page TEXT,
		ip_address TEXT,
		user_agent TEXT,
		timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES users(user_id)
	)
	""")

	# session_logs - Kullanıcı oturumu kayıtları
	cur.execute("""
	CREATE TABLE IF NOT EXISTS session_logs (
		session_id INTEGER PRIMARY KEY AUTOINCREMENT,
		user_id INTEGER NOT NULL,
		login_time TIMESTAMP,
		logout_time TIMESTAMP,
		session_duration_minutes INTEGER,
		ip_address TEXT,
		device_info TEXT,
		timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES users(user_id)
	)
	""")

	# pronunciation_attempts - Telaffuz denemelerini kaydı
	cur.execute("""
	CREATE TABLE IF NOT EXISTS pronunciation_attempts (
		attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
		user_id INTEGER NOT NULL,
		word_id INTEGER NOT NULL,
		target_word TEXT NOT NULL,
		audio_file TEXT,
		score REAL,
		accuracy REAL,
		feedback TEXT,
		timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES users(user_id),
		FOREIGN KEY (word_id) REFERENCES words(word_id)
	)
	""")

	# translation_log - Çeviri denemelerini kaydı
	cur.execute("""
	CREATE TABLE IF NOT EXISTS translation_log (
		translation_id INTEGER PRIMARY KEY AUTOINCREMENT,
		user_id INTEGER NOT NULL,
		english_word TEXT NOT NULL,
		turkish_translation TEXT,
		correct_translation TEXT,
		similarity_score REAL,
		is_correct BOOLEAN,
		attempt_number INTEGER,
		word_id INTEGER,
		timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES users(user_id),
		FOREIGN KEY (word_id) REFERENCES words(word_id)
	)
	""")

	# friends - Arkadaşlık ilişkileri
	cur.execute("""
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

	# study_groups - Çalışma grupları
	cur.execute("""
	CREATE TABLE IF NOT EXISTS study_groups (
		group_id INTEGER PRIMARY KEY AUTOINCREMENT,
		group_name TEXT NOT NULL,
		description TEXT,
		created_by INTEGER NOT NULL,
		max_members INTEGER DEFAULT 20,
		is_private BOOLEAN DEFAULT 0,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (created_by) REFERENCES users(user_id)
	)
	""")

	# group_members - Grup üyeleri
	cur.execute("""
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

	# shares - Paylaşımlar
	cur.execute("""
	CREATE TABLE IF NOT EXISTS shares (
		share_id INTEGER PRIMARY KEY AUTOINCREMENT,
		user_id INTEGER NOT NULL,
		share_type TEXT NOT NULL,
		content TEXT NOT NULL,
		privacy TEXT DEFAULT 'friends',
		likes_count INTEGER DEFAULT 0,
		comments_count INTEGER DEFAULT 0,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES users(user_id)
	)
	""")

	# notifications - Bildirimler
	cur.execute("""
	CREATE TABLE IF NOT EXISTS notifications (
		notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
		user_id INTEGER NOT NULL,
		notification_type TEXT NOT NULL,
		title TEXT NOT NULL,
		message TEXT,
		icon TEXT,
		action_url TEXT,
		is_read BOOLEAN DEFAULT 0,
		metadata TEXT,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES users(user_id)
	)
	""")

	# goals - Kullanıcı hedefleri
	cur.execute("""
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

	# milestones - Hedef aşamaları
	cur.execute("""
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

	conn.commit()
	conn.close()
	print("✓ SQLite DB hazır: " + DB_PATH)


def seed_topics_from_repo(repo_data_dir: str = None) -> int:
	"""
	`database_icin_kelime/data` içindeki .txt dosyalarını topics olarak ekler.
	Dönen değer eklenen topic sayısıdır.
	"""
	if repo_data_dir is None:
		repo_data_dir = os.path.join(os.path.dirname(__file__), "database_icin_kelime", "data")

	if not os.path.isdir(repo_data_dir):
		print("Uyarı: repo data dizini bulunamadı:", repo_data_dir)
		return 0

	files = [f for f in os.listdir(repo_data_dir) if f.endswith('.txt')]
	conn = _connect()
	cur = conn.cursor()
	added = 0
	for fname in files:
		topic_name = os.path.splitext(fname)[0].replace('_', ' ').title()
		try:
			cur.execute("INSERT OR IGNORE INTO topics (topic_name) VALUES (?)", (topic_name,))
			if cur.rowcount:
				added += 1
		except Exception:
			pass

	conn.commit()
	conn.close()
	print(f"✓ {added} topic eklendi (kaynak: {repo_data_dir})")
	return added


def get_db_connection():
	"""Veritabanı bağlantısı döndür."""
	conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
	conn.execute("PRAGMA journal_mode=WAL")
	conn.execute("PRAGMA busy_timeout=30000")
	conn.row_factory = sqlite3.Row
	return conn


def get_user_id(username: str):
	"""Kullanıcı adından user_id döndür."""
	conn = get_db_connection()
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
	row = cursor.fetchone()
	conn.close()
	return row[0] if row else None


def create_or_get_user(username: str) -> int:
	"""Kullanıcı varsa ID'sini döndür, yoksa oluştur."""
	conn = get_db_connection()
	cursor = conn.cursor()
	
	cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
	row = cursor.fetchone()
	
	if row:
		user_id = row[0]
	else:
		cursor.execute("INSERT INTO users (username, level) VALUES (?, ?)", (username, 'A1'))
		user_id = cursor.lastrowid
	
	conn.commit()
	conn.close()
	return user_id


def record_mistake(user_id: int, item_key: str, wrong_answer: str, correct_answer: str, lesson_id: str = None, context: str = None):
	"""Kullanıcının bir hatasını kaydeder veya mevcut kaydı günceller.
	Varsa `count` arttırılır, yoksa yeni satır eklenir.
	Döner: `mistake_id`.
	"""
	conn = get_db_connection()
	cur = conn.cursor()
	cur.execute("SELECT mistake_id FROM mistakes WHERE user_id = ? AND item_key = ?", (user_id, item_key))
	row = cur.fetchone()
	now = datetime.utcnow().isoformat(sep=' ')
	if row:
		mistake_id = row[0]
		cur.execute(
			"""UPDATE mistakes SET count = count + 1, wrong_answer = ?, correct_answer = ?, last_seen = ?, lesson_id = ?, context = ? WHERE mistake_id = ?""",
			(wrong_answer, correct_answer, now, lesson_id, context, mistake_id)
		)
	else:
		cur.execute(
			"""INSERT INTO mistakes (user_id, item_key, lesson_id, context, wrong_answer, correct_answer, last_seen, created_at, next_review)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
			(user_id, item_key, lesson_id, context, wrong_answer, correct_answer, now, now, now)
		)
		mistake_id = cur.lastrowid

	conn.commit()
	conn.close()
	return mistake_id


def get_due_mistakes(user_id: int, limit: int = 20) -> List[dict]:
	"""`next_review` zamanı gelen veya `NULL` olan hataları döndürür (öncelik: next_review, sonra count).
	Dönen liste dict satırlardan oluşur.
	"""
	conn = get_db_connection()
	cur = conn.cursor()
	now = datetime.utcnow().isoformat(sep=' ')
	cur.execute(
		"""SELECT * FROM mistakes WHERE user_id = ? AND (next_review IS NULL OR next_review <= ?) ORDER BY next_review ASC, count DESC LIMIT ?""",
		(user_id, now, limit)
	)
	rows = cur.fetchall()
	conn.close()
	return [dict(r) for r in rows]


def update_review_result(user_id: int, item_key: str, quality: int):
	"""SM-2 mantığıyla bir tekrar sonucunu uygular.
	`quality` 0-5 arası (>=3 geçer), fonksiyon yeni SRS alanlarını döndürür.
	"""
	if quality < 0:
		quality = 0
	if quality > 5:
		quality = 5

	conn = get_db_connection()
	cur = conn.cursor()
	cur.execute("SELECT mistake_id, repetition, interval, easiness FROM mistakes WHERE user_id = ? AND item_key = ?", (user_id, item_key))
	row = cur.fetchone()
	if not row:
		conn.close()
		return None

	mistake_id = row[0]
	repetition = row[1] or 0
	interval = row[2] or 0
	easiness = row[3] or 2.5

	if quality < 3:
		repetition = 0
		interval = 1
	else:
		if repetition == 0:
			interval = 1
		elif repetition == 1:
			interval = 6
		else:
			interval = max(1, round(interval * easiness))
		repetition += 1

	# easiness güncellemesi (SM-2 formülü)
	new_easiness = easiness + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
	if new_easiness < 1.3:
		new_easiness = 1.3

	next_review_dt = datetime.utcnow() + timedelta(days=interval)
	next_review = next_review_dt.isoformat(sep=' ')
	now = datetime.utcnow().isoformat(sep=' ')

	cur.execute(
		"""UPDATE mistakes SET repetition = ?, interval = ?, easiness = ?, next_review = ?, last_seen = ? WHERE mistake_id = ?""",
		(repetition, interval, new_easiness, next_review, now, mistake_id)
	)

	conn.commit()
	conn.close()
	return {
		"mistake_id": mistake_id,
		"repetition": repetition,
		"interval": interval,
		"easiness": new_easiness,
		"next_review": next_review,
	}


if __name__ == "__main__":
	init_db()
	# Sadece topic satırlarını ekleyelim; kelime importları ayrı script ile yapılmalı
	seed_topics_from_repo()

