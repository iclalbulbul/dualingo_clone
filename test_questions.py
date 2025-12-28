from features.course_system import course_system

qs = course_system.get_lesson_questions(1, 1)
print(f"Toplam soru: {len(qs)}")
print()
for i, q in enumerate(qs):
    print(f"{i+1}. {q['question']} = {q['answer']}")
    print(f"   Seçenekler: {q['options']}")
    print()
