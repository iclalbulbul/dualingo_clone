"""
backend/rules.py

Grammar Kural Motoru — kural tabanlı grammar denetimi.

Kontroller:
- Cümle başı büyük harf
- Noktalama
- Özne-fiil uyumu (Subject-Verb Agreement)
- Temel cümle yapısı
- Zamanlama tutarlılığı
"""

import re
from typing import List, Dict, Tuple

# ======== KURALLAR ========

# "I" özel durum - tekil ama çoğul fiil formu alır (I love, I go - "I loves" değil!)
SINGULAR_PRONOUNS_3RD = {"he", "she", "it", "this", "that"}  # 3. tekil şahıs - loves, goes
FIRST_PERSON_SINGULAR = {"i"}  # 1. tekil şahıs - love, go (am hariç)
PLURAL_PRONOUNS = {"we", "they", "you", "these", "those"}

SINGULAR_VERBS = {
    "is", "goes", "runs", "walks", "talks", "plays", "works", "likes", "loves",
    "has", "does", "eats", "drinks", "sleeps", "sits", "stands", "reads", "writes",
    "comes", "takes", "makes", "gives", "finds", "sees", "hears", "thinks",
}

PLURAL_VERBS = {
    "are", "go", "run", "walk", "talk", "play", "work", "like", "love",
    "have", "do", "eat", "drink", "sleep", "sit", "stand", "read", "write",
    "come", "take", "make", "give", "find", "see", "hear", "think",
}

PAST_TENSE_VERBS = {
    "was", "were", "went", "ran", "walked", "talked", "played", "worked", "liked", "loved",
    "had", "did", "ate", "drank", "slept", "sat", "stood", "read", "wrote", "came", "took",
    "made", "gave", "found", "saw", "heard", "thought", "wanted", "needed", "knew", "became"
}

COMMON_WORDS = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from"}

# ======== MAIN ANALYSIS ========

def analyze_sentence(sentence: str) -> Dict:
    """
    Cümleyi analiz eder ve grammar hatalarını tespit eder.
    
    Returns:
        {
            "sentence": str,
            "is_valid": bool,
            "errors": List[Dict],
            "score": float (0-100),
            "suggestions": List[str]
        }
    """
    
    errors = []
    sentence = sentence.strip()
    
    # Boş kontrol
    if not sentence:
        return {
            "sentence": sentence,
            "is_valid": False,
            "errors": [{"rule": "empty_sentence", "message_tr": "Cümle boş bırakılamaz."}],
            "score": 0,
            "suggestions": ["Lütfen bir cümle yazın."]
        }
    
    words = re.findall(r"[A-Za-z']+", sentence)
    
    # Özne-fiil uyumu
    agreement_error = check_subject_verb_agreement(sentence)
    if agreement_error:
        errors.append(agreement_error)
    
    # Cümle yapısı
    structure_errors = check_sentence_structure(sentence, words)
    errors.extend(structure_errors)
    
    # Zamanlama
    tense_errors = check_tense_consistency(sentence)
    errors.extend(tense_errors)
    
    # Score hesapla
    error_weight = {
        "capital_letter": 0,
        "punctuation": 0,
        "subject_verb_agreement": 25,
        "sentence_structure": 20,
        "tense_consistency": 15,
        "empty_sentence": 100,
        "minimum_words": 0,
    }
    
    total_penalty = sum(error_weight.get(err.get("rule"), 10) for err in errors)
    score = max(0, 100 - total_penalty)
    
    suggestions = generate_suggestions(errors, sentence)
    
    return {
        "sentence": sentence,
        "is_valid": len(errors) == 0,
        "errors": errors,
        "score": score,
        "suggestions": suggestions
    }


def check_subject_verb_agreement(sentence: str) -> Dict or None:
    """Özne-yüklem uyumunu kontrol et."""
    words_lower = sentence.rstrip(".!?").lower().split()
    
    if len(words_lower) < 2:
        return None
    
    subject = words_lower[0]
    verb = words_lower[1] if len(words_lower) > 1 else None
    
    if not verb:
        return None
    
    # "I" özel durum - çoğul fiil formu alır (I love, I go, I am)
    if subject in FIRST_PERSON_SINGULAR:
        # "I" sadece "am" ile kullanılır, "is" değil
        if verb == "is":
            return {
                "rule": "subject_verb_agreement",
                "message_tr": f"Özne 'I' ile 'is' değil 'am' kullanılmalı.",
                "subject": subject,
                "verb": verb,
                "correct_verb": "am"
            }
        # "I" tekil fiil formu almaz (I loves yanlış, I love doğru)
        if verb in SINGULAR_VERBS and verb not in {"am", "is", "was", "has"}:
            return {
                "rule": "subject_verb_agreement",
                "message_tr": f"Özne 'I' ile fiil '{verb}' yerine '{_get_plural_form(verb)}' kullanılmalı.",
                "subject": subject,
                "verb": verb,
                "correct_verb": _get_plural_form(verb)
            }
        return None
    
    # 3. tekil şahıs (he, she, it) - tekil fiil formu alır
    if subject in SINGULAR_PRONOUNS_3RD:
        if verb in PLURAL_VERBS and verb not in {"am", "is", "are"}:
            return {
                "rule": "subject_verb_agreement",
                "message_tr": f"Özne '{subject}' 3. tekil şahıs olduğu için, fiil '{verb}' yerine '{_get_singular_form(verb)}' kullanılmalı.",
                "subject": subject,
                "verb": verb,
                "correct_verb": _get_singular_form(verb)
            }
    
    # Çoğul özne
    elif subject in PLURAL_PRONOUNS:
        if verb in SINGULAR_VERBS and verb not in {"are", "were"}:
            return {
                "rule": "subject_verb_agreement",
                "message_tr": f"Özne '{subject}' çoğul olduğu için, fiil '{verb}' yerine '{_get_plural_form(verb)}' kullanılmalı.",
                "subject": subject,
                "verb": verb,
                "correct_verb": _get_plural_form(verb)
            }
    
    return None


def check_sentence_structure(sentence: str, words: List[str]) -> List[Dict]:
    """Temel cümle yapısını kontrol et."""
    errors = []
    words_lower = [w.rstrip(".!?").lower() for w in words]
    
    if len(words_lower) < 3:
        return errors
    
    pronouns = SINGULAR_PRONOUNS_3RD | FIRST_PERSON_SINGULAR | PLURAL_PRONOUNS
    if words_lower[0] in COMMON_WORDS and words_lower[0] not in pronouns:
        errors.append({
            "rule": "sentence_structure",
            "message_tr": f"Cümle genelde bir özne (isim/zamir) ile başlamalı, '{words_lower[0]}' yerine.",
            "position": 0
        })
    
    has_verb = any(w in SINGULAR_VERBS or w in PLURAL_VERBS or w in PAST_TENSE_VERBS for w in words_lower[1:3])
    if not has_verb:
        errors.append({
            "rule": "sentence_structure",
            "message_tr": "Cümle bir fiil içermelidir.",
        })
    
    return errors


def check_tense_consistency(sentence: str) -> List[Dict]:
    """Zamanlama tutarlılığını kontrol et."""
    errors = []
    words_lower = sentence.rstrip(".!?").lower().split()
    
    has_past = any(w in PAST_TENSE_VERBS for w in words_lower)
    has_present = any(w in SINGULAR_VERBS or w in PLURAL_VERBS for w in words_lower)
    
    if has_past and has_present:
        errors.append({
            "rule": "tense_consistency",
            "message_tr": "Cümle içinde geçmiş ve şimdiki zaman karışık görünüyor. Lütfen aynı zamanda tutarlı olun.",
        })
    
    return errors


# ======== YARDIMCI FONKSIYONLAR ========

def _get_singular_form(verb: str) -> str:
    """Fiili tekil hale getir."""
    verb_lower = verb.lower()
    
    if verb_lower == "are":
        return "is"
    if verb_lower == "do":
        return "does"
    if verb_lower == "have":
        return "has"
    
    if verb_lower.endswith(("s", "z", "ch", "sh", "x")):
        return verb_lower + "es"
    elif verb_lower.endswith("y") and not verb_lower[-2] in "aeiou":
        return verb_lower[:-1] + "ies"
    else:
        return verb_lower + "s"


def _get_plural_form(verb: str) -> str:
    """Fiili çoğul hale getir."""
    verb_lower = verb.lower()
    
    if verb_lower == "is":
        return "are"
    if verb_lower == "does":
        return "do"
    if verb_lower == "has":
        return "have"
    if verb_lower.endswith("es"):
        return verb_lower[:-2]
    if verb_lower.endswith("ies"):
        return verb_lower[:-3] + "y"
    if verb_lower.endswith("s"):
        return verb_lower[:-1]
    
    return verb_lower


def generate_suggestions(errors: List[Dict], sentence: str) -> List[str]:
    """Hata önerileri üret."""
    suggestions = []
    
    for error in errors:
        rule = error.get("rule")
        
        if rule == "capital_letter":
            corrected = sentence[0].upper() + sentence[1:]
            suggestions.append(f"Başı büyük harfle yazın: '{corrected}'")
        elif rule == "punctuation":
            corrected = sentence.rstrip(".!?") + "."
            suggestions.append(f"Cümleyi nokta ile bitirin: '{corrected}'")
        elif rule == "subject_verb_agreement":
            suggestions.append(
                f"Fiil uyumunu düzeltin: '{error.get('subject')} {error.get('correct_verb')}...'"
            )
        elif rule == "sentence_structure":
            suggestions.append("Cümleyi özne + fiil + nesne şeklinde düzenleyin.")
        elif rule == "tense_consistency":
            suggestions.append("Cümle içinde zamanlama tutarlı olmalı (geçmiş veya şimdiki).")
        elif rule == "minimum_words":
            suggestions.append("Cümle en az 2 kelime içermelidir.")
    
    return suggestions


if __name__ == "__main__":
    test_sentences = [
        "She go to school.",
        "they goes to the park every day.",
        "He is happy",
    ]
    
    print("=" * 70)
    print("GRAMMAR RULES ENGINE - DEMO")
    print("=" * 70)
    
    for sent in test_sentences:
        result = analyze_sentence(sent)
        print(f"\n📝 Cümle: {result['sentence']}")
        print(f"✓ Geçerli: {result['is_valid']}")
        print(f"📊 Skor: {result['score']}/100")
        
        if result['errors']:
            print("❌ Hatalar:")
            for err in result['errors']:
                print(f"  - [{err.get('rule')}] {err.get('message_tr')}")
        
        if result['suggestions']:
            print("💡 Öneriler:")
            for sugg in result['suggestions']:
                print(f"  - {sugg}")
        
        print("-" * 70)
