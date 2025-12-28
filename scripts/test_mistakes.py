"""
Quick test script for mistakes SRS flow.
Run: python scripts/test_mistakes.py
"""
from db_utils import init_db, create_or_get_user, record_mistake, get_due_mistakes, update_review_result
from scripts.migrate_mistakes import migrate
import time


def run_test():
    print("1) Ensure DB schema")
    init_db()
    migrate()

    print("2) Create test user")
    user_id = create_or_get_user("test_user_quiz")
    print(" -> user_id:", user_id)

    print("3) Record a mistake (word: banana)")
    mid = record_mistake(user_id=user_id, item_key="banana", wrong_answer="bananna", correct_answer="banana", lesson_id="lesson-1", context="sentence")
    print(" -> mistake_id:", mid)

    print("4) Get due mistakes")
    dues = get_due_mistakes(user_id=user_id, limit=10)
    print(" -> due count:", len(dues))
    if dues:
        print(" -> sample:", dues[0])

    print("5) Simulate review (quality=4)")
    res = update_review_result(user_id=user_id, item_key="banana", quality=4)
    print(" -> update result:", res)

    print("6) Get due again")
    dues2 = get_due_mistakes(user_id=user_id, limit=10)
    print(" -> due count after review:", len(dues2))


if __name__ == '__main__':
    run_test()
