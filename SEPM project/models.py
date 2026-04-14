from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()
from flask_login import LoginManager
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False) # 'seeker' or 'recruiter'

    jobs = db.relationship('Job', backref='recruiter', lazy=True)
    resumes = db.relationship('Resume', backref='seeker', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.Text, nullable=False)  # JSON or comma-separated format
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    applications = db.relationship('Application', backref='job', lazy=True, cascade='all, delete-orphan')

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    raw_text = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=True) # AI-generated Professional Summary
    extracted_skills = db.Column(db.Text, nullable=True) # JSON 
    education = db.Column(db.Text, nullable=True) # JSON
    experience = db.Column(db.Text, nullable=True) # JSON
    parsed_status = db.Column(db.String(50), default="Pending") # Pending, Processing, Completed, Failed
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='resume', lazy=True, cascade='all, delete-orphan')

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey('resume.id'), nullable=False)
    match_score = db.Column(db.Float, nullable=True) # 0-100 float computed securely in background
    skill_gaps = db.Column(db.Text, nullable=True) # JSON array of missing skills
    status = db.Column(db.String(50), default="Applied") # Applied, Reviewing, Interview, Offer, Rejected (For Kanban ATS)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
