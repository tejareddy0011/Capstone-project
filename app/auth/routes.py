from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt  # Import db and bcrypt from the app level to avoid circular import
from app.models import User
from . import auth


class AdminUser:
    def __init__(self):
        self.id = 1
        self.username = "admin"
        self.email = "admin@gmail.com"
        self.role = "admin"

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False
    
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        # Check if the email is already registered
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', category='error')
        else:
            new_user = User(username=username, email=email, role = role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! Please log in.', category='success')
            return redirect(url_for('auth.login'))
    return render_template('signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        
                # Check for admin login
        if email == "admin@gmail.com" and password == "admin":
            # Create a mock admin user with static info and log them in



            admin_user = AdminUser()
            login_user(admin_user)
            flash('Login successful as admin!', category='success')
            return redirect(url_for("admin.admin_dashboard"))
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', category='success')
            
            if user.role.lower() == "employer":
                return redirect(url_for('main.dashboard'))  # Adjust route as needed
            if user.role.lower() == "job_seeker":
                return redirect(url_for('main.home'))
            if user.role.lower() == "admin":
                return redirect(url_for("admin.dashboard"))
        else:
            flash('Invalid email or password', category='error')
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', category='success')
    return redirect(url_for('auth.login'))

@auth.route('/dashboard')
@login_required
def dashboard():
    return f"Welcome, {current_user.username}! This is your dashboard."
