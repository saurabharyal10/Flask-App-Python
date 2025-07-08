import sqlite3

conn = sqlite3.connect('submissions.db')
cursor = conn.cursor()

cursor.execute("SELECT name, created_at FROM submissions LIMIT 5")
rows = cursor.fetchall()

print("Sample Data:")
for row in rows:
    print(row)

conn.close()
