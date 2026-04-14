from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Job, Resume, Application
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Platform stats
    stats = {
        'total_users': User.query.count(),
        'total_seekers': User.query.filter_by(role='seeker').count(),
        'total_recruiters': User.query.filter_by(role='recruiter').count(),
        'total_jobs': Job.query.count(),
        'total_resumes': Resume.query.count(),
        'total_applications': Application.query.count()
    }
    
    # Recent users
    recent_users = User.query.order_by(User.id.desc()).limit(10).all()
    
    # Recent jobs
    recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html', stats=stats, recent_users=recent_users, recent_jobs=recent_jobs)

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete yourself.', 'warning')
        return redirect(url_for('admin.manage_users'))
        
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} deleted.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/jobs')
@login_required
@admin_required
def manage_jobs():
    jobs = Job.query.all()
    return render_template('admin_jobs.html', jobs=jobs)
