# lesson_flow.py
# SmartLang / Duolingo-benzeri "1 tur ders" akışı (CLI iskeleti)
# Modüller: ai_utils.py, speech_stt.py, speech_utils.py, rules.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
import json

from ai_utils import (
    translate_word,
    generate_sentence,
    grammar_feedback_json,
    pronunciation_feedback,
    personalized_feedback,
    generate_custom_lesson,
)
from speech_stt import listen_and_recognize
from speech_utils import TextToSpeech
from rules import analyze_sentence
import re
from tracker import save_pronunciation, save_sentence_attempt
from db_utils import create_or_get_user, record_mistake


def contains_target_word(sentence: str, word: str) -> bool:
    """
    Kelimenin cümlede 'ayrı bir kelime' olarak geçip geçmediğini kontrol eder.
    (apple -> pineapple sayılmaz)
    """
    pattern = r"\b" + re.escape(word.lower()) + r"\b"
    return re.search(pattern, sentence.lower()) is not None



# -----------------------------
# Konfig
# -----------------------------
@dataclass
class LessonConfig:
    stt_language: str = "en-US"
    enable_tts: bool = True
    enable_stt: bool = True
    use_llm_grammar: bool = True
    use_rules_grammar: bool = True


# -----------------------------
# Yardımcılar
# -----------------------------
def safe_tts(tts: TextToSpeech, text: str, enabled: bool = True) -> None:
    if not enabled:
        return
    try:
        tts.speak(text=text)
    except Exception as e:
        print(f"⚠️ TTS hata: {e}")


def safe_listen(language: str = "en-US") -> str:
    """
    speech_stt.listen_and_recognize zaten hata durumunda '❌ ...' string döndürüyor. :contentReference[oaicite:1]{index=1}
    """
    try:
        return listen_and_recognize(language=language)
    except Exception as e:
        return f"❌ STT hata: {e}"


def safe_pronunciation(expected: str, recognized: str) -> Dict[str, Any]:
    """
    ai_utils.pronunciation_feedback JSON parse ile dönebiliyor/patlayabiliyor. :contentReference[oaicite:2]{index=2}
    Burada akışı çökertmemek için koruma koyuyoruz.
    """
    try:
        data = pronunciation_feedback(expected, recognized)
        # beklenen: {"score": number, "feedback_tr": string}
        if isinstance(data, dict) and "score" in data:
            return data
        return {"score": 0, "feedback_tr": "⚠️ Beklenmeyen telaffuz çıktısı alındı."}
    except json.JSONDecodeError:
        return {
            "score": 0,
            "feedback_tr": "⚠️ LLM JSON formatında dönmedi (telaffuz değerlendirmesi alınamadı).",
        }
    except Exception as e:
        return {"score": 0, "feedback_tr": f"⚠️ Telaffuz değerlendirmesi hata verdi: {e}"}


# -----------------------------
# 1 Tur Akışı
# -----------------------------
def run_word_practice(word: str, cfg: LessonConfig) -> Dict[str, Any]:
    """
    1) kelimeyi çevir
    2) TTS ile söyle
    3) kullanıcı söylesin -> STT
    4) telaffuz puanı (LLM)
    """
    tts = TextToSpeech()

    print("\n" + "=" * 60)
    print(f"📌 WORD PRACTICE: {word}")
    print("=" * 60)

    # Çeviri
    tr = translate_word(word)
    print(f"🇹🇷 Çeviri: {tr}")

    # Telaffuz talimatı
    prompt = f"Please say the word: {word}"
    print(f"🔊 {prompt}")
    safe_tts(tts, prompt, enabled=cfg.enable_tts)

    recognized = ""
    if cfg.enable_stt:
        recognized = safe_listen(language=cfg.stt_language)
        print(f"📝 STT Sonuç: {recognized}")
    else:
        recognized = input("✍️ (STT kapalı) Duyulan metni buraya yaz: ").strip()

    # Eğer STT hata döndürdüyse telaffuz değerlendirmesi yapma
    if recognized.startswith("❌"):
        pron = {"score": 0, "feedback_tr": "STT başarısız olduğu için telaffuz puanı verilemedi."}
    else:
        pron = safe_pronunciation(word, recognized)

    print(f"🎯 Telaffuz Puanı: {pron.get('score')}")
    print(f"🧠 Geri Bildirim: {pron.get('feedback_tr')}")

    return {
        "word": word,
        "translation_tr": tr,
        "recognized": recognized,
        "pronunciation": pron,
    }


def run_sentence_practice(word: str, cfg: LessonConfig) -> Dict[str, Any]:
    """
    1) LLM ile örnek cümle üret
    2) kullanıcıdan aynı anlamda cümle yazmasını iste
    3) rules + LLM grammar kontrolü
    """
    tts = TextToSpeech()

    print("\n" + "=" * 60)
    print("🧩 SENTENCE PRACTICE")
    print("=" * 60)

    example_sentence = generate_sentence(word)
    print(f"📚 Örnek cümle: {example_sentence}")
    safe_tts(tts, f"Example sentence: {example_sentence}", enabled=cfg.enable_tts)

    user_sentence = input("✍️ Şimdi sen bu kelimeyle bir cümle yaz: ").strip()

    out: Dict[str, Any] = {
        "word": word,
        "example_sentence": example_sentence,
        "user_sentence": user_sentence,
        "rules_grammar": None,
        "llm_grammar": None,
    }

    # Rules tabanlı hızlı kontrol
    if cfg.use_rules_grammar:
        rules_result = analyze_sentence(user_sentence)
        out["rules_grammar"] = rules_result
            # ✅ Duolingo mantığı: hedef kelime cümlede geçiyor mu?
    if not contains_target_word(user_sentence, word):
        # errors / suggestions None gelirse güvence
        if rules_result.get("errors") is None:
            rules_result["errors"] = []
        if rules_result.get("suggestions") is None:
            rules_result["suggestions"] = []

        rules_result["errors"].append({
            "rule": "missing_target_word",
            "message_tr": f"Cümlede hedef kelime geçmiyor: '{word}'",
        })

        # Ceza puanı (istersen 20/30/50 yapabilirsin)
        rules_result["score"] = max(0, int(rules_result.get("score", 0)) - 40)

        # İstersen tamamen geçersiz say
        rules_result["is_valid"] = False

        rules_result["suggestions"].append(f"Kelimeyi cümlede kullan: '{word}'")

        print("\n🧾 (Rules) Hızlı kontrol:")
        print(f"✅ Geçerli mi?: {rules_result.get('is_valid')}")
        print(f"📊 Skor: {rules_result.get('score')}/100")
        if rules_result.get("errors"):
            print("❌ Hatalar:")
            for err in rules_result["errors"]:
                print(f" - [{err.get('rule')}] {err.get('message_tr')}")
        if rules_result.get("suggestions"):
            print("💡 Öneriler:")
            for s in rules_result["suggestions"]:
                print(f" - {s}")
            if cfg.use_rules_grammar:
                rules_result = analyze_sentence(user_sentence)
    

    # LLM tabanlı zengin kontrol (yapısal JSON)
    if cfg.use_llm_grammar:
        llm_result = grammar_feedback_json(user_sentence)
        out["llm_grammar"] = llm_result
        print("\n🤖 (LLM) Detaylı kontrol:")
        print("✅ Corrected:", llm_result.get("corrected"))
        mistakes = llm_result.get("mistakes", [])
        if mistakes:
            print("🧠 Mistakes:")
            for m in mistakes:
                print(f" - part: {m.get('part')} | explanation_tr: {m.get('explanation_tr')}")

    return out


def run_one_lesson(word: str, cfg: LessonConfig) -> Dict[str, Any]:
    """
    Tek tur = word_practice + sentence_practice
    """
    result = {
        "word_practice": run_word_practice(word, cfg),
        "sentence_practice": run_sentence_practice(word, cfg),
    }
    return result


# -----------------------------
# Opsiyonel: kişisel geri bildirim / custom lesson demo
# -----------------------------
def demo_personalized_feedback() -> None:
    stats = {
        "correct_word_ratio": 0.65,
        "pronunciation_avg": 78.2,
        "weak_words": ["apple", "orange", "banana"]
    }
    print("\n🌟 Personalized feedback:")
    print(personalized_feedback(stats))


def demo_custom_lesson(topic: str) -> None:
    print("\n📘 Custom lesson:")
    print(generate_custom_lesson(topic))


# -----------------------------
# CLI
# -----------------------------
def main():
    print("🎮 SmartLang Lesson Flow (CLI)")
    username = input("👤 Kullanıcı adı: ").strip()
    if not username:
        print("❌ Kullanıcı adı gerekli")
        return

    user_id = create_or_get_user(username)

    cfg = LessonConfig(
        stt_language="en-US",
        enable_tts=True,
        enable_stt=True,
        use_llm_grammar=True,
        use_rules_grammar=True,
    )

    print("Çıkmak için boş bırakıp Enter'a basabilirsin.\n")

    while True:
        word = input("🟦 Çalışılacak kelime (örn: banana): ").strip()
        if not word:
            print("👋 Çıkış.")
            break

        lesson_result = run_one_lesson(word, cfg)

        # =========================
        # 📌 PRONUNCIATION KAYDI
        # =========================
        wp = lesson_result["word_practice"]
        pron = wp["pronunciation"]

        save_pronunciation(
            user_id=user_id,
            word=wp["word"],
            score=pron.get("score"),
            feedback=pron.get("feedback_tr"),
        )

        # Eğer telaffuz puanı düşükse, hatayı kaydet
        try:
            score = pron.get("score")
            if score is not None:
                # eşik: 70 (yüzlükse), düşük puan sayılır
                if isinstance(score, (int, float)) and score < 70:
                    record_mistake(
                        user_id=user_id,
                        item_key=wp["word"],
                        wrong_answer=wp.get("recognized", ""),
                        correct_answer=wp["word"],
                        lesson_id=None,
                        context="pronunciation",
                    )
        except Exception:
            pass

        # =========================
        # 📌 SENTENCE KAYDI
        # =========================
        sp = lesson_result["sentence_practice"]

        rules_score = (
            sp["rules_grammar"]["score"]
            if sp.get("rules_grammar")
            else None
        )

        save_sentence_attempt(
            user_id=user_id,
            word=sp["word"],
            sentence=sp["user_sentence"],
            score=rules_score,
            metadata={
                "llm": sp.get("llm_grammar"),
                "rules": sp.get("rules_grammar"),
            }
        )

        # Eğer kurallar veya LLM kontrolünde hata varsa, genel bir mistake kaydı ekle
        try:
            llm = sp.get("llm_grammar") or {}
            rules = sp.get("rules_grammar") or {}
            has_rules_error = rules and rules.get("is_valid") is False
            has_llm_mistakes = llm and bool(llm.get("mistakes"))
            if has_rules_error or has_llm_mistakes:
                corrected = llm.get("corrected") if llm else None
                record_mistake(
                    user_id=user_id,
                    item_key=sp["word"],
                    wrong_answer=sp.get("user_sentence", ""),
                    correct_answer=corrected or sp.get("example_sentence"),
                    lesson_id=None,
                    context="sentence",
                )
        except Exception:
            pass

        print("✅ Kayıt alındı")
        print("-" * 60)


if __name__ == "__main__":
    main()
