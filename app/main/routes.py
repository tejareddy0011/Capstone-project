from flask import render_template,jsonify, request, flash, redirect, url_for, send_from_directory,Response
from . import main
from flask_login import current_user, login_required
from app.models import Job, Application, User
from app import db
from werkzeug.utils import secure_filename
import os
from app.cv_parsing import extract_text_from_pdf, extract_skills, calculate_matching_score


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))# Get the absolute path of the current directory
print(BASE_DIR)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'cvs')

print(UPLOAD_FOLDER)
allowed_extensions = {'pdf', 'docx', 'txt'}

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



@main.route('/')
@login_required
def home():
    jobs = Job.query.all()
    # Render the home template and pass the jobs to it
    return render_template('home.html', jobs=jobs)

@main.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    # Get the jobs posted by the current logged-in user
    posted_jobs = Job.query.filter_by(user_id=current_user.id).all()
    
    # Get the most recent 3 applications for those jobs
    recent_applications = Application.query.filter(Application.job_id.in_([job.id for job in posted_jobs])) \
        .order_by(Application.applied_at.desc()) \
        .limit(3).all()

    return render_template('dashboard.html', recent_applications=recent_applications)


@main.route('/api/job_stats')
@login_required
def job_stats():
    if current_user.role.lower() != 'employer':
        return jsonify({'error': 'Unauthorized access'}), 403
    
    employer_jobs = Job.query.join(User).filter(User.id == current_user.id, User.role == 'employer').count()
    
    applicant= Application.query.join(Job).join(User).filter(
    User.id == current_user.id, User.role == 'employer'
        ).count()

    return jsonify({
        'total_active_jobs': employer_jobs,
        'total_applications': applicant,
    
    })



@main.route('/post_job', methods=['POST'])
@login_required
def post_job():
    # Retrieve form data
    title = request.form.get('jobTitle')
    location = request.form.get('jobLocation')
    job_type = request.form.get('jobType')
    description = request.form.get('jobDescription')
    skills = request.form.get("skills")
    experience = request.form.get("experience")

    # Validate form data
    if not (title and location and job_type and description):
        flash("All fields are required!", category='error')
        return redirect(url_for('main.dashboard'))  # Adjust as necessary

    # Create new Job object and save to the database
    new_job = Job(title=title, 
                  location=location, 
                  description=description,
                  company_name=current_user.username,
                  skills= skills, 
                  type=job_type,
                  experience=experience,
                  user_id= current_user.id)
    db.session.add(new_job)
    db.session.commit()
    
    flash("Job posted successfully!", category='success')
    return redirect(url_for('main.dashboard'))  # Redirect back to dashboard

@main.route('/active_jobs')
@login_required
def active_jobs():
    try:
        jobs = Job.query.filter_by(user_id=current_user.id).all()  # Adjust query if necessary
        return render_template('active_job.html', jobs=jobs)
    except Exception as e:
        print(e)
      # Optional: Add an error template


@main.route('/applications', methods=['GET'])
@login_required
def view_job_applications():
    # Ensure the user is an employer
    if current_user.role != 'employer':
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for('main.home'))

    # Get all jobs posted by the current user
    user_jobs = Job.query.filter_by(user_id=current_user.id).all()

    # Fetch applications related to those jobs
    applications = []
    for job in user_jobs:
        job_applications = Application.query.filter_by(job_id=job.id).all()
        applications.extend(job_applications)

    return render_template('employer_applications.html', applications=applications)

    
@main.route('/delete_job/<int:job_id>', methods=['DELETE'])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return jsonify({'message': 'Job deleted successfully'}), 200
    
    
# Route to fetch applicants for a specific job
@main.route('/api/applicants/<int:job_id>')
def get_applicants(job_id):
    try:
        # Fetch applications for the given job ID
        applications = Application.query.filter_by(job_id=job_id).all()

        # Check if there are no applications
        if not applications:
            return jsonify({'applicants': [], 'message': 'No applicants found for this job.'})

        # Extract applicant data
        applicants_data = [
            {
                'name': application.user.username,  # Assuming 'username' field exists in User model
                'email': application.user.email     # Assuming 'email' field exists in User model
            }
            for application in applications
        ]

        return jsonify({'applicants': applicants_data})

    except Exception as e:
        # Handle any unexpected errors
        return jsonify({'error': str(e)}), 500



@main.route('/uploads/cvs/<filename>')
def serve_cv(filename):
    directory = UPLOAD_FOLDER
    file_path = os.path.join(directory, filename)
    
    if not os.path.exists(file_path):
        return 0  # Return 404 if file doesn't exist

    file_extension = os.path.splitext(filename)[1].lower()

    # Define the MIME type based on the file extension
    mime_types = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain'
    }
    
    mime_type = mime_types.get(file_extension, 'application/octet-stream')

    # Open the file and return it as a response with inline content disposition
    with open(file_path, 'rb') as f:
        content = f.read()

    response = Response(content, mimetype=mime_type)
    response.headers['Content-Disposition'] = 'inline; filename=' + filename

    return response


@main.route('/apply', methods=['POST'])
@login_required
def apply_for_job():
    job_id = request.form.get('job_id')
    job = Job.query.get_or_404(job_id)  # Get the job using the job_id

    # Check if file is part of the request
    if 'cv' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('home'))

    file = request.files['cv']

    # If the user doesn't select a file
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('home'))

    
    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
        file_extension = os.path.splitext(file.filename)[1]
        # filename = secure_filename(current_user.email)
        filename = f"{current_user.email}{file_extension}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Save the application record (assumes you have an Application model)
        application = Application(user_id=current_user.id, job_id=job.id, cv_filename=filename)
        db.session.add(application)
        db.session.commit()

        flash('Application submitted successfully!', 'success')
        return redirect(url_for('main.home'))
    else:
        flash('Invalid file type. Please upload a PDF, DOCX, or TXT file.', 'error')
        return redirect(url_for('main.home'))
    


@main.route('/applied-jobs')
@login_required
def applied_jobs():
    # Query the Application model to get all applications for the current user
    user_applications = Application.query.filter_by(user_id=current_user.id).join(Job).all()
    
    # Extract the associated job information for each application
    applied_jobs = []
    for application in user_applications:
        applied_jobs.append({
            'title': application.job_listing.title,
            'company_name': application.job_listing.company_name,
            'location': application.job_listing.location,
            'applied_date': application.applied_at,
            'description': application.job_listing.description,
            'job_id': application.job_listing.id
        })

    return render_template('profile.html', applied_jobs=applied_jobs)






# Route to shortlist candidates for a particular job
@main.route('/shortlist/<int:job_id>', methods=['POST'])
@login_required
def shortlist_candidates(job_id):
    # Get the job
    job = Job.query.get_or_404(job_id)
    
    # Define the target skills for the job (this can be set dynamically based on the job's data)
    target_skills = job.skills.split(",")  # Assuming the skills are stored as a comma-separated string
    
    print(job.skills)
    # Get all applications for the job
    applications = Application.query.filter_by(job_id=job_id).all()
    
    shortlisted_candidates = []
    
    try:
        # Process each application
        for application in applications:
            # Get the CV filename and path
            cv_filename = application.cv_filename
            cv_path = os.path.join(UPLOAD_FOLDER, cv_filename)

            # Extract text from the CV
            resume_text = extract_text_from_pdf(cv_path)
            
            # Extract skills from the resume
            skills_found = extract_skills(resume_text)
            
            print(skills_found)
            print(target_skills)
            # Calculate the matching score
            score = calculate_matching_score(skills_found, target_skills)
            
            # Add the candidate to the shortlist with score
            shortlisted_candidates.append({
                'candidate': application.user.username,
                'score': score,
                'cv_filename': cv_filename
            })
    except:
        pass

    # Sort candidates by score
    shortlisted_candidates = sorted(shortlisted_candidates, key=lambda x: x['score'], reverse=True)
    
    # Render the results (you can create a template to show these results)
    return render_template('shortlisted_candidates.html', job=job, candidates=shortlisted_candidates)


