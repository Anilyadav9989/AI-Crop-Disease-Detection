import sqlite3

conn = sqlite3.connect("crop_disease.db")

cursor = conn.cursor()

try:
    cursor.execute("""
    ALTER TABLE predictions
    ADD COLUMN username TEXT
    """)
    print("Username column added successfully!")

except Exception as e:
    print("Column may already exist:", e)

conn.commit()
conn.close()