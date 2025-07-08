import sqlite3

conn = sqlite3.connect('submissions.db')
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(submissions)")
print("Submissions Table Columns:")
for col in cursor.fetchall():
    print(col)

cursor.execute("PRAGMA table_info(feedback)")
print("\nFeedback Table Columns:")
for col in cursor.fetchall():
    print(col)

conn.close()
