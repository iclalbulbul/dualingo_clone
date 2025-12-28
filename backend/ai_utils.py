"""
AI Utilities

Bu modül:
- Kelime çevirisi
- Cümle üretimi
- Gramer kontrolü
- Kişiselleştirilmiş geri bildirim
- Kullanıcı yönlendirmeli ders üretimi

işlemlerini LLM kullanarak gerçekleştirir.
API yoksa dummy modda çalışır.
"""

import os
from dotenv import load_dotenv
import json
import time

from google import genai


load_dotenv()
API_KEY = os.getenv("API_KEY")

model = None
if API_KEY:
    try:
        model = genai.Client(api_key=API_KEY)
    except Exception as e:
        print(f"⚠️ LLM API başlatılamadı: {e}")
else:
    print("⚠️ API_KEY set edilmemiş, dummy modda çalışacak.")


def _llm_chat(prompt: str, system: str = "You are an English teacher.", timeout: int = 10) -> str:
    """
    Tüm LLM çağrıları buradan geçer.
    Eğer API yoksa dummy cevap döner.
    """

    if model is None:
        # Fallback: gerçek LLM yokken JSON döndür
        # Bu sentinel string kullanılarak mistake_feedback'te tanınır
        return "DUMMY_RESPONSE"

    try:
        response = model.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Sistem: {system}\n\nPrompt: {prompt}",
        )
        return response.text
    except Exception as e:
        print(f"❌ LLM API hatası: {e}")
        return "DUMMY_RESPONSE"

def translate_word(word: str) -> str:
    """
    İngilizce kelimeyi Türkçeye çevirir.
    Sadece tek kelimelik cevap bekleriz.
    """
    prompt = f'Translate this English word into Turkish, just one word, no explanation: "{word}"'
    result = _llm_chat(prompt, system="You are a bilingual English-Turkish dictionary.")

    return result.splitlines()[0]

def generate_sentence(word: str) -> str:
    """
    Verilen kelimeyi A1–A2 seviyesinde basit bir İngilizce cümlede kullanır.
    """
    prompt = f'Use the word "{word}" in a simple A1–A2 level English sentence.'
    result = _llm_chat(prompt, system="You are an English teacher for beginners.")

    # DUMMY_RESPONSE ise fallback örnek cümleler kullan
    if result == "DUMMY_RESPONSE":
        return _generate_fallback_sentence(word)

    return result.splitlines()[0]


def _generate_fallback_sentence(word: str) -> str:
    """
    API olmadığında kelime için basit örnek cümle oluşturur.
    """
    # Önceden hazırlanmış örnek cümleler
    example_sentences = {
        # Yaygın fiiller
        'go': 'I go to school every day.',
        'eat': 'I eat breakfast in the morning.',
        'drink': 'I drink water when I am thirsty.',
        'sleep': 'I sleep eight hours every night.',
        'read': 'I like to read books.',
        'write': 'I write in my notebook.',
        'run': 'I run in the park.',
        'walk': 'I walk to the store.',
        'play': 'I play with my friends.',
        'work': 'I work at an office.',
        'study': 'I study English every day.',
        'learn': 'I want to learn new words.',
        'speak': 'I speak English well.',
        'listen': 'I listen to music.',
        'watch': 'I watch TV in the evening.',
        'make': 'I make breakfast for my family.',
        'take': 'I take the bus to work.',
        'give': 'I give gifts to my friends.',
        'come': 'Please come to my party.',
        'see': 'I see a beautiful flower.',
        'know': 'I know the answer.',
        'think': 'I think this is easy.',
        'want': 'I want to travel.',
        'need': 'I need your help.',
        'like': 'I like chocolate.',
        'love': 'I love my family.',
        'help': 'Can you help me?',
        'ask': 'I ask my teacher a question.',
        'tell': 'Please tell me a story.',
        'say': 'I say hello to everyone.',
        'call': 'I call my mother every week.',
        'try': 'I try to do my best.',
        'use': 'I use my phone every day.',
        'find': 'I find my keys.',
        'put': 'I put my bag on the table.',
        'get': 'I get up early in the morning.',
        'buy': 'I buy vegetables at the market.',
        'open': 'I open the door.',
        'close': 'Please close the window.',
        'start': 'I start work at 9 am.',
        'stop': 'The bus stops here.',
        'wait': 'I wait for my friend.',
        'meet': 'I meet my friends on weekends.',
        'bring': 'Please bring your book.',
        'send': 'I send emails to my colleagues.',
        'leave': 'I leave home at 8 am.',
        'move': 'I move to a new house.',
        'live': 'I live in a big city.',
        'sit': 'I sit on the chair.',
        'stand': 'Please stand up.',
        
        # Yaygın isimler
        'book': 'I have a new book.',
        'water': 'I drink water every day.',
        'food': 'The food is delicious.',
        'house': 'I live in a small house.',
        'school': 'I go to school by bus.',
        'friend': 'My friend is very kind.',
        'family': 'I love my family.',
        'time': 'What time is it?',
        'day': 'Today is a beautiful day.',
        'year': 'This year is special.',
        'money': 'I save money for vacation.',
        'car': 'My father has a car.',
        'city': 'I live in a big city.',
        'name': 'My name is John.',
        'morning': 'I wake up early in the morning.',
        'night': 'I sleep well at night.',
        'phone': 'I use my phone to call friends.',
        'music': 'I listen to music every day.',
        'movie': 'I watch a movie on weekends.',
        'coffee': 'I drink coffee in the morning.',
        'tea': 'Would you like some tea?',
        'apple': 'I eat an apple every day.',
        'cat': 'I have a cute cat.',
        'dog': 'My dog is very friendly.',
        'room': 'My room is clean.',
        'table': 'The book is on the table.',
        'door': 'Please open the door.',
        'window': 'I look out the window.',
        'weather': 'The weather is nice today.',
        'sun': 'The sun is shining.',
        'rain': 'It will rain tomorrow.',
        
        # Yaygın sıfatlar
        'good': 'This is a good idea.',
        'bad': 'The weather is bad today.',
        'big': 'I live in a big house.',
        'small': 'I have a small bag.',
        'new': 'I bought a new phone.',
        'old': 'This is an old book.',
        'happy': 'I am happy today.',
        'sad': 'She feels sad.',
        'easy': 'This lesson is easy.',
        'difficult': 'The test was difficult.',
        'beautiful': 'The flower is beautiful.',
        'important': 'Education is important.',
        'different': 'We have different opinions.',
        'same': 'We wear the same clothes.',
        'fast': 'The car is very fast.',
        'slow': 'The turtle is slow.',
        'hot': 'The summer is hot.',
        'cold': 'The winter is cold.',
        'young': 'The children are young.',
        'tired': 'I am tired after work.',
        
        # Diğer yaygın kelimeler
        'today': 'Today is Monday.',
        'tomorrow': 'I will go shopping tomorrow.',
        'yesterday': 'I met her yesterday.',
        'now': 'I am studying now.',
        'always': 'I always drink coffee.',
        'never': 'I never eat meat.',
        'sometimes': 'I sometimes go to the gym.',
        'here': 'Come here please.',
        'there': 'The park is over there.',
        'home': 'I go home after work.',
        'please': 'Please help me.',
        'thank': 'Thank you very much.',
        'sorry': 'I am sorry for being late.',
        'welcome': 'Welcome to our home.',
        'hello': 'Hello, how are you?',
        'goodbye': 'Goodbye, see you later.',
    }
    
    word_lower = word.lower().strip()
    
    # Kelime listede varsa o cümleyi kullan
    if word_lower in example_sentences:
        return example_sentences[word_lower]
    
    # Kelime tipine göre genel cümle şablonları
    templates = [
        f"I use the word '{word}' in my daily life.",
        f"The teacher explains what '{word}' means.",
        f"Can you tell me about '{word}'?",
        f"I learned the word '{word}' today.",
        f"This is a good example of '{word}'.",
        f"'{word.capitalize()}' is an important word to know.",
    ]
    
    # Rastgele bir şablon seç
    import random
    return random.choice(templates)

def grammar_feedback(sentence: str) -> str:
    """
    Cümlenin gramerini kontrol eder, hataları bulur ve Türkçe kısa açıklama yapar.
    """
    prompt = f"""
    Check the grammar of this English sentence:

    "{sentence}"

    1. First, write the corrected version of the sentence.
    2. Then, in Turkish, briefly explain the grammar mistakes.
    Keep it short and clear.
    """
    result = _llm_chat(prompt, system="You are an English grammar teacher.")
    return result

def grammar_feedback_json(sentence: str) -> dict:
    """
    Cümlenin gramerini kontrol eder, sonucu JSON olarak döndürür.
    Örnek çıktı:
    {
      "corrected": "She went to school yesterday.",
      "mistakes": [
        {
          "part": "go",
          "explanation_tr": "Geçmiş zamanda 'went' kullanılmalı."
        }
      ]
    }
    """
    prompt = f"""
    Check the grammar of this English sentence:

    "{sentence}"

    Return ONLY valid JSON with this structure:
    {{
      "corrected": "<düzeltilmiş cümle>",
      "mistakes": [
         {{"part": "<yanlış kısım>", "explanation_tr": "<Türkçe açıklama>"}}
      ]
    }}
    
    Kurallar:
    - Sadece JSON döndür.
    - Açıklamaları Türkçe yaz.
    
    but not use ```json just text but but json format.
    """
    result = _llm_chat(prompt, system="You are an English grammar teacher.")

    # DUMMY_RESPONSE ise basit gramer kontrolü yap
    if result == "DUMMY_RESPONSE":
        return _simple_grammar_check(sentence)

    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        # LLM düzgün JSON döndüremezse basit kontrol yap
        return _simple_grammar_check(sentence)

    return data


def _simple_grammar_check(sentence: str) -> dict:
    """API olmadan basit gramer kontrolü yapar."""
    mistakes = []
    corrected = sentence
    words = sentence.lower().split()
    
    # Basit gramer kuralları
    grammar_rules = {
        # Subject-Verb agreement
        ('she', 'go'): ('went', "Geçmiş zaman için 'went' kullanılmalı veya 'goes' (şimdiki zaman)."),
        ('he', 'go'): ('went', "Geçmiş zaman için 'went' kullanılmalı veya 'goes' (şimdiki zaman)."),
        ('it', 'go'): ('went', "Geçmiş zaman için 'went' kullanılmalı veya 'goes' (şimdiki zaman)."),
        ('she', 'have'): ('has', "She/He/It ile 'has' kullanılmalı."),
        ('he', 'have'): ('has', "She/He/It ile 'has' kullanılmalı."),
        ('it', 'have'): ('has', "She/He/It ile 'has' kullanılmalı."),
        ('she', 'do'): ('does', "She/He/It ile 'does' kullanılmalı."),
        ('he', 'do'): ('does', "She/He/It ile 'does' kullanılmalı."),
        ('i', 'is'): ('am', "I ile 'am' kullanılmalı."),
        ('you', 'is'): ('are', "You ile 'are' kullanılmalı."),
        ('we', 'is'): ('are', "We ile 'are' kullanılmalı."),
        ('they', 'is'): ('are', "They ile 'are' kullanılmalı."),
    }
    
    # İkili kelime kontrolü
    for i in range(len(words) - 1):
        pair = (words[i], words[i + 1])
        if pair in grammar_rules:
            correction, explanation = grammar_rules[pair]
            mistakes.append({
                "part": words[i + 1],
                "explanation_tr": explanation
            })
            # Düzeltilmiş cümleyi oluştur
            corrected = corrected.replace(f" {words[i + 1]} ", f" {correction} ", 1)
    
    # Yaygın yanlış yazımlar
    common_mistakes = {
        'recieve': ('receive', "'i' harfi 'e' harfinden önce gelir: receive"),
        'definately': ('definitely', "Doğru yazım: definitely"),
        'seperate': ('separate', "Doğru yazım: separate"),
        'occured': ('occurred', "Çift 'r' olmalı: occurred"),
        'untill': ('until', "Tek 'l' olmalı: until"),
        'tommorow': ('tomorrow', "Doğru yazım: tomorrow"),
        'becuase': ('because', "Doğru yazım: because"),
        'wich': ('which', "Doğru yazım: which"),
        'teh': ('the', "Doğru yazım: the"),
    }
    
    for wrong, (correct, explanation) in common_mistakes.items():
        if wrong in sentence.lower():
            mistakes.append({
                "part": wrong,
                "explanation_tr": explanation
            })
            corrected = corrected.lower().replace(wrong, correct)
    
    # Cümle başı büyük harf kontrolü
    if sentence and sentence[0].islower():
        mistakes.append({
            "part": sentence[0],
            "explanation_tr": "Cümle başı büyük harfle başlamalı."
        })
        corrected = corrected[0].upper() + corrected[1:]
    
    # Noktalama kontrolü
    if sentence and sentence[-1] not in '.!?':
        mistakes.append({
            "part": "(noktalama)",
            "explanation_tr": "Cümle sonunda noktalama işareti olmalı (. ! ?)"
        })
        corrected = corrected + "."
    
    return {
        "corrected": corrected,
        "mistakes": mistakes
    }

def personalized_feedback(user_stats: dict) -> str:
    """
    Kullanıcının istatistiklerine göre kısa bir motivasyon + öneri mesajı üretir.
    user_stats örneği:
    {
      "correct_word_ratio": 0.7,
      "pronunciation_avg": 82.5,
      "weak_words": ["apple", "orange"]
    }
    """
    prompt = f"""
    Kullanıcı istatistikleri:
    - Doğru kelime oranı: {user_stats.get('correct_word_ratio', 0)*100:.1f}%
    - Ortalama telaffuz puanı: {user_stats.get('pronunciation_avg', 0):.1f}
    - Zayıf kelimeler: {", ".join(user_stats.get('weak_words', []))}

    Bu kullanıcıya Türkçe olarak 2–3 cümlelik kişisel geri bildirim yaz.
    1. Küçük bir motivasyon cümlesi olsun.
    2. Hangi alana odaklanması gerektiğini söyle (kelime, telaffuz vs.).
    3. Çok akademik değil, samimi ama öğretici bir dil kullan.
    """
    result = _llm_chat(prompt, system="You are a friendly language learning coach.")
    return result

def generate_custom_lesson(topic: str, level: str = "A1-A2") -> str:
    """
    Kullanıcının istediği konuya göre yapay zekâ ile mini ders üretir.
    Bu fonksiyon SmartLang'in özgün özelliğidir.
    """
    prompt = f"""
    Kullanıcı İngilizce öğreniyor ve şu konuyu çalışmak istiyor:
    "{topic}"

    Seviye: {level}

    Lütfen:
    1) Bu konuya uygun 2 kısa ve basit İngilizce örnek cümle yaz
    2) 1 adet mini alıştırma sorusu oluştur
    3) Türkçe kısa bir açıklama ekle

    Cevabı sade, öğretici ve A1–A2 seviyesine uygun yaz.
    """

    return _llm_chat(prompt, system="You are a friendly English teacher.")

def pronunciation_feedback(expected: str, recognized: str) -> dict:
    """
    Kullanıcının telaffuzunu değerlendirir.
    """
    prompt = f"""
    Expected word: "{expected}"
    Recognized speech: "{recognized}"

    Evaluate pronunciation quality from 0 to 100.
    Then explain shortly in Turkish:
    - What was correct
    - What was wrong
    - How to improve

    Return JSON format:
    {{
      "score": number,
      "feedback_tr": string
    }}
    but not use ```json just text but but json format.
    """

    result = _llm_chat(prompt, system="You are an English pronunciation coach.")
    
    # Fallback kontrolü
    if result == "DUMMY_RESPONSE":
        return _simple_pronunciation_check(expected, recognized)

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return _simple_pronunciation_check(expected, recognized)


def _simple_pronunciation_check(expected: str, recognized: str) -> dict:
    """API olmadan basit telaffuz kontrolü yapar."""
    expected_lower = expected.lower().strip()
    recognized_lower = recognized.lower().strip()
    
    # Levenshtein mesafesi hesapla
    def levenshtein(a, b):
        if len(a) < len(b):
            return levenshtein(b, a)
        if len(b) == 0:
            return len(a)
        
        previous_row = range(len(b) + 1)
        for i, c1 in enumerate(a):
            current_row = [i + 1]
            for j, c2 in enumerate(b):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]
    
    distance = levenshtein(expected_lower, recognized_lower)
    max_len = max(len(expected_lower), len(recognized_lower))
    
    # Benzerlik yüzdesi
    if max_len == 0:
        similarity = 100
    else:
        similarity = max(0, 100 - (distance / max_len * 100))
    
    score = int(similarity)
    
    # Geri bildirim oluştur
    if expected_lower == recognized_lower:
        feedback = f"Mükemmel! '{expected}' kelimesini doğru telaffuz ettin."
    elif score >= 80:
        feedback = f"Çok iyi! '{expected}' kelimesine çok yaklaştın. Algılanan: '{recognized}'. Küçük düzeltmelerle mükemmel olacak."
    elif score >= 60:
        feedback = f"Fena değil! '{expected}' kelimesini pratik etmeye devam et. Algılanan: '{recognized}'."
    elif score >= 40:
        feedback = f"'{expected}' kelimesinin telaffuzunu geliştirmelisin. Algılanan: '{recognized}'. Kelimenin ses yapısına dikkat et."
    else:
        feedback = f"'{expected}' kelimesini daha yavaş ve net söylemeyi dene. Algılanan: '{recognized}'."
    
    return {
        "score": score,
        "feedback_tr": feedback
    }


def mistake_feedback(wrong_answer: str, correct_answer: str, context: str = "sentence") -> dict:
    """
    Kullanıcının yaptığı hataya LLM tarafından ayrıntılı ve kişiselleştirilmiş geri bildirim sağlar.
    
    Parametreler:
    - wrong_answer: Kullanıcının yanlış yaptığı şey
    - correct_answer: Doğru cevap
    - context: Hata tipi ("word", "sentence", "pronunciation")
    
    Dönen format:
    {
      "explanation": "Türkçe detaylı açıklama",
      "tips": ["İpucu 1", "İpucu 2"],
      "example": "Benzeri bir örnek",
      "practice_sentence": "Pratik için örnek cümle"
    }
    """
    
    context_descriptions = {
        "word": "Kelime çevirisi",
        "sentence": "Cümle yazma / Gramer",
        "pronunciation": "Telaffuz"
    }
    
    context_desc = context_descriptions.get(context, context)
    
    prompt = f"""Kullanıcı İngilizce öğreniyor ve bir hata yaptı.

Hata Tipi: {context_desc}
Yanlış Cevap: "{wrong_answer}"
Doğru Cevap: "{correct_answer}"

Lütfen kullanıcıya Türkçe olarak:
1. Bu hatanın neden yanlış olduğunu açıkla (2-3 cümle, kısa ve net)
2. 2-3 uygulamalı ipucu ver 
3. Benzer bir örnek ver (İngilizce tam cümle)
4. Doğru cevabı içeren anlamlı bir İngilizce örnek cümle yaz (practice_sentence). Bu cümle doğru cevabı bağlamında kullanmalı.

Örnek: Doğru cevap "beautiful" ise, practice_sentence: "The sunset was so beautiful that everyone stopped to watch it."

SADECE şu JSON formatında cevap ver, başka birşey yazma:
{{"explanation": "...", "tips": ["...", "...", "..."], "example": "...", "practice_sentence": "..."}}"""
    
    result = _llm_chat(prompt, system="You are a supportive English teacher who gives feedback in Turkish.")
    
    # Dummy response kontrolü
    if result == "DUMMY_RESPONSE":
        print(f"⚠️ API bağlantısı yok, fallback feedback kullanılıyor")
        
        # Doğru cevaba göre anlamlı bir örnek cümle oluştur
        correct_lower = correct_answer.lower().strip()
        
        # Basit örnek cümleler
        practice_examples = {
            # Sıfatlar
            "happy": "I feel happy when I spend time with my family.",
            "sad": "She looked sad after hearing the bad news.",
            "big": "This is a very big house with many rooms.",
            "small": "The small cat is sleeping on the sofa.",
            "beautiful": "The garden looks beautiful in spring.",
            "good": "This is a good book to read.",
            "bad": "The weather was bad yesterday.",
            "hot": "The coffee is too hot to drink.",
            "cold": "It's very cold outside today.",
            "new": "I bought a new phone last week.",
            "old": "This is an old building from 1900.",
            "fast": "The train is very fast.",
            "slow": "The turtle is slow but steady.",
            "easy": "This exercise is easy to understand.",
            "hard": "The exam was really hard.",
            "difficult": "Learning a new language can be difficult.",
            # Fiiller - Temel
            "go": "I go to school every morning.",
            "went": "She went to the store yesterday.",
            "gone": "He has gone home already.",
            "come": "Please come to my party tomorrow.",
            "came": "They came to visit us last Sunday.",
            "eat": "We eat dinner at 7 o'clock.",
            "ate": "I ate breakfast at 8 this morning.",
            "drink": "I drink water every day.",
            "drank": "She drank her coffee quickly.",
            "read": "She likes to read books in the evening.",
            "write": "Can you write your name here?",
            "wrote": "He wrote a letter to his friend.",
            "run": "The children run in the park.",
            "ran": "He ran to catch the bus.",
            "walk": "I walk to work every day.",
            "walked": "We walked along the beach.",
            "see": "I can see the mountains from here.",
            "saw": "I saw a movie last night.",
            "take": "Please take your umbrella.",
            "took": "She took her bag and left.",
            "make": "Can you make some coffee?",
            "made": "He made a delicious cake.",
            "give": "Please give me the book.",
            "gave": "She gave me a nice gift.",
            "buy": "I want to buy a new car.",
            "bought": "They bought a house last year.",
            "think": "I think this is a good idea.",
            "thought": "I thought about your question.",
            "know": "I know the answer.",
            "knew": "She knew the truth all along.",
            "want": "I want to learn English.",
            "need": "You need to study more.",
            "like": "I like chocolate ice cream.",
            "love": "I love my family very much.",
            "have": "I have two brothers.",
            "had": "She had a great time at the party.",
            "has": "He has a beautiful garden.",
            "is": "She is my best friend.",
            "are": "They are very kind people.",
            "was": "It was a wonderful day.",
            "were": "We were happy to see you.",
            "do": "I do my homework every day.",
            "did": "She did a great job.",
            "does": "He does his best.",
            # İsimler
            "book": "I'm reading an interesting book.",
            "water": "Please drink more water.",
            "food": "The food at this restaurant is delicious.",
            "house": "They live in a big house.",
            "car": "My father has a red car.",
            "school": "I go to school by bus.",
            "work": "She goes to work at 9 AM.",
            "friend": "He is my best friend.",
            "family": "My family is very important to me.",
            "time": "What time is it now?",
            "day": "Today is a beautiful day.",
            "year": "This year went by so fast.",
            "money": "He saved a lot of money.",
            "life": "Life is full of surprises.",
        }
        
        # Eğer özel bir cümle varsa kullan, yoksa dinamik cümle oluştur
        if correct_lower in practice_examples:
            practice_sent = practice_examples[correct_lower]
        else:
            # Kelimeye göre basit cümle oluştur
            if correct_lower.endswith('ed'):
                practice_sent = f"Yesterday, she {correct_answer} the task successfully."
            elif correct_lower.endswith('ing'):
                practice_sent = f"She is {correct_answer} right now."
            elif correct_lower.endswith('ly'):
                practice_sent = f"He did the work {correct_answer}."
            elif correct_lower.endswith('tion') or correct_lower.endswith('sion'):
                practice_sent = f"The {correct_answer} was very important."
            elif correct_lower.endswith('ness'):
                practice_sent = f"Her {correct_answer} was truly inspiring."
            else:
                practice_sent = f"Example: 'I use {correct_answer} in my daily life.'"
        
        return {
            "explanation": f"'{wrong_answer}' yerine '{correct_answer}' kullanmalısın. Bu kelimeyi doğru kullanmayı öğrenmek için örnek cümleyi incele.",
            "tips": [
                "Doğru cevabı yüksek sesle tekrar et",
                "Kelimeyi bir cümle içinde kullanmaya çalış",
                "Günlük hayatta bu kelimeyi kullanacak durumlar düşün"
            ],
            "example": f"Correct usage: {correct_answer}",
            "practice_sentence": practice_sent
        }
    
    try:
        # Eğer sonuç zaten bir string JSON ise direkt parse et
        if isinstance(result, str):
            # JSON'ı bul ve çıkar (markdown formatında gelebilir)
            if "```" in result:
                result = result.split("```")[1].replace("json", "").strip()
            
            data = json.loads(result)
            # Gerekli alanların hepsi var mı kontrol et
            if not all(key in data for key in ["explanation", "tips", "example", "practice_sentence"]):
                raise ValueError("Eksik alanlar")
            return data
    except (json.JSONDecodeError, ValueError, IndexError) as e:
        print(f"⚠️ JSON parse hatası: {e}, fallback kullanılıyor")
    
    # Fallback: Manuel bir geri bildirim oluştur
    return {
        "explanation": f"'{wrong_answer}' yerine '{correct_answer}' kullanmalısın.",
        "tips": [
            "Doğru cevabı tekrar et ve hatırla",
            "Benzer durumlarda tekrar dene",
            "Sık sık pratik yap"
        ],
        "example": f"Doğru kullanım: {correct_answer}",
        "practice_sentence": f"Örnek cümle: She decided to {correct_answer} the project carefully."
    }

