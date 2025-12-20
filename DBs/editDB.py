import sqlite3

DB_PATH = "DBs/points.db"

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    a = "<script>alert('XSS')</script>"
    cursor.execute("""INSERT INTO student VALUES (?, ?)""", (6,a))