"""
SmartLang – AI Utilities

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

from openai import OpenAI

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

client = None
if API_KEY:
    client = OpenAI(api_key=API_KEY)
else:
    # "API key yoksa dummy moda düşüyor"
    print("WARNING: OPENAI_API_KEY set edilmemiş, ai_utils dummy modda çalışacak.")


def _llm_chat(prompt: str, system: str = "You are an English teacher.") -> str:
    """
    Tüm LLM çağrıları buradan geçer. Eğer API yoksa dummy cevap döner.
    """
    if client is None:
        # Fallback: gerçek LLM yokken sahte cevap
        return "️ Şu an LLM'e bağlı değiliz (dummy cevap). Prompt: " + prompt[:80]

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()

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

    return result.splitlines()[0]

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
    """
    result = _llm_chat(prompt, system="You are an English grammar teacher.")

    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        # LLM düzgün JSON döndüremezse uygulama çökmesin diye fallback
        return {
            "corrected": sentence,
            "mistakes": [
                {
                    "part": sentence,
                    "explanation_tr": "JSON formatı alınamadı, bu nedenle orijinal cümleyi döndürüyoruz."
                }
            ]
        }

    return data


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
    """

    result = _llm_chat(prompt, system="You are an English pronunciation coach.")

    # API yoksa fallback
    if result.startswith("⚠️"):
        return {
            "score": 50,
            "feedback_tr": "Telaffuz kısmen doğru ancak daha net konuşmalısın."
        }

    import json
    try:
        return json.loads(result)
    except:
        return {
            "score": 60,
            "feedback_tr": "Telaffuz değerlendirildi ancak ayrıntı alınamadı."
        }
