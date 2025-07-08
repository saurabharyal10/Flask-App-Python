import sqlite3

conn = sqlite3.connect('submissions.db')
cursor = conn.cursor()

# Try adding created_at to submissions
try:
    cursor.execute("ALTER TABLE submissions ADD COLUMN created_at TEXT")
    print("✅ added created_at to submissions")
except Exception as e:
    print("❌ Error in submissions:", e)

# Try adding created_at to feedback
try:
    cursor.execute("ALTER TABLE feedback ADD COLUMN created_at TEXT")
    print("✅ added created_at to feedback")
except Exception as e:
    print("❌ Error in feedback:", e)

# Backfill NULLs with current timestamp
try:
    cursor.execute("UPDATE submissions SET created_at = datetime('now') WHERE created_at IS NULL")
    cursor.execute("UPDATE feedback SET created_at = datetime('now') WHERE created_at IS NULL")
    print("✅ Backfilled missing dates")
except Exception as e:
    print("❌ Error while backfilling:", e)

conn.commit()
conn.close()
