from flask_login import UserMixin
from app.extensions import db, bcrypt
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(255), default="User")
    # Establish relationship with Job model with cascade delete
    jobs = db.relationship('Job', backref='user', cascade='all, delete-orphan')

    # Relationship with Application model with cascade delete
    applications = db.relationship('Application', backref='applicant', cascade='all, delete-orphan', lazy=True)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100))
    company_name = db.Column(db.String(100))
    type = db.Column(db.String(255))
    experience = db.Column(db.String(255))
    skills = db.Column(db.Text, nullable=False, default="testing")
    
    # Foreign key referencing the user who created the job
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', name='fk_jobs_user_id'), 
        nullable=False
    )

    # Relationship with Application model with cascade delete
    applications = db.relationship('Application', backref='job_listing', lazy=True, cascade='all, delete-orphan')


class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_applications_user_id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', name='fk_applications_job_id'), nullable=False)
    cv_filename = db.Column(db.String(256), nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with User model
    user = db.relationship('User', backref=db.backref('user_applications', lazy=True))

    # Relationship with Job model
    job = db.relationship('Job', backref=db.backref('job_applications', lazy=True))
