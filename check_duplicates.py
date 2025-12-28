from db_utils import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# user_course_progress'te duplicate kontrol
cur.execute('SELECT user_id, unit_id, lesson_id, COUNT(*) as cnt FROM user_course_progress GROUP BY user_id, unit_id, lesson_id HAVING cnt > 1')
dups = cur.fetchall()
print('Duplicate Progress:')
for d in dups:
    print(f'  user_id={d[0]}, unit_id={d[1]}, lesson_id={d[2]}, count={d[3]}')

# A1 unitlerini kontrol et
cur.execute("SELECT unit_id, order_num, title FROM course_units WHERE level_code = 'A1' ORDER BY order_num")
units = cur.fetchall()
print('\nA1 Units:')
for u in units:
    print(f'  unit_id={u[0]}, order={u[1]}, title={u[2]}')

# Kullanıcı 22 için progress kayıtları
cur.execute('SELECT unit_id, lesson_id, status FROM user_course_progress WHERE user_id = 22 ORDER BY unit_id, lesson_id')
progress = cur.fetchall()
print('\nUser 22 Progress:')
for p in progress:
    print(f'  unit_id={p[0]}, lesson_id={p[1]}, status={p[2]}')

conn.close()
