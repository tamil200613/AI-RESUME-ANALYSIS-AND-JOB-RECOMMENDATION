from app import create_app
from models import db, Job
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    # 1. Create a dummy job that should DEFINITELY be expired
    expired_job = Job(
        title="EXPIRED TEST JOB",
        description="This job should not show",
        required_skills="None",
        posted_by=1, # Admin/First user
        deadline=datetime.utcnow() - timedelta(days=1),
        is_active=True
    )
    db.session.add(expired_job)
    db.session.commit()
    print(f"Created expired job ID: {expired_job.id}")

    # 2. Run the logic from seeker.py
    now = datetime.utcnow()
    raw_jobs = Job.query.filter_by(is_active=True).all()
    all_active_jobs = []
    
    # EXACT LOGIC FROM SEEKER.PY:
    for job in raw_jobs:
        effective_deadline = job.deadline or (job.created_at + timedelta(days=14))
        if effective_deadline.hour == 0 and effective_deadline.minute == 0:
            if effective_deadline.date() < now.date():
                continue
        else:
            if effective_deadline < now:
                continue
        all_active_jobs.append(job)

    # 3. Check if dummy job passed the filter
    passed = [j for j in all_active_jobs if j.id == expired_job.id]
    if passed:
        print(f"BUG! Expired job {expired_job.id} passed the filter!")
    else:
        print(f"PASS: Expired job {expired_job.id} was correctly hidden.")

    # 4. Clean up
    db.session.delete(expired_job)
    db.session.commit()
