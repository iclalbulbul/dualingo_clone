import sqlite3

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

print("=== A1 SEVİYESİ KELİMELER ===")
cursor.execute("SELECT english, turkish FROM words WHERE level = 'A1' AND turkish IS NOT NULL LIMIT 30")
for row in cursor.fetchall():
    print(f"  {row[0]} = {row[1]}")

print("\n=== KAYNAK KONTROLÜ ===")
cursor.execute("SELECT COUNT(*) FROM words WHERE turkish IS NOT NULL")
print(f"Türkçe çevirisi olan kelime: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM words WHERE turkish IS NULL OR turkish = ''")
print(f"Türkçe çevirisi olmayan kelime: {cursor.fetchone()[0]}")

conn.close()
