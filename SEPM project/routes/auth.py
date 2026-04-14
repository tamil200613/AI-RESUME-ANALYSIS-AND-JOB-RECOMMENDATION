from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        user = User.query.filter_by(email=data.get('email')).first()
        
        if user and user.check_password(data.get('password')):
            login_user(user)
            if user.role == 'recruiter':
                return redirect(url_for('recruiter.dashboard'))
            else:
                return redirect(url_for('seeker.dashboard'))
        flash('Invalid email or password')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        
        # Basic validation
        if User.query.filter_by(email=data.get('email')).first():
            flash('Email already registered')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=data.get('username')).first():
            flash('Username already taken')
            return redirect(url_for('auth.register'))
            
        new_user = User(
            username=data.get('username'),
            email=data.get('email'),
            role=data.get('role', 'seeker') # Default to seeker
        )
        new_user.set_password(data.get('password'))
        
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        if new_user.role == 'recruiter':
            return redirect(url_for('recruiter.dashboard'))
        return redirect(url_for('seeker.dashboard'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
