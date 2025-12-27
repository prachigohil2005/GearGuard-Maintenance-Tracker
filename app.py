from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_required, current_user
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Import models after app initialization
from models import db, User

# Initialize database
db.init_app(app)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import and register blueprints
from routes.auth import auth_bp
from routes.equipment import equipment_bp
from routes.requests import requests_bp
from routes.teams import teams_bp
from routes.dashboard import dashboard_bp

app.register_blueprint(auth_bp)
app.register_blueprint(equipment_bp)
app.register_blueprint(requests_bp)
app.register_blueprint(teams_bp)
app.register_blueprint(dashboard_bp)

# Context processor for global variables
@app.context_processor
def inject_user():
    return dict(current_user=current_user, now=datetime.now())

# Home route
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

# Create tables and seed data
def init_db():
    with app.app_context():
        db.create_all()
        
        # Check if we need to seed data
        if User.query.count() == 0:
            from seed_data import seed_database
            seed_database()
            print("✅ Database seeded successfully!")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
