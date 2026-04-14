from app import create_app
from models import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE job ADD COLUMN deadline DATETIME'))
            conn.commit()
        print("Migration successful: added deadline column to job table.")
    except Exception as e:
        if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
            print("Column 'deadline' already exists.")
        else:
            print(f"Migration failed: {e}")
