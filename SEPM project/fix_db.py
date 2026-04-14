import sqlite3
import os

db_path = 'ats_platform.db'
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(resume)")
        columns = [c[1] for c in cursor.fetchall()]
        
        if 'summary' not in columns:
            print("Adding 'summary' column to 'resume' table...")
            cursor.execute("ALTER TABLE resume ADD COLUMN summary TEXT")
            conn.commit()
            print("Successfully added 'summary' column.")
        else:
            print("Column 'summary' already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Database file {db_path} not found.")
