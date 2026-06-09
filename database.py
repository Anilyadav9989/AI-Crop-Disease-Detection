import sqlite3

conn = sqlite3.connect("crop_disease.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    disease TEXT,
    confidence REAL,
    fertilizer TEXT,
    treatment TEXT,
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("Database Created Successfully!")