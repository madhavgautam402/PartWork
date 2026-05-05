import mysql.connector
import hashlib
import time
from datetime import datetime
from werkzeug.security import generate_password_hash

def get_db_connection():
    return mysql.connector.connect(
        host='localhost', user='root', password='root123', database='jobdb'
    )

# ==========================================
# PAYMENT / WALLET FUNCTIONS
# ==========================================
def save_payment_token(user_id, user_type, token):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if user_type == "student":
            cursor.execute("SELECT payout_method_id FROM Student_Payout_Method WHERE student_id = %s", (user_id,))
            if cursor.fetchone():
                cursor.execute("UPDATE Student_Payout_Method SET payout_token = %s WHERE student_id = %s", (token, user_id))
            else:
                cursor.execute("INSERT INTO Student_Payout_Method (student_id, method_type, payout_token) VALUES (%s, 'DigitalWallet', %s)", (user_id, token))
        else:
            cursor.execute("SELECT payment_method_id FROM Employer_Payment_Method WHERE employer_id = %s", (user_id,))
            if cursor.fetchone():
                cursor.execute("UPDATE Employer_Payment_Method SET payment_token = %s WHERE employer_id = %s", (token, user_id))
            else:
                cursor.execute("INSERT INTO Employer_Payment_Method (employer_id, method_type, payment_token) VALUES (%s, 'CreditCard', %s)", (user_id, token))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Payment Save Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_payment_token(user_id, user_type):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if user_type == "student":
        cursor.execute("SELECT payout_token AS Token FROM Student_Payout_Method WHERE student_id = %s", (user_id,))
    else:
        cursor.execute("SELECT payment_token AS Token FROM Employer_Payment_Method WHERE employer_id = %s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row['Token'] if row else None


# ==========================================
# USER & PROFILE FUNCTIONS
# ==========================================
def register_user(email, password, role, extra_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Start Transaction
        conn.start_transaction()

        # 2. Hash Password and Insert into User Table
        print(password)
        hashed_pw = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO User (Email, Password, Role) VALUES (%s, %s, %s)",
            (email, hashed_pw, role.capitalize())
        )
        user_id = cursor.lastrowid

        # 3. Insert into Role-Specific Table
        if role.lower() == 'student':
            cursor.execute("""
                INSERT INTO Student (UserID, FirstName, LastName, AcademicAffiliation, Zipcode)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, extra_data['fname'], extra_data['lname'], 
                  extra_data['uni'], extra_data['zip']))
        
        elif role.lower() == 'employer':
            cursor.execute("""
                INSERT INTO Employer (UserID, BusinessName)
                VALUES (%s, %s)
            """, (user_id, extra_data['biz_name']))

        conn.commit()
        return True, "Registration successful!"
    except Exception as e:
        conn.rollback()
        print(f"Registration Error: {e}")
        return False, "Email already exists or data invalid."
    finally:
        cursor.close()
        conn.close()


def verify_user(user_id, user_type):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Map the table and column names based on user_type
    table = "Student" if user_type == "student" else "Employer"
    id_col = "StudentID" if user_type == "student" else "EmployerID"
    query = f"SELECT * FROM {table} WHERE {id_col} = %s"
    
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    if user:
        if user_type == "student":
            user['student_id'] = user['StudentID']
        else:
            user['employer_id'] = user['EmployerID']
            
    return user

def get_student_profile(student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Student WHERE StudentID = %s", (student_id,))
    profile = cursor.fetchone()
    if profile:
        cursor.execute("SELECT Skill FROM SkillTags WHERE StudentID = %s", (student_id,))
        profile['Skills'] = [s['Skill'] for s in cursor.fetchall()]
    cursor.close()
    conn.close()
    return profile

def get_employer_profile(employer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch using EmployerID, JOIN to get the email from User table
        cursor.execute("""
            SELECT e.BusinessName, u.Email, e.VerifiedIdentity, e.TrustScore 
            FROM Employer e
            JOIN User u ON e.UserID = u.UserID 
            WHERE e.EmployerID = %s
        """, (employer_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching employer profile: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_student_profile(student_id, city, state, zipcode, street):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Student 
            SET City = %s, State = %s, Zipcode = %s, Street = %s 
            WHERE StudentID = %s
        """, (city, state, zipcode, street, student_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Profile Update Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def update_employer_profile(employer_id, business_name, email, password=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Update Employer table using EmployerID
        cursor.execute("UPDATE Employer SET BusinessName = %s WHERE EmployerID = %s", (business_name, employer_id))

        # 2. Update User table by JOINing through EmployerID
        if password and len(password.strip()) > 0:
            cursor.execute("""
                UPDATE User u
                JOIN Employer e ON u.UserID = e.UserID
                SET u.Email = %s, u.Password = %s 
                WHERE e.EmployerID = %s
            """, (email, password, employer_id))
        else:
            cursor.execute("""
                UPDATE User u
                JOIN Employer e ON u.UserID = e.UserID
                SET u.Email = %s 
                WHERE e.EmployerID = %s
            """, (email, employer_id))

        conn.commit()
        return True, "Profile updated successfully!"
    except Exception as e:
        conn.rollback()
        print(f"Error updating employer profile: {e}")
        return False, "Database error occurred while updating profile."
    finally:
        cursor.close()
        conn.close()
        return True, "Profile updated successfully!"


def verify_employer_identity(employer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Employer SET VerifiedIdentity = 'Y' WHERE EmployerID = %s", (employer_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Verify Identity Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def add_student_skill(student_id, skill):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM SkillTags WHERE StudentID = %s AND Skill = %s", (student_id, skill))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO SkillTags (StudentID, Skill) VALUES (%s, %s)", (student_id, skill))
            conn.commit()
        success = True
    except Exception as e:
        conn.rollback()
        print(f"Add Skill Error: {e}")
        success = False
    finally:
        cursor.close()
        conn.close()
    return success

def update_student_skills(student_id, skills_array):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM SkillTags WHERE StudentID = %s", (student_id,))
        for skill in skills_array:
            cursor.execute("INSERT INTO SkillTags (StudentID, Skill) VALUES (%s, %s)", (student_id, skill))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Skill Update Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


# ==========================================
# JOB LISTING & FILTERING
# ==========================================
def get_personalized_feed(student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT DISTINCT O.*, E.BusinessName FROM Opportunity O JOIN Posts P ON O.OppID = P.OppID
        JOIN Employer E ON P.EmployerID = E.EmployerID JOIN RequiredSkills RS ON O.OppID = RS.OppID JOIN Student S ON S.Zipcode = O.Zipcode
        WHERE S.StudentID = %s AND RS.Skill IN (SELECT Skill FROM SkillTags WHERE StudentID = %s) AND O.Status = 'Active';
    """
    cursor.execute(sql, (student_id, student_id))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_all_active_jobs():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT O.*, E.BusinessName FROM Opportunity O JOIN Posts P ON O.OppID = P.OppID JOIN Employer E ON P.EmployerID = E.EmployerID WHERE O.Status = 'Active' ORDER BY O.OppID DESC")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_all_unique_skills():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT RS.Skill FROM RequiredSkills RS
        JOIN Opportunity O ON RS.OppID = O.OppID
        WHERE O.Status = 'Active' ORDER BY RS.Skill ASC
    """)
    skills = [row['Skill'] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return skills

def get_filtered_jobs(job_types=None, compensations=None, skills=None, keyword=None, location=None, sort_by="latest"):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT DISTINCT O.*, E.BusinessName, COALESCE(PW.TotalAmount, 0) as WalletAmount
        FROM Opportunity O JOIN Posts P ON O.OppID = P.OppID 
        JOIN Employer E ON P.EmployerID = E.EmployerID LEFT JOIN ProjWallet PW ON O.OppID = PW.OppID
        WHERE O.Status = 'Active'
    """
    params = []

    if keyword:
        sql += " AND (O.RoleTitle LIKE %s OR O.Description LIKE %s OR E.BusinessName LIKE %s)"
        params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
    if location and location != "Any":
        sql += " AND O.State = %s"
        params.append(location)
    if job_types:
        placeholders = ', '.join(['%s'] * len(job_types))
        sql += f" AND O.Type IN ({placeholders})"
        params.extend(job_types)
    if compensations:
        comp_conditions = []
        if 'Paid' in compensations: comp_conditions.append("PW.TotalAmount > 0")
        if 'Unpaid' in compensations: comp_conditions.append("PW.TotalAmount = 0 OR PW.TotalAmount IS NULL")
        if comp_conditions: sql += f" AND ({' OR '.join(comp_conditions)})"
    if skills:
        placeholders = ', '.join(['%s'] * len(skills))
        sql += f" AND O.OppID IN (SELECT OppID FROM RequiredSkills WHERE Skill IN ({placeholders}))"
        params.extend(skills)

    if sort_by == 'wallet_desc': sql += " ORDER BY WalletAmount DESC, O.OppID DESC"
    elif sort_by == 'wallet_asc': sql += " ORDER BY WalletAmount ASC, O.OppID DESC"
    elif sort_by == 'oldest': sql += " ORDER BY O.OppID ASC"
    else: sql += " ORDER BY O.OppID DESC"

    cursor.execute(sql, tuple(params))
    results = cursor.fetchall()
    
    for job in results:
        cursor.execute("SELECT Skill FROM RequiredSkills WHERE OppID = %s", (job['OppID'],))
        job['Skills'] = [s['Skill'] for s in cursor.fetchall()]

    cursor.close()
    conn.close()
    return results

def get_filtered_students(keyword=None, location=None, skills=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Base query: using DISTINCT to avoid duplicates if a student matches multiple skills
    query = "SELECT DISTINCT s.* FROM Student s"
    
    # If skills are provided, we need to JOIN with SkillTags
    if skills:
        query += " JOIN SkillTags st ON s.StudentID = st.StudentID"
    
    query += " WHERE 1=1"
    params = []

    # Filter by Name or University
    if keyword:
        query += " AND (s.FirstName LIKE %s OR s.LastName LIKE %s OR s.AcademicAffiliation LIKE %s)"
        search_term = f"%{keyword}%"
        params.extend([search_term, search_term, search_term])

    # Filter by Location
    if location:
        query += " AND (s.City LIKE %s OR s.State LIKE %s)"
        loc_term = f"%{location}%"
        params.extend([loc_term, loc_term])

    # Filter by Skills
    if skills:
        # Creates a string like '%s, %s, %s' based on list length
        format_strings = ','.join(['%s'] * len(skills))
        query += f" AND st.Skill IN ({format_strings})"
        params.extend(skills)
        
    cursor.execute(query, tuple(params))
    students = cursor.fetchall()
    
    # Attach skills to each student object for the UI tags
    for student in students:
        cursor.execute("SELECT Skill FROM SkillTags WHERE StudentID = %s", (student['StudentID'],))
        student['Skills'] = [s['Skill'] for s in cursor.fetchall()]
        if student.get('ReliabilityScore'):
            student['ReliabilityScore'] = float(student['ReliabilityScore'])
            
    cursor.close()
    conn.close()
    return students

def search_opportunities(query):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    term = f"%{query}%"
    sql = "SELECT DISTINCT O.* FROM Opportunity O LEFT JOIN RequiredSkills RS ON O.OppID = RS.OppID WHERE O.Status = 'Active' AND (O.RoleTitle LIKE %s OR RS.Skill LIKE %s OR O.City LIKE %s);"
    cursor.execute(sql, (term, term, term))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_students_for_hire():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT S.StudentID, S.FirstName, S.LastName, S.AcademicAffiliation, S.City, S.ReliabilityScore FROM Student S")
    students = cursor.fetchall()
    for student in students:
        if student.get('ReliabilityScore'): student['ReliabilityScore'] = float(student['ReliabilityScore'])
        cursor.execute("SELECT Skill FROM SkillTags WHERE StudentID = %s", (student['StudentID'],))
        student['Skills'] = [s['Skill'] for s in cursor.fetchall()]
    cursor.close()
    conn.close()
    return students


# ==========================================
# JOB MANAGEMENT (CREATION & EDITS)
# ==========================================
def create_job_post(employer_id, title, job_type, req_students, city, state, skills, description, funds, milestones):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Opportunity (RoleTitle, Type, RequiredStudents, City, State, Description, Status) 
            VALUES (%s, %s, %s, %s, %s, %s, 'Active')
        """, (title, job_type, req_students, city, state, description))
        opp_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO Posts (EmployerID, OppID) VALUES (%s, %s)", (employer_id, opp_id))
        
        for skill in skills:
            cursor.execute("INSERT INTO RequiredSkills (OppID, Skill) VALUES (%s, %s)", (opp_id, skill))
            
        for ms in milestones:
            cursor.execute("""
                INSERT INTO MilestoneLedger (OppID, Description, Payout, Deadline, ApprovalStatus) 
                VALUES (%s, %s, %s, %s, 'Pending')
            """, (opp_id, ms['desc'], ms['payout'], ms['deadline']))
            
        cursor.execute("INSERT INTO ProjWallet (OppID, TotalAmount, Status) VALUES (%s, %s, 'Funded')", (opp_id, funds))
        
        conn.commit()
        return True, "Job posted successfully!"
    except Exception as e:
        conn.rollback()
        print(f"Post Job Error: {e}")
        return False, "Database error occurred."
    finally:
        cursor.close()
        conn.close()

def edit_job(opp_id, title, job_type, req_students, city, state, skills, description):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) 
    try:
        cursor.execute("""
            SELECT O.Status, 
                (SELECT COUNT(*) FROM Job_application JA 
                    JOIN Application A ON JA.ApplicationID = A.ApplicationID 
                    WHERE JA.OppID = O.OppID AND A.Status = 'Accepted') as HiredCount
            FROM Opportunity O WHERE O.OppID = %s
        """, (opp_id,))
        job_info = cursor.fetchone()
        
        if not job_info:
            return False, "Job not found."
            
        current_status = job_info['Status']
        hired_count = job_info['HiredCount']
        req_students_int = int(req_students)
        
        if req_students_int < hired_count:
            return False, f"Cannot reduce capacity. You already have {hired_count} student(s) hired."
            
        new_status = current_status
        if current_status in ['Active', 'Assigned']:
            if req_students_int > hired_count:
                new_status = 'Active'
            elif req_students_int == hired_count:
                new_status = 'Assigned'

        cursor.execute("""
            UPDATE Opportunity 
            SET RoleTitle=%s, Type=%s, RequiredStudents=%s, City=%s, State=%s, Description=%s, Status=%s 
            WHERE OppID=%s
        """, (title, job_type, req_students_int, city, state, description, new_status, opp_id))
        
        cursor.execute("DELETE FROM RequiredSkills WHERE OppID = %s", (opp_id,))
        for skill in skills:
            cursor.execute("INSERT INTO RequiredSkills (OppID, Skill) VALUES (%s, %s)", (opp_id, skill))
            
        conn.commit()
        return True, "Details updated successfully!"
    except Exception as e:
        conn.rollback()
        print(f"Edit Error: {e}")
        return False, "Database error."
    finally:
        cursor.close()
        conn.close()

def update_job_post(opp_id, role_title, description, job_type, city, state, req_students):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Opportunity 
            SET RoleTitle=%s, Description=%s, Type=%s, City=%s, State=%s, RequiredStudents=%s 
            WHERE OppID=%s
        """, (role_title, description, job_type, city, state, req_students, opp_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Update Job Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


# ==========================================
# APPLICATIONS & HIRING PROCESS
# ==========================================
def apply_for_job(student_id, opp_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Skill FROM RequiredSkills WHERE OppID = %s", (opp_id,))
    job_skills = set([s['Skill'] for s in cursor.fetchall()])
    
    cursor.execute("SELECT Skill FROM SkillTags WHERE StudentID = %s", (student_id,))
    student_skills = set([s['Skill'] for s in cursor.fetchall()])
    
    if not job_skills.issubset(student_skills):
        cursor.close()
        conn.close()
        return False, "ACTION REQUIRED: You do not have the required skills on your profile for this role."
    
    try:
        cursor.execute("SELECT 1 FROM Job_application WHERE StudentID = %s AND OppID = %s", (student_id, opp_id))
        if cursor.fetchone(): return False, "You have already applied for this role."
        
        cursor.execute("INSERT INTO Application (ApplicationDate, Status) VALUES (CURDATE(), 'Pending')")
        app_id = cursor.lastrowid
        cursor.execute("INSERT INTO Job_application (ApplicationID, OppID, StudentID) VALUES (%s, %s, %s)", (app_id, opp_id, student_id))
        conn.commit()
        success, msg = True, "Application Submitted Successfully!"
    except Exception as e:
        conn.rollback()
        print(f"Apply Error: {e}")
        success, msg = False, "Database Error."
    finally:
        cursor.close()
        conn.close()
    return success, msg

def accept_application(app_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("UPDATE Application SET Status = 'Accepted' WHERE ApplicationID = %s", (app_id,))
        cursor.execute("SELECT OppID FROM Job_application WHERE ApplicationID = %s", (app_id,))
        row = cursor.fetchone()
        
        if row:
            opp_id = row['OppID']
            cursor.execute("""
                SELECT O.RequiredStudents, 
                    (SELECT COUNT(*) FROM Job_application JA JOIN Application A ON JA.ApplicationID = A.ApplicationID WHERE JA.OppID = O.OppID AND A.Status = 'Accepted') as AcceptedCount
                FROM Opportunity O WHERE O.OppID = %s
            """, (opp_id,))
            quota = cursor.fetchone()
            req_students = quota['RequiredStudents'] if quota and quota['RequiredStudents'] else 0
            accepted_count = quota['AcceptedCount'] if quota and quota['AcceptedCount'] else 0
            
            if req_students > 0 and accepted_count >= req_students:
                cursor.execute("UPDATE Opportunity SET Status = 'Assigned' WHERE OppID = %s", (opp_id,))
                cursor.execute("UPDATE Application SET Status = 'Rejected' WHERE Status = 'Pending' AND ApplicationID IN (SELECT ApplicationID FROM Job_application WHERE OppID = %s)", (opp_id,))
        
        conn.commit()
        success = True
    except Exception as e:
        conn.rollback()
        print(f"CRITICAL HIRE ERROR: {e}")
        success = False
    finally:
        cursor.close()
        conn.close()
    return success

def withdraw_application(app_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Application SET Status = 'Withdrawn' WHERE ApplicationID = %s", (app_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Withdraw Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def schedule_interview(app_id, scheduled_time, meeting_type, meeting_link):
    input_time = datetime.strptime(scheduled_time.replace('T', ' '), '%Y-%m-%d %H:%M')
    if input_time < datetime.now():
        return False, "You cannot schedule an interview in the past."

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Interview (ApplicationID, ScheduledTime, MeetingType, ApplicationStatus, MeetingLink)
            VALUES (%s, %s, %s, 'Scheduled', %s)
            ON DUPLICATE KEY UPDATE ScheduledTime=VALUES(ScheduledTime), MeetingType=VALUES(MeetingType), ApplicationStatus='Scheduled', MeetingLink=VALUES(MeetingLink)
        """, (app_id, scheduled_time.replace('T', ' '), meeting_type, meeting_link))
        conn.commit()
        return True, "Interview scheduled successfully!"
    except Exception as e:
        conn.rollback()
        print(f"Interview Error: {e}")
        return False, "Database error."
    finally:
        cursor.close()
        conn.close()


# ==========================================
# DASHBOARD SPECIFIC DATA QUERIES
# ==========================================
def get_employer_data(emp_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT O.*, (SELECT COUNT(*) FROM Job_application WHERE OppID = O.OppID) as AppCount 
        FROM Opportunity O JOIN Posts P ON O.OppID = P.OppID WHERE P.EmployerID = %s;
    """
    cursor.execute(sql, (emp_id,))
    postings = cursor.fetchall()
    cursor.execute("SELECT TrustScore FROM Employer WHERE EmployerID = %s", (emp_id,))
    ts = cursor.fetchone()
    cursor.close()
    conn.close()
    return postings, (float(ts['TrustScore']) if ts and ts['TrustScore'] else 5.0)

def get_student_applications(student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT O.RoleTitle, E.BusinessName, A.Status, A.ApplicationDate, O.OppID, A.ApplicationID, O.City, O.Status as JobStatus
        FROM Job_application JA JOIN Application A ON JA.ApplicationID = A.ApplicationID JOIN Opportunity O ON JA.OppID = O.OppID
        JOIN Posts P ON O.OppID = P.OppID JOIN Employer E ON P.EmployerID = E.EmployerID WHERE JA.StudentID = %s ORDER BY A.ApplicationDate DESC;
    """
    cursor.execute(sql, (student_id,))
    apps = cursor.fetchall()
    cursor.close()
    conn.close()
    return apps

def get_active_projects(user_id, user_type):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if user_type == 'employer':
        sql = """
            SELECT O.*, 
                (SELECT COUNT(*) FROM Job_application JA2 JOIN Application A2 ON JA2.ApplicationID = A2.ApplicationID WHERE JA2.OppID = O.OppID AND A2.Status = 'Accepted') as HiredCount
            FROM Opportunity O 
            JOIN Posts P ON O.OppID = P.OppID 
            WHERE P.EmployerID = %s AND O.Status IN ('Assigned', 'Funded', 'Completed')
            GROUP BY O.OppID;
        """
    else:
        sql = """
            SELECT O.*, E.BusinessName, A.Status as AppStatus, A.ApplicationID
            FROM Opportunity O 
            JOIN Job_application JA ON O.OppID = JA.OppID
            JOIN Application A ON JA.ApplicationID = A.ApplicationID
            JOIN Posts P ON O.OppID = P.OppID
            JOIN Employer E ON P.EmployerID = E.EmployerID
            WHERE JA.StudentID = %s AND A.Status = 'Accepted';
        """
    cursor.execute(sql, (user_id,))
    projects = cursor.fetchall()
    cursor.close()
    conn.close()
    return projects

def get_job_details(opp_id, student_id=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT O.*, E.BusinessName, E.VerifiedIdentity, E.TrustScore 
        FROM Opportunity O 
        JOIN Posts P ON O.OppID = P.OppID 
        JOIN Employer E ON P.EmployerID = E.EmployerID 
        WHERE O.OppID = %s
    """, (opp_id,))
    job = cursor.fetchone()
    
    if job:
        cursor.execute("SELECT Skill FROM RequiredSkills WHERE OppID = %s", (opp_id,))
        job['Skills'] = [s['Skill'] for s in cursor.fetchall()]
        
        job['HasApplied'] = False
        job['MissingSkills'] = False 
        job['MyApplicationStatus'] = None
        
        cursor.execute("""
            SELECT S.StudentID, S.FirstName, S.LastName, A.ApplicationID 
            FROM Job_application JA 
            JOIN Application A ON JA.ApplicationID = A.ApplicationID 
            JOIN Student S ON JA.StudentID = S.StudentID 
            WHERE JA.OppID = %s AND A.Status = 'Accepted'
        """, (opp_id,))
        hired_team = cursor.fetchall()
        job['HiredApplicants'] = hired_team if hired_team else []
        
        job['IsHired'] = False
        job['MyApplicationID'] = None

        if student_id:
            cursor.execute("""
                SELECT A.ApplicationID, A.Status, 
                    DATE_FORMAT(I.ScheduledTime, '%b %d, %Y at %h:%i %p') as ScheduledAt, 
                    I.MeetingType, I.ApplicationStatus as IntStatus, I.MeetingLink
                FROM Job_application JA
                JOIN Application A ON JA.ApplicationID = A.ApplicationID
                LEFT JOIN Interview I ON A.ApplicationID = I.ApplicationID
                WHERE JA.OppID = %s AND JA.StudentID = %s
            """, (opp_id, student_id))
            my_app = cursor.fetchone()

            if my_app:
                job['HasApplied'] = True
                job['MyApplicationID'] = my_app['ApplicationID']
                
                # FIXED: Prioritize 'Accepted' or 'Rejected' so they don't get stuck in Interview mode
                if my_app['Status'] in ['Accepted', 'Rejected']:
                    job['MyApplicationStatus'] = my_app['Status']
                elif my_app['IntStatus'] == 'Scheduled':
                    job['MyApplicationStatus'] = 'Interviewing'
                    job['InterviewTime'] = my_app['ScheduledAt']
                    job['InterviewType'] = my_app['MeetingType']
                    job['InterviewLink'] = my_app['MeetingLink']
                else:
                    job['MyApplicationStatus'] = my_app['Status']
            
            if not job['HasApplied'] and job['Skills']: 
                cursor.execute("SELECT Skill FROM SkillTags WHERE StudentID = %s", (student_id,))
                student_skills = set([s['Skill'] for s in cursor.fetchall()])
                job_skills = set(job['Skills'])
                if not job_skills.issubset(student_skills):
                    job['MissingSkills'] = True
            
            for app in job['HiredApplicants']:
                if str(app['StudentID']) == str(student_id):
                    job['IsHired'] = True
                    break

        cursor.execute("SELECT MilestoneID, Description, Payout, Deadline, ApprovalStatus FROM MilestoneLedger WHERE OppID = %s", (opp_id,))
        job['Milestones'] = cursor.fetchall()

        cursor.execute("SELECT TotalAmount FROM ProjWallet WHERE OppID = %s", (opp_id,))
        wallet = cursor.fetchone()
        job['EscrowRemaining'] = float(wallet['TotalAmount']) if wallet else 0.0

        job['Feedback'] = []
        if hired_team:
            app_ids = [str(h['ApplicationID']) for h in hired_team]
            format_strings = ','.join(['%s'] * len(app_ids))
            cursor.execute(f"""
                SELECT RecordID, ReviewerRole, MetricType, ImpactScore, FeedbackDescription, Refuted 
                FROM PerformanceLedger WHERE ApplicationID IN ({format_strings})
            """, tuple(app_ids))
            job['Feedback'] = cursor.fetchall()

    cursor.close()
    conn.close()
    return job

def get_app_details(opp_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT S.StudentID, S.FirstName, S.LastName, S.ReliabilityScore as AvgImpact, 
            A.ApplicationID, 
            CASE 
                WHEN A.Status = 'Accepted' THEN 'Accepted'
                WHEN A.Status = 'Rejected' THEN 'Rejected'
                WHEN I.ApplicationStatus = 'Scheduled' THEN 'Interviewing' 
                ELSE A.Status 
            END AS Status, 
            DATE_FORMAT(I.ScheduledTime, '%b %d, %Y at %h:%i %p') as ScheduledAt, 
            I.MeetingType, I.MeetingLink 
        FROM Job_application JA
        JOIN Application A ON JA.ApplicationID = A.ApplicationID
        JOIN Student S ON JA.StudentID = S.StudentID
        LEFT JOIN Interview I ON A.ApplicationID = I.ApplicationID
        WHERE JA.OppID = %s
    """, (opp_id,))
    
    apps = cursor.fetchall()
    cursor.close()
    conn.close()
    return apps

def get_student_app_details(app_id, opp_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT O.RoleTitle, O.Description, E.BusinessName, O.City, O.Status as JobStatus FROM Opportunity O JOIN Posts P ON O.OppID = P.OppID JOIN Employer E ON P.EmployerID = E.EmployerID WHERE O.OppID = %s", (opp_id,))
    job_info = cursor.fetchone()
    
    cursor.execute("SELECT Skill FROM RequiredSkills WHERE OppID = %s", (opp_id,))
    skills = [s['Skill'] for s in cursor.fetchall()]
    
    cursor.execute("SELECT Status FROM Application WHERE ApplicationID = %s", (app_id,))
    status = cursor.fetchone()['Status']

    cursor.execute("SELECT MilestoneID, Description, Payout, Deadline, ApprovalStatus FROM MilestoneLedger WHERE OppID = %s", (opp_id,))
    milestones = cursor.fetchall()

    cursor.execute("SELECT TotalAmount FROM ProjWallet WHERE OppID = %s", (opp_id,))
    wallet = cursor.fetchone()
    total_escrow = float(wallet['TotalAmount']) if wallet else 0.0

    cursor.execute("SELECT SUM(Payout) as ApprovedTotal FROM MilestoneLedger WHERE OppID = %s AND ApprovalStatus = 'Approved'", (opp_id,))
    approved = cursor.fetchone()['ApprovedTotal'] or 0.0

    cursor.execute("SELECT ReviewerRole, MetricType, ImpactScore, Refuted FROM PerformanceLedger WHERE ApplicationID = %s", (app_id,))
    feedback = cursor.fetchall()

    cursor.close()
    conn.close()
    return {"job": job_info, "skills": skills, "status": status, "milestones": milestones, "escrow": total_escrow - float(approved), "feedback": feedback}

def get_applicant_profile(app_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT S.*, A.Status, A.ApplicationID,
        (SELECT AVG(ImpactScore) FROM PerformanceLedger WHERE ApplicationID = A.ApplicationID) as AvgImpact
        FROM Job_application JA JOIN Application A ON JA.ApplicationID = A.ApplicationID JOIN Student S ON JA.StudentID = S.StudentID WHERE A.ApplicationID = %s
    """
    cursor.execute(sql, (app_id,))
    student = cursor.fetchone()
    if student:
        if student.get('ReliabilityScore'): student['ReliabilityScore'] = float(student['ReliabilityScore'])
        if student.get('AvgImpact') and student['AvgImpact'] is not None: student['AvgImpact'] = float(student['AvgImpact'])
        cursor.execute("SELECT Skill FROM SkillTags WHERE StudentID = %s", (student['StudentID'],))
        student['Skills'] = [s['Skill'] for s in cursor.fetchall()]
    cursor.close()
    conn.close()
    return student


# ==========================================
# MILESTONES & PAYOUTS
# ==========================================
def edit_milestone(milestone_id, desc, payout, deadline):
    today = datetime.now().date()
    ms_date = datetime.strptime(deadline, '%Y-%m-%d').date()
    if ms_date < today:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE MilestoneLedger SET Description = %s, Payout = %s, Deadline = %s WHERE MilestoneID = %s", (desc, payout, deadline, milestone_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Edit Milestone Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def submit_milestone_work(milestone_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE MilestoneLedger SET ApprovalStatus = 'Submitted' WHERE MilestoneID = %s", (milestone_id,))
        conn.commit()
        success = True
    except Exception as e:
        conn.rollback()
        print(f"Milestone Submit Error: {e}")
        success = False
    finally:
        cursor.close()
        conn.close()
    return success

def reject_milestone(milestone_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE MilestoneLedger SET ApprovalStatus = 'Pending' WHERE MilestoneID = %s", (milestone_id,))
        conn.commit()
        success = True
    except Exception as e:
        conn.rollback()
        print(f"Milestone Reject Error: {e}")
        success = False
    finally:
        cursor.close()
        conn.close()
    return success

def approve_milestone(milestone_id, opp_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    job_completed = False
    app_id = None
    
    try:
        # 1. Get the payout amount for this milestone
        cursor.execute("SELECT Payout FROM MilestoneLedger WHERE MilestoneID = %s", (milestone_id,))
        payout_res = cursor.fetchone()
        payout_amount = float(payout_res['Payout']) if payout_res else 0.0

        # 2. Mark Milestone as Approved
        cursor.execute("UPDATE MilestoneLedger SET ApprovalStatus = 'Approved' WHERE MilestoneID = %s", (milestone_id,))
        
        # 3. Get the EmployerID from the Posts table
        cursor.execute("SELECT EmployerID FROM Posts WHERE OppID = %s", (opp_id,))
        emp_res = cursor.fetchone()
        emp_id = emp_res['EmployerID'] if emp_res else None

        wallet_id = opp_id

        # Get the Employer's Payment Method ID 
        payment_method_id = None
        if emp_id:
            cursor.execute("SELECT payment_method_id FROM Employer_Payment_Method WHERE employer_id = %s LIMIT 1", (emp_id,))
            emp_pay_res = cursor.fetchone()
            if emp_pay_res:
                payment_method_id = emp_pay_res['payment_method_id']
        
        # 4. Find all hired students for this project
        cursor.execute("""
            SELECT JA.StudentID, JA.ApplicationID 
            FROM Job_application JA 
            JOIN Application A ON JA.ApplicationID = A.ApplicationID 
            WHERE JA.OppID = %s AND A.Status = 'Accepted'
        """, (opp_id,))
        hired_students = cursor.fetchall()
        
        # 5. The "Equal Split" Transaction Loop
        if hired_students and emp_id and wallet_id:
            split_amount = round(payout_amount / len(hired_students), 2)
            
            for student in hired_students:
                std_id = student['StudentID']
                
                payout_method_id = None
                cursor.execute("SELECT payout_method_id FROM Student_Payout_Method WHERE student_id = %s LIMIT 1", (std_id,))
                std_payout_res = cursor.fetchone()
                if std_payout_res:
                    payout_method_id = std_payout_res['payout_method_id']

                tx_hash = hashlib.sha256(f"{milestone_id}_{std_id}_{time.time()}".encode()).hexdigest()
                
                cursor.execute("""
                    INSERT INTO Transaction_Ledger 
                    (wallet_id, EmployerID, StudentID, amount, transaction_type, transaction_hash, milestone_id, payment_method_id, payout_method_id)
                    VALUES (%s, %s, %s, %s, 'Payout', %s, %s, %s, %s)
                """, (wallet_id, emp_id, std_id, split_amount, tx_hash, milestone_id, payment_method_id, payout_method_id))
                
                if not app_id: 
                    app_id = student['ApplicationID']

        # 6. FIXED: Check if project is completely funded dynamically 
        # (Don't subtract from TotalAmount, compare Approved vs Initial Deposit)
        cursor.execute("SELECT TotalAmount FROM ProjWallet WHERE OppID = %s", (opp_id,))
        wallet = cursor.fetchone()
        total_funded = float(wallet['TotalAmount']) if wallet else 0.0

        cursor.execute("SELECT SUM(Payout) as ApprovedTotal FROM MilestoneLedger WHERE OppID = %s AND ApprovalStatus = 'Approved'", (opp_id,))
        approved_res = cursor.fetchone()
        approved_total = float(approved_res['ApprovedTotal']) if approved_res and approved_res['ApprovedTotal'] else 0.0

        if approved_total >= total_funded:
            cursor.execute("UPDATE Opportunity SET Status = 'Completed' WHERE OppID = %s", (opp_id,))
            job_completed = True
            
        conn.commit()
        return True, job_completed, app_id
        
    except Exception as e:
        conn.rollback()
        print(f"Approve Error: {e}") 
        return False, False, None
    finally:
        cursor.close()
        conn.close()

def mark_opportunity_completed(opp_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Opportunity SET Status = 'Completed' WHERE OppID = %s", (opp_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error completing opp: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def complete_project_and_rate(opp_id, reviewer_role, ratings_dict):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Get the ApplicationID(s) involved in this project
        cursor.execute("""
            SELECT JA.ApplicationID, JA.StudentID, P.EmployerID 
            FROM Job_application JA 
            JOIN Application A ON JA.ApplicationID = A.ApplicationID 
            JOIN Posts P ON JA.OppID = P.OppID
            WHERE JA.OppID = %s AND A.Status = 'Accepted'
        """, (opp_id,))
        apps = cursor.fetchall()
        
        if not apps:
            return False
        for app in apps:
            for metric, score in ratings_dict.items():
                cursor.execute("""
                    INSERT INTO PerformanceLedger (ApplicationID, ReviewerRole, MetricType, ImpactScore, FeedbackDescription, Refuted)
                    VALUES (%s, %s, %s, %s, 'Final Project Rating', 'N')
                """, (app['ApplicationID'], reviewer_role, metric, score))
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN ReviewerRole = 'Employer' THEN 1 ELSE 0 END) as EmpRated,
                SUM(CASE WHEN ReviewerRole = 'Student' THEN 1 ELSE 0 END) as StuRated
            FROM PerformanceLedger 
            WHERE ApplicationID IN (SELECT ApplicationID FROM Job_application WHERE OppID = %s)
            AND MetricType IN ('Quality of Work', 'Communication', 'Professionalism')
        """, (opp_id,))
        check = cursor.fetchone()
        if check['EmpRated'] > 0 and check['StuRated'] > 0:
            
            # A. Mark job as completed
            cursor.execute("UPDATE Opportunity SET Status = 'Completed' WHERE OppID = %s", (opp_id,))
            
            # B. Update Student Reliability Scores
            for app in apps:
                cursor.execute("""
                    UPDATE Student SET ReliabilityScore = (
                        SELECT AVG(ImpactScore) FROM PerformanceLedger 
                        WHERE ApplicationID IN (SELECT ApplicationID FROM Job_application WHERE StudentID = %s)
                        AND ReviewerRole = 'Employer' AND ImpactScore IS NOT NULL AND Refuted = 'N'
                    ) WHERE StudentID = %s
                """, (app['StudentID'], app['StudentID']))
            
            # C. Update Employer Trust Score
            emp_id = apps[0]['EmployerID']
            cursor.execute("""
                UPDATE Employer SET TrustScore = (
                    SELECT AVG(PL.ImpactScore) 
                    FROM PerformanceLedger PL
                    JOIN Job_application JA ON PL.ApplicationID = JA.ApplicationID
                    JOIN Posts P ON JA.OppID = P.OppID
                    WHERE P.EmployerID = %s AND PL.ReviewerRole = 'Student' 
                    AND PL.ImpactScore IS NOT NULL AND PL.Refuted = 'N'
                ) WHERE EmployerID = %s
            """, (emp_id, emp_id))
            
            print(f"Project {opp_id} fully finalized and scores updated.")
        else:
            print(f"Rating recorded for {reviewer_role}. Waiting for the other party to rate.")

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Detailed Rating Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# ==========================================
# REVIEWS, DISPUTES & MESSAGING
# ==========================================
def check_both_rated(app_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM PerformanceLedger WHERE ApplicationID = %s", (app_id,))
        count = cursor.fetchone()[0]
        return count >= 2
    except Exception as e:
        print(f"Check rating error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def submit_feedback(app_id, reviewer_role, metrics, feedback_text):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        for metric, score in metrics.items():
            cursor.execute("INSERT INTO PerformanceLedger (ApplicationID, ImpactScore, MetricType, ReviewerRole) VALUES (%s, %s, %s, %s)", (app_id, score, metric, reviewer_role))
        if feedback_text:
            cursor.execute("INSERT INTO PerformanceLedger (ApplicationID, ImpactScore, MetricType, ReviewerRole) VALUES (%s, NULL, %s, %s)", (app_id, f"Feedback: {feedback_text}", reviewer_role))
        
        cursor.execute("SELECT JA.StudentID, P.EmployerID FROM Job_application JA JOIN Posts P ON JA.OppID = P.OppID WHERE JA.ApplicationID = %s", (app_id,))
        ids = cursor.fetchone()

        if reviewer_role == 'Employer':
            cursor.execute("SELECT AVG(PL.ImpactScore) as new_score FROM PerformanceLedger PL JOIN Job_application JA ON PL.ApplicationID = JA.ApplicationID WHERE JA.StudentID = %s AND PL.ReviewerRole = 'Employer' AND PL.ImpactScore IS NOT NULL", (ids['StudentID'],))
            res = cursor.fetchone()
            if res and res['new_score']: cursor.execute("UPDATE Student SET ReliabilityScore = %s WHERE StudentID = %s", (round(res['new_score'], 1), ids['StudentID']))
        else:
            cursor.execute("SELECT AVG(PL.ImpactScore) as new_score FROM PerformanceLedger PL JOIN Job_application JA ON PL.ApplicationID = JA.ApplicationID JOIN Posts P ON JA.OppID = P.OppID WHERE P.EmployerID = %s AND PL.ReviewerRole = 'Student' AND PL.ImpactScore IS NOT NULL", (ids['EmployerID'],))
            res = cursor.fetchone()
            if res and res['new_score']: cursor.execute("UPDATE Employer SET TrustScore = %s WHERE EmployerID = %s", (round(res['new_score'], 1), ids['EmployerID']))
                
        conn.commit()
        success = True
    except Exception as e:
        conn.rollback()
        print(f"Feedback Error: {e}")
        success = False
    finally:
        cursor.close()
        conn.close()
    return success

def post_feedback(app_id, reviewer_role, metric_type, impact_score, feedback_desc):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO PerformanceLedger (ApplicationID, ReviewerRole, MetricType, ImpactScore, FeedbackDescription, Refuted)
            VALUES (%s, %s, %s, %s, %s, 'N')
        """, (app_id, reviewer_role, metric_type, impact_score, feedback_desc))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Feedback Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def refute_feedback(record_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE PerformanceLedger SET Refuted = 'Y' WHERE RecordID = %s", (record_id,))
        conn.commit()
        if cursor.rowcount == 0: return False
        return True
    except Exception as e:
        conn.rollback()
        print(f"Refute SQL Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def send_message(opp_id, sender_name, sender_role, message_text):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO ChatMessages (OppID, SenderName, SenderRole, MessageText) 
            VALUES (%s, %s, %s, %s)
        """, (opp_id, sender_name, sender_role, message_text))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Chat Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_chat_messages(opp_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT SenderName, SenderRole, MessageText, DATE_FORMAT(SentAt, '%h:%i %p') as TimeString 
        FROM ChatMessages 
        WHERE OppID = %s 
        ORDER BY SentAt ASC
    """, (opp_id,))
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return messages

def get_active_jobs_for_employer(employer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT O.OppID, O.RoleTitle 
            FROM Opportunity O
            JOIN Posts P ON O.OppID = P.OppID
            WHERE P.EmployerID = %s AND O.Status = 'Active'
        """, (employer_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching active jobs: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def create_project_invitation(opp_id, employer_id, student_id, message):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if an invite already exists to prevent spam
        cursor.execute("""
            SELECT 1 FROM Project_Invitations 
            WHERE opp_id = %s AND student_id = %s AND status = 'Pending'
        """, (opp_id, student_id))
        
        if cursor.fetchone():
            return False, 'You have already invited this student to this project.'

        # Insert the invite
        cursor.execute("""
            INSERT INTO Project_Invitations (opp_id, employer_id, student_id, message, status)
            VALUES (%s, %s, %s, %s, 'Pending')
        """, (opp_id, employer_id, student_id, message))
        
        conn.commit()
        return True, 'Invite sent successfully!'
        
    except Exception as e:
        conn.rollback()
        print(f"Invite Error: {e}")
        return False, 'Database error occurred while sending invite.'
    finally:
        cursor.close()
        conn.close()

def get_student_invitations(student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Grabs the pending invites and joins the job/employer details
        cursor.execute("""
            SELECT pi.invite_id, pi.opp_id, pi.message AS Message,
                o.RoleTitle, o.Type, o.City, e.BusinessName
            FROM Project_Invitations pi
            JOIN Opportunity o ON pi.opp_id = o.OppID
            JOIN Employer e ON pi.employer_id = e.EmployerID
            WHERE pi.student_id = %s AND pi.status = 'Pending'
        """, (student_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching invitations: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def respond_to_invitation(invite_id, opp_id, student_id, action):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if action == 'Accept':
            # 1. Mark invite as Accepted
            cursor.execute("UPDATE Project_Invitations SET status = 'Accepted' WHERE invite_id = %s AND student_id = %s", (invite_id, student_id))
            conn.commit() # Commit the invite update first
            
            # 2. Automatically create the Job Application using your existing function!
            # Note: Make sure the parameter order matches your actual apply_to_job function signature!
            success, message = apply_for_job(student_id, opp_id) 
            
            if not success:
                return False, f"Invite accepted, but application failed: {message}"
                
            return True, "Successfully applied from invitation!"
            
        elif action == 'Decline':
            # Just mark it as Declined so it disappears from their dashboard
            cursor.execute("UPDATE Project_Invitations SET status = 'Declined' WHERE invite_id = %s AND student_id = %s", (invite_id, student_id))
            conn.commit()
            return True, "Invitation declined."
            
    except Exception as e:
        conn.rollback()
        print(f"Error responding to invite: {e}")
        return False, "Database error occurred."
    finally:
        cursor.close()
        conn.close()