import os
from flask import Flask, render_template

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'enterprise-ats-secret-key-999'
    
    # Configure SQLite database
    basedir = os.path.abspath(os.path.dirname(__name__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'ats_platform.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    from models import db, login_manager
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from routes.auth import auth_bp
    from routes.seeker import seeker_bp
    from routes.recruiter import recruiter_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(seeker_bp)
    app.register_blueprint(recruiter_bp)
    app.register_blueprint(admin_bp)

    @app.route('/')
    def index():
        return render_template('base.html')

    with app.app_context():
        # Ensure the database and tables are created
        db.create_all()
        
        # Ensure an admin account exists
        from models import User
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin = User(username='admin', email='admin@ats.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin account created: admin / admin123")
        
        # Manual migration for 'summary' column if it's missing (db.create_all doesn't update existing tables)
        try:
            import sqlite3
            db_path = os.path.join(basedir, 'ats_platform.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(resume)")
            columns = [c[1] for c in cursor.fetchall()]
            if 'summary' not in columns:
                cursor.execute("ALTER TABLE resume ADD COLUMN summary TEXT")
                conn.commit()
            conn.close()
        except Exception as e:
            # Silently fail if it's not a dev environment or other issues
            print(f"Skipping manual migration check: {e}")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
