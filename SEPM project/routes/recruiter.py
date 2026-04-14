from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Job, Application, Resume
import json
from datetime import datetime

recruiter_bp = Blueprint('recruiter', __name__, url_prefix='/recruiter')

@recruiter_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'recruiter':
        return redirect(url_for('seeker.dashboard'))
        
    jobs = Job.query.filter_by(posted_by=current_user.id).order_by(Job.created_at.desc()).all()
    
    # Calculate Stats
    stats = {
        'total_jobs': len(jobs),
        'total_applications': Application.query.join(Job).filter(Job.posted_by == current_user.id).count(),
        'pending_reviews': Application.query.join(Job).filter(Job.posted_by == current_user.id, Application.status == 'Applied').count(),
        'hired_count': Application.query.join(Job).filter(Job.posted_by == current_user.id, Application.status == 'Offer').count(),
        'now': datetime.utcnow()
    }
    
    return render_template('recruiter_dashboard.html', jobs=jobs, stats=stats)

@recruiter_bp.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role != 'recruiter':
        return redirect(url_for('seeker.dashboard'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        required_skills = request.form.get('required_skills')
        deadline_str = request.form.get('deadline')
        
        deadline = None
        if deadline_str:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            
        job = Job(
            title=title,
            description=description,
            required_skills=required_skills,
            posted_by=current_user.id,
            deadline=deadline
        )
        db.session.add(job)
        db.session.commit()
        
        flash('Job posted successfully!', 'success')
        return redirect(url_for('recruiter.dashboard'))
        
    return render_template('post_job.html')

@recruiter_bp.route('/job/<int:job_id>/board')
@login_required
def kanban_board(job_id):
    if current_user.role != 'recruiter':
        return redirect(url_for('seeker.dashboard'))
        
    job = Job.query.get_or_404(job_id)
    if job.posted_by != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('recruiter.dashboard'))
        
    # Get all applications for this job, sorted by match score
    applications = Application.query.filter_by(job_id=job.id).order_by(Application.match_score.desc()).all()
    
    # We will pass JSON decoder to template
    return render_template('kanban_board.html', job=job, applications=applications, json=json)

@recruiter_bp.route('/candidate/<int:application_id>')
@login_required
def candidate_details(application_id):
    if current_user.role != 'recruiter':
        return redirect(url_for('seeker.dashboard'))
        
    application = Application.query.get_or_404(application_id)
    job = Job.query.get(application.job_id)
    
    if job.posted_by != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('recruiter.dashboard'))
        
    return render_template('candidate_details.html', application=application, job=job, json=json)
    
@recruiter_bp.route('/application/<int:application_id>/status', methods=['POST'])
@login_required
def update_application_status(application_id):
    if current_user.role != 'recruiter':
        return redirect(url_for('seeker.dashboard'))
        
    application = Application.query.get_or_404(application_id)
    job = Job.query.get(application.job_id)
    
    if job.posted_by != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('recruiter.dashboard'))
        
    new_status = request.form.get('status')
    if new_status in ['Applied', 'Reviewing', 'Interview', 'Offer', 'Rejected']:
        application.status = new_status
        db.session.commit()
        flash(f'Candidate moved to {new_status}', 'success')
        
    # Redirect back to the referrer (kanban board or candidate details)
    return redirect(request.referrer or url_for('recruiter.candidate_details', application_id=application.id))

@recruiter_bp.route('/job/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job(job_id):
    if current_user.role != 'recruiter':
        return redirect(url_for('seeker.dashboard'))
        
    job = Job.query.get_or_404(job_id)
    if job.posted_by != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('recruiter.dashboard'))
        
    db.session.delete(job)
    db.session.commit()
    
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('recruiter.dashboard'))

@recruiter_bp.route('/job/<int:job_id>/extend', methods=['POST'])
@login_required
def extend_deadline(job_id):
    if current_user.role != 'recruiter':
        return redirect(url_for('seeker.dashboard'))
        
    job = Job.query.get_or_404(job_id)
    if job.posted_by != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('recruiter.dashboard'))
        
    new_deadline_str = request.form.get('new_deadline')
    if new_deadline_str:
        job.deadline = datetime.strptime(new_deadline_str, '%Y-%m-%d')
        db.session.commit()
        flash(f'Deadline for {job.title} extended successfully!', 'success')
        
    return redirect(url_for('recruiter.dashboard'))
