from ai_utils import (
    translate_word,
    generate_sentence,
    grammar_feedback,
    grammar_feedback_json,
    personalized_feedback,
    generate_custom_lesson
)


def main():
    print("=== translate_word('apple') ===")
    print(translate_word("apple"))
    print()

    print("=== generate_sentence('apple') ===")
    print(generate_sentence("apple"))
    print()

    sentence = "She go to school yesterday."
    print("=== grammar_feedback (düz metin) ===")
    print(grammar_feedback(sentence))
    print()

    print("=== grammar_feedback_json (yapısal çıktı) ===")
    data = grammar_feedback_json(sentence)
    print("corrected:", data.get("corrected"))
    print("mistakes:")
    for m in data.get("mistakes", []):
        print(" - part:", m.get("part"), "| explanation_tr:", m.get("explanation_tr"))
    print()

    print("=== personalized_feedback(stats) ===")
    stats = {
        "correct_word_ratio": 0.65,
        "pronunciation_avg": 78.2,
        "weak_words": ["apple", "orange", "banana"]
    }
    print(personalized_feedback(stats))
    print()
    print("=== generate_custom_lesson (özgün özellik) ===")
    topic = "Ordering food at a restaurant"
    print(generate_custom_lesson(topic))



if __name__ == "__main__":
    main()
