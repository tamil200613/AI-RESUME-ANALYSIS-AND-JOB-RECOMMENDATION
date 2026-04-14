from app import create_app
from models import db, Job
from datetime import datetime

app = create_app()
with app.app_context():
    now = datetime.utcnow()
    # 1. Check RAW data
    jobs = Job.query.all()
    print(f"DEBUG: Current UTC: {now}")
    print("-" * 50)
    for j in jobs:
        print(f"ID: {j.id} | Title: {j.title}")
        print(f"  - Deadline: {j.deadline} (Type: {type(j.deadline)})")
        print(f"  - Active: {j.is_active}")
        if j.deadline:
            print(f"  - Deadline < Now: {j.deadline < now}")
            print(f"  - Deadline >= Now: {j.deadline >= now}")
    
    print("-" * 50)
    # 2. Check Query result
    import sqlalchemy
    from sqlalchemy import or_
    all_active_jobs = Job.query.filter(
        Job.is_active == True,
        or_(Job.deadline == None, Job.deadline >= now)
    ).all()
    print(f"DEBUG: SQLAlchemy Query returned {len(all_active_jobs)} jobs.")
    for j in all_active_jobs:
        print(f"  [IN QUERY]: ID {j.id} - {j.title}")
