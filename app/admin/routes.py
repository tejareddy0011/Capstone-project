from flask import render_template, redirect, url_for
from . import admin
from flask_login import current_user, login_required
from app.models import Application, User, Job
from app import db

@admin.route('/admin_dashboard')
@login_required
def admin_dashboard():
    
    print(current_user.username)
    
    # You can replace the below with actual data from your database
    active_users = User.query.count()# Example count, should be fetched from the User model
    job_postings = Job.query.count()  # Example count, should be fetched from the Job model
    applicants = Application.query.count()  # Example revenue, calculate based on your business logic

    users = User.query.all()
    jobs = Job.query.all()

    return render_template(
        'admin_dashboard.html',
        active_users=active_users,
        job_postings=job_postings,
        applicants = applicants, 
        users = users,
        jobs = jobs
    )



@admin.route("/delete-user/<id>")
@login_required
def delete_user(id):
    user = User.query.filter_by(id=id).first()
    db.session.delete(user)
    db.session.commit()
    
    return redirect(url_for('admin.admin_dashboard'))
    
    
@admin.route('/delete_job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return redirect(url_for('admin.admin_dashboard'))