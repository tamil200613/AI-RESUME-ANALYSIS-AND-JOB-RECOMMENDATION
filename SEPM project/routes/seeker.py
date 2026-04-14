from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from models import db, Job, Resume, Application
import os
from werkzeug.utils import secure_filename
from core.extractor import extract_text_from_pdf, extract_entities
from core.semantic_matcher import calculate_match_score
import json
import google.generativeai as genai
from datetime import datetime, timedelta

seeker_bp = Blueprint('seeker', __name__, url_prefix='/seeker')

def calculate_resume_score(resume):
    """
    Calculates a general 'Strength Score' for a resume (0-100).
    This is different from a match score; it measures how well the resume is built.
    """
    if not resume:
        return 0
    
    score = 0
    # 1. Content Length (up to 30 points)
    length = len(resume.raw_text)
    if length > 2000: score += 30
    elif length > 1000: score += 20
    elif length > 500: score += 10
    
    # 2. Skills Count (up to 40 points)
    try:
        skills = json.loads(resume.extracted_skills or '[]')
        skill_count = len(skills)
        if skill_count >= 10: score += 40
        elif skill_count >= 5: score += 25
        elif skill_count >= 2: score += 10
    except:
        pass
        
    # 3. Completeness (up to 30 points)
    if resume.summary and len(resume.summary) > 50: score += 15
    if resume.education and len(resume.education) > 10: score += 7
    if resume.experience and len(resume.experience) > 10: score += 8
    
    return min(100, score)

@seeker_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'seeker':
        return redirect(url_for('recruiter.dashboard'))
    
    # Get user's active resume
    resume = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.uploaded_at.desc()).first()
    
    strength_score = calculate_resume_score(resume)
    recommended_jobs = []
    latest_jobs = []
    
    # 1. Fetch ALL active jobs and filter expired ones in Python for reliability
    now = datetime.utcnow()
    # Get all active jobs (SQLite date filtering can be inconsistent leading to 'still showing' bugs)
    raw_jobs = Job.query.filter_by(is_active=True).all()
    
    all_active_jobs = []
    for job in raw_jobs:
        # Determine the effective deadline (explicit or 1-day default for legacy jobs)
        effective_deadline = job.deadline or (job.created_at + timedelta(days=1))
        
        # Comparison logic
        if effective_deadline.hour == 0 and effective_deadline.minute == 0:
            # If it's a date-only deadline, it's valid until the day is over
            if effective_deadline.date() < now.date():
                continue
        else:
            # Exact time comparison
            if effective_deadline < now:
                continue
                
        all_active_jobs.append(job)
    
    # 2. If student has a resume, calculate recommendations
    if resume and resume.parsed_status == 'Completed':
        applied_job_ids = [app.job_id for app in Application.query.filter_by(resume_id=resume.id).all()]
        resume_skills = set([s.lower() for s in json.loads(resume.extracted_skills or '[]')])
        
        all_scored_jobs = []
        for job in all_active_jobs:
            if job.id not in applied_job_ids:
                # Calculate match
                score = calculate_match_score(resume.raw_text, job.description + " " + job.required_skills)
                
                job_skills = set([s.strip().lower() for s in job.required_skills.split(',') if s.strip()])
                missing_skills = list(job_skills - resume_skills)
                
                job_data = {
                    'job': job,
                    'score': score,
                    'missing_skills': missing_skills[:3]
                }
                
                all_scored_jobs.append(job_data)
                if score > 20:
                    recommended_jobs.append(job_data)
        
        # Sort recommendations by score
        recommended_jobs.sort(key=lambda x: x['score'], reverse=True)
        recommended_jobs = recommended_jobs[:5]
        
        # Latest jobs (sorted by creation date)
        latest_jobs = sorted(all_scored_jobs, key=lambda x: x['job'].created_at, reverse=True)[:8]
    else:
        # Fallback for students without resumes: show latest active jobs without scores
        latest_jobs = []
        # We need to manually construct the dict structure the template expects
        for job in sorted(all_active_jobs, key=lambda x: x.created_at, reverse=True)[:8]:
            latest_jobs.append({
                'job': job,
                'score': 0, # No score without resume
                'missing_skills': []
            })
        
    return render_template('seeker_dashboard.html', 
                         resume=resume, 
                         recommended_jobs=recommended_jobs, 
                         latest_jobs=latest_jobs,
                         strength_score=strength_score,
                         now=datetime.utcnow())

@seeker_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_resume():
    if current_user.role != 'seeker':
        return redirect(url_for('recruiter.dashboard'))

    if request.method == 'POST':
        if 'resume_file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['resume_file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
            
        if file and (file.filename.endswith('.pdf') or file.filename.endswith('.docx')):
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            
            # In a real app, do this asynchronously. Doing it synchronously here for simplicity
            try:
                if filename.endswith('.pdf'):
                    raw_text = extract_text_from_pdf(filepath)
                else:
                    raw_text = "DOCX extraction not fully implemented here yet." # Simplified
                
                entities = extract_entities(raw_text)
                
                # --- AI SUMMARY GENERATION ---
                summary = "Processing summary..."
                try:
                    # Reuse Gemini API key from chat logic
                    api_key = "AIzaSyAw8xbRhPu0CXzXtFN_8zcW5fzQEcFFtLg"
                    genai.configure(api_key=api_key)
                    
                    # Robust model selection
                    model_name = 'gemini-1.5-flash'
                    try:
                        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                        if available_models:
                            if 'models/gemini-1.5-flash' in available_models:
                                model_name = 'gemini-1.5-flash'
                            elif 'models/gemini-1.5-pro' in available_models:
                                model_name = 'gemini-1.5-pro'
                            else:
                                model_name = available_models[0].replace('models/', '')
                    except:
                        pass
                        
                    model = genai.GenerativeModel(model_name)
                    prompt = (
                        f"Extract a concise professional summary (2 to 3 sentences maximum) from the following resume text. "
                        f"Include years of experience, key roles, technical skills, and career objectives. Do not include personal names.\n\n"
                        f"Resume Text:\n{raw_text[:3000]}"
                    )
                    response = model.generate_content(prompt)
                    if response.text:
                        summary = response.text.strip()
                except Exception as ai_err:
                    print(f"AI Summary failed: {ai_err}")
                    # Fallback to a much shorter snippet if AI fails, to show the summary context
                    summary = raw_text[:300].replace('\n', ' ')
                    if len(raw_text) > 300:
                        summary += "..."
                
                resume = Resume(
                    user_id=current_user.id,
                    filename=filename,
                    raw_text=raw_text,
                    summary=summary,
                    extracted_skills=json.dumps(entities.get('skills', [])),
                    parsed_status='Completed'
                )
                db.session.add(resume)
                db.session.commit()
                flash('Resume uploaded and analyzed successfully!', 'success')
                return redirect(url_for('seeker.dashboard'))
            except Exception as e:
                flash(f'Error processing resume: {str(e)}', 'danger')
                
    return render_template('upload.html')

@seeker_bp.route('/update_summary', methods=['POST'])
@login_required
def update_summary():
    if current_user.role != 'seeker':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    if not data or 'summary' not in data:
        return jsonify({'error': 'Summary text is required'}), 400
        
    resume = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.uploaded_at.desc()).first()
    if not resume:
        return jsonify({'error': 'No resume found'}), 404
        
    resume.summary = data['summary'].strip()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Summary updated successfully'})

@seeker_bp.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    if current_user.role != 'seeker':
        return redirect(url_for('recruiter.dashboard'))
        
    resume = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.uploaded_at.desc()).first()
    if not resume:
        flash('Please upload a resume first.', 'warning')
        return redirect(url_for('seeker.upload_resume'))
        
    job = Job.query.get_or_404(job_id)
    
    # SECURITY: Check deadline again in the backend (Python-side for reliability)
    now = datetime.utcnow()
    effective_deadline = job.deadline or (job.created_at + timedelta(days=1))
    
    if effective_deadline.hour == 0 and effective_deadline.minute == 0:
        if effective_deadline.date() < now.date():
            flash('Sorry, the application deadline for this position has passed.', 'danger')
            return redirect(url_for('seeker.dashboard'))
    elif effective_deadline < now:
        flash('Sorry, the application deadline for this position has passed.', 'danger')
        return redirect(url_for('seeker.dashboard'))
        
    # Check if already applied
    existing_app = Application.query.filter_by(job_id=job.id, resume_id=resume.id).first()
    if existing_app:
        flash('You have already applied to this job.', 'info')
        return redirect(url_for('seeker.dashboard'))
        
    # Calculate score
    score = calculate_match_score(resume.raw_text, job.description + " " + job.required_skills)
    
    # Determine skill gaps
    job_skills = set([s.strip().lower() for s in job.required_skills.split(',') if s.strip()])
    resume_skills = set([s.lower() for s in json.loads(resume.extracted_skills or '[]')])
    missing_skills = list(job_skills - resume_skills)
    
    app = Application(
        job_id=job.id,
        resume_id=resume.id,
        match_score=score,
        skill_gaps=json.dumps(missing_skills),
        status='Applied'
    )
    db.session.add(app)
    db.session.commit()
    
    flash(f'Successfully applied for {job.title}!', 'success')
    return redirect(url_for('seeker.dashboard'))

@seeker_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    if current_user.role != 'seeker':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
        
    user_message = data['message']
    
    # Set API key
    api_key = "AIzaSyAw8xbRhPu0CXzXtFN_8zcW5fzQEcFFtLg"
    if not api_key:
        return jsonify({'error': 'Gemini API key is not configured.'}), 500
        
    try:
        genai.configure(api_key=api_key)
        
        # Robust model selection: Try to find any model that supports generateContent
        # This solves the 404 errors for specific model names.
        model_name = 'gemini-1.5-flash' # Default
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            if available_models:
                # Prioritize flash or pro if they exist in the list
                if 'models/gemini-1.5-flash' in available_models:
                    model_name = 'gemini-1.5-flash'
                elif 'models/gemini-1.5-pro' in available_models:
                    model_name = 'gemini-1.5-pro'
                elif 'models/gemini-pro' in available_models:
                    model_name = 'gemini-pro'
                else:
                    model_name = available_models[0].replace('models/', '')
        except Exception:
            pass # Fallback to default if listing fails
            
        model = genai.GenerativeModel(model_name)
        
        # Get user's resume for context
        resume = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.uploaded_at.desc()).first()
        
        system_prompt = (
            "You are a helpful and professional AI career assistant for a student/job seeker portal. "
            "You can answer general questions and assist with job applications, resume building, and career guidance. "
        )
        
        if resume:
            system_prompt += (
                f"\n\nThe user has uploaded a resume. Here is some content: {resume.raw_text[:2000]}... "
                f"\n\nTheir extracted skills are: {resume.extracted_skills}. "
                "Use this information to provide personalized advice on how they can improve their profile, what skills they should learn, or what roles fit them."
            )
        
        prompt = f"{system_prompt}\n\nUser: {user_message}\nAI Assistant:"
        
        response = model.generate_content(prompt)
        
        if response.text:
            return jsonify({'reply': response.text})
        else:
            return jsonify({'error': 'AI did not return a response.'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

