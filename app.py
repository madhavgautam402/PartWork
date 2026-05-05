from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import database as db
from skills import MASTER_SKILLS, indian_cities_by_state
import uuid
import os
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = db.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM User WHERE Email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['Password'], password):
            session['user_id'] = user['UserID']
            session['role'] = user['Role'].lower()
            
            # Fetch the Role-specific ID (EmployerID or StudentID)
            role_data = db.verify_user(user['UserID'], session['role'])
            if session['role'] == 'employer':
                session['employer_id'] = role_data['EmployerID']
            else:
                session['student_id'] = role_data['StudentID']
                
            return redirect(url_for('home'))
        
        flash("Invalid email or password.")
    return render_template('login.html')

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    role = data.get('role')
    email = data.get('email')
    password = data.get('password')
    
    # Pack extra fields based on role
    extra_data = {}
    if role == 'student':
        extra_data = {
            'fname': data.get('fname'),
            'lname': data.get('lname'),
            'uni': data.get('uni'),
            'zip': data.get('zip')
        }
    else:
        extra_data = {'biz_name': data.get('biz_name')}

    success, msg = db.register_user(email, password, role, extra_data)
    if success:
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': msg})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ==========================================
# CORE NAVIGATION ROUTES
# ==========================================
@app.route('/')
@app.route('/home')
def home():
    if 'user_id' not in session: return redirect(url_for('login'))
        
    user_id = session['user_id']
    if session.get('role') == 'employer':
        # Fetch the employer profile so the template doesn't crash!
        profile = db.get_employer_profile(user_id)
        
        postings, trust_score = db.get_employer_data(user_id)
        active_jobs = [p for p in postings if p['Status'] == 'Active']
        total_apps = sum([p['AppCount'] for p in postings])
        
        return render_template('home_employer.html', profile=profile, postings=active_jobs, trust_score=trust_score, total_apps=total_apps)
    else:
        profile = db.get_student_profile(user_id)
        
        jobs = db.get_personalized_feed(user_id)
        if not jobs: jobs = db.get_all_active_jobs()
        jobs = jobs[:4]
        
        conn = db.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        for job in jobs:
            cursor.execute("SELECT Skill FROM RequiredSkills WHERE OppID = %s", (job['OppID'],))
            job['Skills'] = [s['Skill'] for s in cursor.fetchall()]
        cursor.close()
        conn.close()
        return render_template('home_student.html', profile=profile, jobs=jobs)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: 
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    role = session.get('role')
    
    if role == 'employer':
        profile = db.get_employer_profile(user_id)
        if not profile:
            session.clear()
            flash("Profile not found. Please log in again.")
            return redirect(url_for('login'))
            
        payment_token = db.get_payment_token(user_id, 'employer')
        return render_template('dashboard_employer.html', profile=profile, payment_token=payment_token)
        
    else:
        profile = db.get_student_profile(user_id)
        if not profile:
            session.clear()
            flash("Profile not found. Please log in again.")
            return redirect(url_for('login'))
            
        payment_token = db.get_payment_token(user_id, 'student')
        return render_template('dashboard_student.html', profile=profile, payment_token=payment_token, skills_list=MASTER_SKILLS)
# ==========================================
# STUDENT ROUTES
# ==========================================
@app.route('/find_work', methods=['GET'])
def find_work():
    selected_types = request.args.getlist('jobType')
    selected_comps = request.args.getlist('compensation')
    selected_skills = request.args.getlist('skill')
    keyword = request.args.get('q')
    location = request.args.get('loc')
    sort_by = request.args.get('sort', 'latest')

    jobs = db.get_filtered_jobs(selected_types, selected_comps, selected_skills, keyword, location, sort_by)
    return render_template('find_work.html', jobs=jobs, all_skills=MASTER_SKILLS, selected_types=selected_types, selected_comps=selected_comps, selected_skills=selected_skills)

@app.route('/job/<int:opp_id>')
def job_details(opp_id):
    student_id = session.get('user_id')
    job = db.get_job_details(opp_id, student_id)
    if not job: return "Opportunity not found", 404
    return render_template('job_details.html', job=job)

@app.route('/applications')
def applications():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
        
    student_id = session.get('student_id')
    
    # Existing call to get standard applications
    apps = db.get_student_applications(student_id) 
    
    # NEW: Call to get VIP invitations
    invitations = db.get_student_invitations(student_id)
    
    return render_template('applications.html', apps=apps, invitations=invitations)


# NEW API ROUTE for the Accept/Decline buttons
@app.route('/api/respond_invite', methods=['POST'])
def api_respond_invite():
    if session.get('role') != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.json
    invite_id = data.get('invite_id')
    opp_id = data.get('opp_id')
    action = data.get('action') # Will be 'Accept' or 'Decline'
    student_id = session.get('student_id')

    if not all([invite_id, opp_id, action, student_id]):
        return jsonify({'success': False, 'message': 'Missing data'}), 400

    success, message = db.respond_to_invitation(invite_id, opp_id, student_id, action)
    
    return jsonify({'success': success, 'message': message})

@app.route('/my_projects')
def my_projects():
    if 'user_id' not in session or session.get('role') != 'student': return redirect(url_for('login'))
    projects = db.get_active_projects(session['user_id'], 'student')
    return render_template('my_projects.html', projects=projects)

# ==========================================
# EMPLOYER ROUTES
# ==========================================
@app.route('/hire_students', methods=['GET'])
def hire_students():
    # 1. Security / Authentication Check
    if 'user_id' not in session or session.get('role') != 'employer':
        return redirect(url_for('login')) # Adjust this to your actual login route
    
    employer_id = session.get('employer_id')
    
    # 2. Grab Sidebar Filter Parameters from the URL
    search_query = request.args.get('q', '').strip()
    location_query = request.args.get('loc', '').strip()
    # request.args.getlist() automatically grabs all checked boxes with name="skill" and puts them in a Python list
    selected_skills = request.args.getlist('skill') 
    
    # 3. Clean Database Calls
    # Assuming you have a function that takes these filters and returns matching students
    students = db.get_filtered_students(search_query, location_query, selected_skills)
    
    # Get the employer's active jobs for the "Invite to Project" dropdown
    active_jobs = db.get_active_jobs_for_employer(employer_id)
    # 4. Render the UI
    return render_template(
        'hire_students.html',
        students=students,
        all_skills=MASTER_SKILLS,
        selected_skills=selected_skills,
        active_jobs=active_jobs
    )

@app.route('/student/<int:student_id>')
def student_profile(student_id):
    if 'user_id' not in session or session.get('role') != 'employer': return redirect(url_for('login'))
    profile = db.get_student_profile(student_id)
    if not profile: return "Student not found", 404
    return render_template('student_profile.html', profile=profile)

@app.route('/manage_projects')
def manage_projects():
    if 'user_id' not in session or session.get('role') != 'employer': return redirect(url_for('login'))
    postings, _ = db.get_employer_data(session['user_id'])
    active_postings = [p for p in postings if p['Status'] != 'Completed']
    completed_postings = [p for p in postings if p['Status'] == 'Completed']
    return render_template('manage_projects.html', active=active_postings, completed=completed_postings)

@app.route('/manage_job/<int:opp_id>')
def manage_job(opp_id):
    if 'user_id' not in session or session.get('role') != 'employer': return redirect(url_for('login'))
    job = db.get_job_details(opp_id)
    applicants = db.get_app_details(opp_id)
    if not job: return "Opportunity not found", 404
    return render_template('manage_job.html', job=job, applicants=applicants, skills_list=MASTER_SKILLS, city_data=indian_cities_by_state)

@app.route('/post_job')
def post_job():
    if 'user_id' not in session or session.get('role') != 'employer': return redirect(url_for('login'))
    return render_template('post_job.html', skills_list=MASTER_SKILLS, city_data=indian_cities_by_state)

@app.route('/api/invite_student', methods=['POST'])
def invite_student():
    # Security check
    if session.get('role') != 'employer':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.json
    student_id = data.get('student_id')
    opp_id = data.get('opp_id')
    message = data.get('message')
    employer_id = session.get('employer_id')

    if not student_id or not opp_id:
        return jsonify({'success': False, 'message': 'Missing data'}), 400

    # Call the database function
    success, return_message = db.create_project_invitation(opp_id, employer_id, student_id, message)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': return_message}), 400

# ==========================================
# API ROUTES
# ==========================================
@app.route('/api/update_employer', methods=['POST'])
def update_employer():
    if session.get('role') != 'employer':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    employer_id = session.get('employer_id')
    data = request.json
    
    business_name = data.get('business_name')
    email = data.get('email')
    password = data.get('password') 

    if not business_name or not email:
        return jsonify({'success': False, 'message': 'Business Name and Email are required.'}), 400

    success, message = db.update_employer_profile(employer_id, business_name, email, password)
    return jsonify({'success': success, 'message': message})

@app.route('/api/filter_jobs', methods=['GET'])
def api_filter_jobs():
    selected_types = request.args.getlist('jobType')
    selected_comps = request.args.getlist('compensation')
    selected_skills = request.args.getlist('skill')
    keyword = request.args.get('q') 
    location = request.args.get('loc') 
    sort_by = request.args.get('sort', 'latest') 
    jobs = db.get_filtered_jobs(selected_types, selected_comps, selected_skills, keyword, location, sort_by)
    return jsonify(jobs)

@app.route('/api/apply', methods=['POST'])
def api_apply():
    if 'user_id' not in session or session.get('role') != 'student': return jsonify({'success': False, 'message': 'You must be logged in as a student to apply.'})
    data = request.get_json()
    success, msg = db.apply_for_job(session['user_id'], data.get('opp_id'))
    return jsonify({'success': success, 'message': msg})

@app.route('/api/update_skills', methods=['POST'])
def api_update_skills():
    if 'user_id' not in session or session.get('role') != 'student': 
        return jsonify({'success': False})
    
    data = request.get_json()
    skills_array = data.get('skills', []) 
    
    if db.update_student_skills(session['user_id'], skills_array):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Database error saving skills.'})

@app.route('/api/save_payment', methods=['POST'])
def api_save_payment():
    if 'user_id' not in session: return jsonify({'success': False})
    role = session.get('role')
    token = request.get_json().get('token', '').strip()
    if token and db.save_payment_token(session['user_id'], role, token): 
        return jsonify({'success': True, 'message': 'Payment method saved successfully!'})
    return jsonify({'success': False, 'message': 'Database error.'})

@app.route('/api/generate_payment', methods=['POST'])
def api_generate_payment():
    if 'user_id' not in session: return jsonify({'success': False})
    role = session.get('role')
    secure_token = f"PW-WALLET-{uuid.uuid4().hex[:12].upper()}"
    if db.save_payment_token(session['user_id'], role, secure_token): 
        return jsonify({'success': True, 'token': secure_token, 'message': 'Escrow wallet generated!'})
    return jsonify({'success': False, 'message': 'Database error.'})

@app.route('/api/update_profile', methods=['POST'])
def api_update_profile():
    if 'user_id' not in session or session.get('role') != 'student': return jsonify({'success': False})
    data = request.get_json()
    if db.update_student_profile(session['user_id'], data.get('city'), data.get('state'), data.get('zipcode'), data.get('street')): return jsonify({'success': True, 'message': 'Profile updated successfully!'})
    return jsonify({'success': False, 'message': 'Failed to update profile.'})

@app.route('/api/edit_job', methods=['POST'])
def api_edit_job():
    if 'user_id' not in session or session.get('role') != 'employer': return jsonify({'success': False, 'message': 'Unauthorized'})
    data = request.get_json()
    if db.edit_job(data.get('opp_id'), data.get('title'), data.get('type'), data.get('req_students'), data.get('city'), data.get('state'), data.get('skills', []), data.get('desc')): 
        return jsonify({'success': True, 'message': 'Job updated successfully!'})
    return jsonify({'success': False, 'message': 'Failed to update job.'})

@app.route('/api/accept_applicant', methods=['POST'])
def api_accept_applicant():
    if 'user_id' not in session or session.get('role') != 'employer': return jsonify({'success': False, 'message': 'Unauthorized'})
    if db.accept_application(request.get_json().get('app_id')): return jsonify({'success': True, 'message': 'Applicant Accepted! Job is now Assigned.'})
    return jsonify({'success': False, 'message': 'Error accepting applicant.'})

@app.route('/api/post_job', methods=['POST'])
def api_post_job():
    if 'user_id' not in session or session.get('role') != 'employer': return jsonify({'success': False, 'message': 'Unauthorized'})
    data = request.get_json()
    success, msg = db.create_job_post(session['user_id'], data['title'], data['type'], data['req_students'], data['city'], data['state'], data['skills'], data['desc'], data['funds'], data['milestones'])
    return jsonify({'success': success, 'message': msg})

@app.route('/api/verify_identity', methods=['POST'])
def api_verify_identity():
    if session.get('role') != 'employer': return jsonify({'success': False})
    
    if db.verify_employer_identity(session.get('employer_id')): 
        return jsonify({'success': True, 'message': 'Identity Verified Successfully!'})
    return jsonify({'success': False, 'message': 'Verification Failed.'})

@app.route('/api/submit_milestone', methods=['POST'])
def api_submit_milestone():
    if 'user_id' not in session or session.get('role') != 'student': return jsonify({'success': False})
    milestone_id = request.get_json().get('milestone_id')
    if db.submit_milestone_work(milestone_id): return jsonify({'success': True, 'message': 'Work submitted for review!'})
    return jsonify({'success': False, 'message': 'Error submitting work.'})

@app.route('/api/approve_milestone', methods=['POST'])
def api_approve_milestone():
    if 'user_id' not in session or session.get('role') != 'employer':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    data = request.get_json()
    success, job_completed, app_id = db.approve_milestone(data['milestone_id'], data['opp_id'])
    if success:
        return jsonify({'success': True, 'job_completed': job_completed})
    else:
        return jsonify({'success': False, 'message': 'Database error while approving.'})

@app.route('/api/reject_milestone', methods=['POST'])
def api_reject_milestone():
    if 'user_id' not in session or session.get('role') != 'employer': return jsonify({'success': False})
    if db.reject_milestone(request.get_json().get('milestone_id')): return jsonify({'success': True, 'message': 'Milestone rejected. Sent back to student.'})
    return jsonify({'success': False, 'message': 'Error rejecting milestone.'})

@app.route('/api/edit_milestone', methods=['POST'])
def api_edit_milestone():
    if 'user_id' not in session or session.get('role') != 'employer': return jsonify({'success': False})
    data = request.get_json()
    if db.edit_milestone(data['milestone_id'], data['desc'], data['payout'], data['deadline']): return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/post_feedback', methods=['POST'])
def api_post_feedback():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    success = db.post_feedback(
        data.get('app_id'), 
        session.get('role').capitalize(), # 'Employer' or 'Student'
        data.get('metric'), 
        data.get('score'), 
        data.get('comment')
    )
    return jsonify({'success': success})

@app.route('/api/refute_feedback', methods=['POST'])
def api_refute_feedback():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
        
    data = request.get_json()
    record_id = data.get('record_id')
    
    success = db.refute_feedback(record_id)
    return jsonify({'success': success})

@app.route('/api/complete_and_rate', methods=['POST'])
def api_complete_and_rate():
    data = request.get_json()
    opp_id = data.get('opp_id')
    ratings = data.get('ratings')
    role = session.get('role').capitalize()
    
    success = db.complete_project_and_rate(opp_id, role, ratings)
    return jsonify({'success': success})

@app.route('/api/send_message', methods=['POST'])
def api_send_message():
    if 'user_id' not in session: return jsonify({'success': False})
    
    data = request.get_json()
    opp_id = data.get('opp_id')
    message = data.get('message')
    role = session.get('role').capitalize()
    
    if role == 'Employer':
        name = db.get_employer_profile(session['user_id'])['BusinessName']
    else:
        name = db.get_student_profile(session['user_id'])['FirstName']
    
    if db.send_message(opp_id, name, role, message):
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/get_messages/<int:opp_id>')
def api_get_messages(opp_id):
    if 'user_id' not in session: return jsonify({'messages': []})
    
    messages = db.get_chat_messages(opp_id)
    
    if session.get('role') == 'employer':
        my_name = db.get_employer_profile(session['user_id'])['BusinessName']
    else:
        my_name = db.get_student_profile(session['user_id'])['FirstName']
        
    return jsonify({
        'messages': messages, 
        'my_name': my_name 
    })

@app.route('/api/schedule_interview', methods=['POST'])
def api_schedule_interview():
    if 'user_id' not in session or session.get('role') != 'employer': 
        return jsonify({'success': False, 'message': 'Unauthorized'})
        
    data = request.get_json()
    success, msg = db.schedule_interview(
        data.get('app_id'), 
        data.get('scheduled_time'), 
        data.get('meeting_type'),
        data.get('meeting_link')
    )
    return jsonify({'success': success, 'message': msg})

if __name__ == '__main__':
    app.run(debug=True)