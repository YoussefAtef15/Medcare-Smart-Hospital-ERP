from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import sqlite3
import re
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'smart_hospital_secret_key'

# --- File Upload Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'Smart Hospital System.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads/prescriptions')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# --- Security: Initialize Admin Password Hash ---
def initialize_admin_hash():
    try:
        conn = get_db_connection()
        admin = conn.execute("SELECT * FROM User WHERE Username = 'admin'").fetchone()
        if admin and not admin['PasswordHash'].startswith('scrypt:'):
            secure_hash = generate_password_hash('admin123')
            conn.execute("UPDATE User SET PasswordHash = ? WHERE Username = 'admin'", (secure_hash,))
            conn.commit()
        conn.close()
    except Exception:
        pass


initialize_admin_hash()


# --- Helper Function for Audit Logging ---
def log_audit(user_id, action, table_name, record_id=None):
    if user_id:
        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO AuditLog (UserID, Action, TableName, RecordID, ActionDate)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, action, table_name, record_id))
            conn.commit()
            conn.close()
        except Exception:
            pass


# --- Helper Function for Notifications ---
def add_notification(message):
    if 'notifications' not in session:
        session['notifications'] = []
    session['notifications'].insert(0, {
        'msg': message,
        'time': datetime.now().strftime("%Y-%m-%d %I:%M %p")
    })
    session['notifications'] = session['notifications'][:5]
    session.modified = True


# --- Default Role Setup ---
@app.before_request
def require_login():
    allowed_routes = ['login', 'static', 'switch_role']
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        return redirect(url_for('login'))


# --- AUTHENTICATION & PROFILE ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM User WHERE Username = ? AND IsActive = 1', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['PasswordHash'], password):
            session['user_id'] = user['UserID']
            session['username'] = user['Username']
            session['role'] = user['Role'].lower()
            session['doctor_id'] = user['DoctorID']
            session['nurse_id'] = user['NurseID']
            session['patient_id'] = user['PatientID']

            log_audit(user['UserID'], 'User Logged In', 'User', user['UserID'])
            flash(f'Welcome, {user["Username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Access Denied: Invalid credentials or deactivated account.', 'error')

    return render_template('auth/login.html')


@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        log_audit(user_id, 'User Logged Out', 'User', user_id)
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


@app.route('/switch_role/<role>')
def switch_role(role):
    session.clear()
    flash(f'Session cleared. Please log in with your {role.capitalize()} account credentials to continue.', 'info')
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    conn = get_db_connection()
    role = session.get('role')
    user_id = session.get('user_id')

    if request.method == 'POST':
        data = request.form
        try:
            if role == 'doctor':
                doc_id = session.get('doctor_id')
                # Strict constraints: Cannot update Salary, HireDate, Dept, Specs. Only Contact Info.
                conn.execute('UPDATE Doctor SET Email=?, Street=?, City=?, ZipCode=? WHERE DoctorID=?',
                             (data['email'], data['street'], data['city'], data['zip_code'], doc_id))
                if data.get('phone'):
                    conn.execute('DELETE FROM Doctor_Phone WHERE DoctorID=?', (doc_id,))
                    conn.execute('INSERT INTO Doctor_Phone (DoctorID, Phone) VALUES (?, ?)', (doc_id, data['phone']))
                log_audit(user_id, 'Updated Profile Info', 'Doctor', doc_id)

            elif role == 'nurse':
                nurse_id = session.get('nurse_id')
                conn.execute('UPDATE Nurse SET Email=?, Street=?, City=?, ZipCode=? WHERE NurseID=?',
                             (data['email'], data['street'], data['city'], data['zip_code'], nurse_id))
                if data.get('phone'):
                    conn.execute('DELETE FROM Nurse_Phone WHERE NurseID=?', (nurse_id,))
                    conn.execute('INSERT INTO Nurse_Phone (NurseID, Phone) VALUES (?, ?)', (nurse_id, data['phone']))
                log_audit(user_id, 'Updated Profile Info', 'Nurse', nurse_id)

            elif role == 'patient':
                pat_id = session.get('patient_id')
                conn.execute('UPDATE Patient SET Street=?, City=?, ZipCode=? WHERE PatientID=?',
                             (data['street'], data['city'], data['zip_code'], pat_id))
                if data.get('phone'):
                    conn.execute('DELETE FROM Patient_Phone WHERE PatientID=?', (pat_id,))
                    conn.execute('INSERT INTO Patient_Phone (PatientID, Phone) VALUES (?, ?)', (pat_id, data['phone']))
                log_audit(user_id, 'Updated Profile Info', 'Patient', pat_id)

            conn.commit()
            flash('Your profile has been updated successfully.', 'success')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')

        conn.close()
        return redirect(url_for('profile'))

    # GET Request: Fetch Data
    profile_data = None
    phone = ''
    if role == 'doctor':
        profile_data = conn.execute(
            'SELECT d.*, dept.DepartmentName FROM Doctor d LEFT JOIN Department dept ON d.DepartmentID = dept.DepartmentID WHERE d.DoctorID=?',
            (session.get('doctor_id'),)).fetchone()
        phone_row = conn.execute('SELECT Phone FROM Doctor_Phone WHERE DoctorID=?',
                                 (session.get('doctor_id'),)).fetchone()
        phone = phone_row['Phone'] if phone_row else ''
    elif role == 'nurse':
        profile_data = conn.execute(
            'SELECT n.*, dept.DepartmentName FROM Nurse n LEFT JOIN Department dept ON n.DepartmentID = dept.DepartmentID WHERE n.NurseID=?',
            (session.get('nurse_id'),)).fetchone()
        phone_row = conn.execute('SELECT Phone FROM Nurse_Phone WHERE NurseID=?', (session.get('nurse_id'),)).fetchone()
        phone = phone_row['Phone'] if phone_row else ''
    elif role == 'patient':
        profile_data = conn.execute('SELECT * FROM Patient WHERE PatientID=?', (session.get('patient_id'),)).fetchone()
        phone_row = conn.execute('SELECT Phone FROM Patient_Phone WHERE PatientID=?',
                                 (session.get('patient_id'),)).fetchone()
        phone = phone_row['Phone'] if phone_row else ''

    user_data = conn.execute('SELECT * FROM User WHERE UserID=?', (user_id,)).fetchone()
    conn.close()

    return render_template('auth/profile.html', profile_data=profile_data, phone=phone, user_data=user_data)


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        current_pw = request.form['current_password']
        new_pw = request.form['new_password']
        confirm_pw = request.form['confirm_password']

        if new_pw != confirm_pw:
            flash('New password and confirmation do not match!', 'error')
            return redirect(url_for('change_password'))

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM User WHERE UserID=?', (session['user_id'],)).fetchone()

        if not check_password_hash(user['PasswordHash'], current_pw):
            conn.close()
            flash('Incorrect current password. Please try again.', 'error')
            return redirect(url_for('change_password'))

        hashed_pw = generate_password_hash(new_pw)
        conn.execute('UPDATE User SET PasswordHash=? WHERE UserID=?', (hashed_pw, session['user_id']))
        conn.commit()
        conn.close()

        log_audit(session['user_id'], 'Changed Password', 'User', session['user_id'])
        session.clear()
        flash('Password changed successfully! Please log in again with your new password.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/change_password.html')


# --- Global Search API ---
@app.route('/api/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    conn = get_db_connection()
    suggestions = []

    patients = conn.execute(
        'SELECT PatientID, FirstName, LastName FROM Patient WHERE FirstName LIKE ? OR LastName LIKE ? LIMIT 3',
        ('%' + query + '%', '%' + query + '%')).fetchall()
    for p in patients:
        suggestions.append({'type': 'Patient', 'text': f"{p['FirstName']} {p['LastName']}", 'url': '/patients'})

    appts = conn.execute('SELECT AppointmentID, Status FROM Appointment WHERE Status LIKE ? LIMIT 3',
                         ('%' + query + '%',)).fetchall()
    for a in appts:
        suggestions.append(
            {'type': 'Appointment', 'text': f"Appt #{a['AppointmentID']} - {a['Status']}", 'url': '/appointments'})

    conn.close()
    return jsonify(suggestions)


# --- DASHBOARD ---
@app.route('/')
def dashboard():
    conn = get_db_connection()
    role = session.get('role', 'guest')

    # Basic stats for all roles
    total_patients = conn.execute('SELECT COUNT(*) FROM Patient').fetchone()[0]
    total_revenue = conn.execute('SELECT SUM(PaidAmount) FROM Bill').fetchone()[0] or 0.0
    total_appointments = conn.execute('SELECT COUNT(*) FROM Appointment').fetchone()[0]

    total_feedback = conn.execute('SELECT COUNT(*) FROM AI_Prediction WHERE Is_Accurate IS NOT NULL').fetchone()[0]
    accurate_predictions = conn.execute('SELECT COUNT(*) FROM AI_Prediction WHERE Is_Accurate = 1').fetchone()[0]
    ai_accuracy = round((accurate_predictions / total_feedback) * 100, 1) if total_feedback > 0 else 0

    occupied_rooms = conn.execute('SELECT COUNT(*) FROM Room WHERE Status = "Occupied"').fetchone()[0]
    available_rooms = conn.execute('SELECT COUNT(*) FROM Room WHERE Status = "Available"').fetchone()[0]
    maintenance_rooms = conn.execute('SELECT COUNT(*) FROM Room WHERE Status = "Maintenance"').fetchone()[0]
    total_rooms = conn.execute('SELECT COUNT(*) FROM Room').fetchone()[0]

    recent_appointments = conn.execute('''
        SELECT p.FirstName, p.LastName, a.AppointmentTime, a.AppointmentDate, a.Status 
        FROM Appointment a
        JOIN Patient p ON a.PatientID = p.PatientID
        ORDER BY a.AppointmentDate DESC, a.AppointmentTime DESC
        LIMIT 4
    ''').fetchall()

    total_billed = conn.execute('SELECT SUM(TotalAmount) FROM Bill').fetchone()[0] or 0.0
    unpaid_amount = total_billed - total_revenue

    monthly_appointments = conn.execute('''
        SELECT strftime('%m', AppointmentDate) as month, COUNT(*) as count 
        FROM Appointment 
        GROUP BY month 
        ORDER BY month
    ''').fetchall()

    chart_months = [datetime.strptime(row['month'], '%m').strftime('%b') for row in monthly_appointments]
    chart_appts = [row['count'] for row in monthly_appointments]

    today_str = datetime.today().strftime('%Y-%m-%d')
    today_appointments = \
    conn.execute('SELECT COUNT(*) FROM Appointment WHERE AppointmentDate = ?', (today_str,)).fetchone()[0]
    doctors_on_duty = conn.execute('SELECT COUNT(*) FROM Doctor').fetchone()[0]
    patients_waiting = conn.execute('SELECT COUNT(*) FROM Appointment WHERE Status = "Pending"').fetchone()[0]

    emergency_details = conn.execute('''
        SELECT p.FirstName, p.LastName, a.AppointmentDate, ai.Predicted_Disease, ai.Confidence_Score
        FROM AI_Prediction ai
        JOIN Appointment a ON ai.AppointmentID = a.AppointmentID
        JOIN Patient p ON a.PatientID = p.PatientID
        WHERE ai.Predicted_Disease LIKE '%Stroke%' 
        OR ai.Predicted_Disease LIKE '%Heart%' 
        OR ai.Predicted_Disease LIKE '%Emergency%'
        OR ai.Predicted_Disease LIKE '%Infarction%'
    ''').fetchall()
    emergency_cases = len(emergency_details)

    # --- ADMIN SPECIFIC DATA ---
    recent_activities = []
    upcoming_appointments = []
    alerts = []
    dept_labels = []
    dept_counts = []

    if role == 'admin':
        recent_activities = conn.execute(
            'SELECT a.*, u.Username FROM AuditLog a LEFT JOIN User u ON a.UserID = u.UserID ORDER BY ActionDate DESC LIMIT 5').fetchall()

        upcoming_appointments = conn.execute('''
            SELECT p.FirstName, p.LastName, a.AppointmentTime, a.AppointmentDate, a.Status, d.LastName as DLast 
            FROM Appointment a
            JOIN Patient p ON a.PatientID = p.PatientID
            JOIN Doctor d ON a.DoctorID = d.DoctorID
            WHERE a.AppointmentDate >= ?
            ORDER BY a.AppointmentDate ASC, a.AppointmentTime ASC
            LIMIT 5
        ''', (today_str,)).fetchall()

        unpaid_count = conn.execute('SELECT COUNT(*) FROM Bill WHERE PaymentStatus != "Paid"').fetchone()[0]
        if unpaid_count > 0: alerts.append({'type': 'danger', 'icon': 'bi-cash-stack',
                                            'msg': f'{unpaid_count} Unpaid bills require immediate attention.'})

        if maintenance_rooms > 0: alerts.append({'type': 'warning', 'icon': 'bi-tools',
                                                 'msg': f'{maintenance_rooms} Rooms are currently under maintenance.'})

        if patients_waiting > 0: alerts.append({'type': 'info', 'icon': 'bi-hourglass-split',
                                                'msg': f'{patients_waiting} Appointments waiting for confirmation.'})

        depts = conn.execute('''
            SELECT dept.DepartmentName, COUNT(d.DoctorID) as doc_count 
            FROM Department dept
            LEFT JOIN Doctor d ON dept.DepartmentID = d.DepartmentID
            GROUP BY dept.DepartmentID
        ''').fetchall()
        dept_labels = [d['DepartmentName'] for d in depts]
        dept_counts = [d['doc_count'] for d in depts]

    conn.close()
    current_date_display = datetime.today().strftime('%A, %b %d, %Y')

    return render_template('dashboard.html',
                           total_patients=total_patients,
                           revenue=round(total_revenue, 2),
                           total_appointments=total_appointments,
                           ai_accuracy=ai_accuracy,
                           occupied_rooms=occupied_rooms,
                           available_rooms=available_rooms,
                           maintenance_rooms=maintenance_rooms,
                           total_rooms=total_rooms,
                           recent_appointments=recent_appointments,
                           unpaid_amount=round(unpaid_amount, 2),
                           chart_months_json=json.dumps(chart_months),
                           chart_appts_json=json.dumps(chart_appts),
                           today_appointments=today_appointments,
                           doctors_on_duty=doctors_on_duty,
                           patients_waiting=patients_waiting,
                           emergency_cases=emergency_cases,
                           emergency_details=emergency_details,
                           current_date_display=current_date_display,
                           recent_activities=recent_activities,
                           upcoming_appointments=upcoming_appointments,
                           alerts=alerts,
                           dept_labels_json=json.dumps(dept_labels),
                           dept_counts_json=json.dumps(dept_counts))


# --- PAGE RENDERING ROUTES ---

@app.route('/users')
def users_page():
    if session.get('role') != 'admin':
        flash('Unauthorized Access.', 'error')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    users = conn.execute('''
        SELECT u.*, 
               d.FirstName as DFirst, d.LastName as DLast,
               n.FirstName as NFirst, n.LastName as NLast,
               p.FirstName as PFirst, p.LastName as PLast
        FROM User u
        LEFT JOIN Doctor d ON u.DoctorID = d.DoctorID
        LEFT JOIN Nurse n ON u.NurseID = n.NurseID
        LEFT JOIN Patient p ON u.PatientID = p.PatientID
    ''').fetchall()

    doctors = conn.execute('SELECT DoctorID, FirstName, LastName FROM Doctor').fetchall()
    nurses = conn.execute('SELECT NurseID, FirstName, LastName FROM Nurse').fetchall()
    patients = conn.execute('SELECT PatientID, FirstName, LastName FROM Patient').fetchall()
    conn.close()
    return render_template('admin/users.html', users=users, doctors=doctors, nurses=nurses, patients=patients)


@app.route('/patients')
def patients_page():
    if session.get('role') == 'patient':
        flash('Access Denied: Patients cannot view the directory.', 'error')
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    patients = conn.execute('''
        SELECT p.*, pp.Phone, r.RoomNumber, e.Name as EmgName, e.Relation as EmgRelation, e.Phone as EmgPhone, i.Provider as InsProvider, i.PolicyNumber as InsPolicy, i.Coverage as InsCoverage
        FROM Patient p 
        LEFT JOIN Patient_Phone pp ON p.PatientID = pp.PatientID 
        LEFT JOIN Room r ON p.PatientID = r.PatientID
        LEFT JOIN EmergencyContact e ON p.PatientID = e.PatientID
        LEFT JOIN Insurance i ON p.PatientID = i.PatientID
        GROUP BY p.PatientID
        ORDER BY p.PatientID ASC
    ''').fetchall()
    conn.close()
    return render_template('clinical/patients.html', patients=patients, today_date=datetime.today().strftime('%Y-%m-%d'))


@app.route('/appointments')
def appointments_page():
    conn = get_db_connection()
    role = session.get('role')
    query = '''
        SELECT a.AppointmentID, a.AppointmentDate, a.AppointmentTime, a.EndTime, a.AppointmentType, a.Status,
               p.FirstName as PFirst, p.LastName as PLast,
               d.FirstName as DFirst, d.LastName as DLast
        FROM Appointment a
        JOIN Patient p ON a.PatientID = p.PatientID
        JOIN Doctor d ON a.DoctorID = d.DoctorID
    '''
    if role == 'patient':
        appts = conn.execute(query + ' WHERE a.PatientID = ? ORDER BY a.AppointmentDate DESC',
                             (session.get('patient_id'),)).fetchall()
    else:
        appts = conn.execute(query + ' ORDER BY a.AppointmentDate DESC').fetchall()

    patients = conn.execute('SELECT PatientID, FirstName, LastName FROM Patient').fetchall()
    doctors = conn.execute('SELECT DoctorID, FirstName, LastName, Specialization FROM Doctor').fetchall()
    conn.close()
    return render_template('operations/appointments.html', appointments=appts, patients=patients, doctors=doctors)


@app.route('/billing')
def billing_page():
    conn = get_db_connection()
    role = session.get('role')
    query = '''
        SELECT b.BillID, b.BillDate, b.TotalAmount, b.PaidAmount, b.PaymentStatus, b.PaymentMethod,
               p.FirstName, p.LastName
        FROM Bill b
        JOIN Patient p ON b.PatientID = p.PatientID
    '''
    if role == 'patient':
        bills = conn.execute(query + ' WHERE p.PatientID = ? ORDER BY b.BillDate DESC',
                             (session.get('patient_id'),)).fetchall()
    else:
        bills = conn.execute(query + ' ORDER BY b.BillDate DESC').fetchall()

    patients = conn.execute('SELECT PatientID, FirstName, LastName FROM Patient').fetchall()
    conn.close()
    return render_template('operations/billing.html', bills=bills, patients=patients)


@app.route('/records')
def records_page():
    role = session.get('role')
    if role not in ['admin', 'doctor', 'patient']:
        flash('Access Denied.', 'error')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    if role == 'patient':
        records = conn.execute('''
            SELECT mr.*, p.FirstName as PFirst, p.LastName as PLast, d.FirstName as DFirst, d.LastName as DLast, r.RoomNumber
            FROM MedicalRecord mr
            JOIN Patient p ON mr.PatientID = p.PatientID
            JOIN Doctor d ON mr.DoctorID = d.DoctorID
            LEFT JOIN Room r ON p.PatientID = r.PatientID
            WHERE mr.PatientID = ?
        ''', (session.get('patient_id'),)).fetchall()
        tests = conn.execute(
            'SELECT mt.*, d.FirstName as DFirst, d.LastName as DLast FROM MedicalTest mt JOIN MedicalRecord mr ON mt.RecordID = mr.RecordID LEFT JOIN Doctor d ON mt.DoctorID = d.DoctorID WHERE mr.PatientID = ? ORDER BY mt.TestDate DESC',
            (session.get('patient_id'),)).fetchall()
    else:
        records = conn.execute('''
            SELECT mr.*, p.FirstName as PFirst, p.LastName as PLast, d.FirstName as DFirst, d.LastName as DLast, r.RoomNumber
            FROM MedicalRecord mr
            JOIN Patient p ON mr.PatientID = p.PatientID
            JOIN Doctor d ON mr.DoctorID = d.DoctorID
            LEFT JOIN Room r ON p.PatientID = r.PatientID
        ''').fetchall()
        tests = conn.execute(
            'SELECT mt.*, d.FirstName as DFirst, d.LastName as DLast FROM MedicalTest mt LEFT JOIN Doctor d ON mt.DoctorID = d.DoctorID ORDER BY mt.TestDate DESC').fetchall()

    patients = conn.execute('SELECT PatientID, FirstName, LastName FROM Patient').fetchall()
    doctors = conn.execute('SELECT DoctorID, FirstName, LastName FROM Doctor').fetchall()
    conn.close()
    return render_template('clinical/records.html', records=records, tests=tests, patients=patients, doctors=doctors)


@app.route('/prescriptions')
def prescriptions_page():
    conn = get_db_connection()
    role = session.get('role')

    query = '''
        SELECT p.PrescriptionID, p.Date, mr.Diagnosis, pt.FirstName as PFirst, pt.LastName as PLast, d.FirstName as DFirst, d.LastName as DLast,
               pi.MedicineName, pi.Dosage, pi.Duration
        FROM Prescription p
        JOIN MedicalRecord mr ON p.RecordID = mr.RecordID
        JOIN Patient pt ON mr.PatientID = pt.PatientID
        JOIN Doctor d ON mr.DoctorID = d.DoctorID
        LEFT JOIN Prescription_Item pi ON p.PrescriptionID = pi.PrescriptionID
    '''
    if role == 'patient':
        rx = conn.execute(query + ' WHERE mr.PatientID = ? ORDER BY p.Date DESC',
                          (session.get('patient_id'),)).fetchall()
    else:
        rx = conn.execute(query + ' ORDER BY p.Date DESC').fetchall()

    records = conn.execute(
        'SELECT mr.RecordID, mr.VisitDate, p.FirstName, p.LastName FROM MedicalRecord mr JOIN Patient p ON mr.PatientID = p.PatientID').fetchall()
    conn.close()
    return render_template('clinical/prescriptions.html', prescriptions=rx, records=records)


@app.route('/rooms')
def rooms_page():
    if session.get('role') not in ['admin', 'nurse']:
        flash('Access Denied.', 'error')
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    rooms = conn.execute(
        'SELECT r.*, p.FirstName, p.LastName FROM Room r LEFT JOIN Patient p ON r.PatientID = p.PatientID').fetchall()
    history = conn.execute(
        'SELECT ra.*, r.RoomNumber, p.FirstName, p.LastName FROM RoomAssignment ra JOIN Room r ON ra.RoomID = r.RoomID JOIN Patient p ON ra.PatientID = p.PatientID ORDER BY ra.StartDate DESC').fetchall()
    patients = conn.execute('SELECT PatientID, FirstName, LastName FROM Patient').fetchall()
    conn.close()
    return render_template('operations/rooms.html', rooms=rooms, history=history, patients=patients)


@app.route('/doctors')
def doctors_page():
    if session.get('role') != 'admin': return redirect(url_for('dashboard'))
    conn = get_db_connection()
    doctors = conn.execute(
        'SELECT d.*, dept.DepartmentName, dp.Phone FROM Doctor d LEFT JOIN Department dept ON d.DepartmentID = dept.DepartmentID LEFT JOIN Doctor_Phone dp ON d.DoctorID = dp.DoctorID GROUP BY d.DoctorID').fetchall()
    departments = conn.execute('SELECT * FROM Department').fetchall()
    conn.close()
    return render_template('staff/doctors.html', doctors=doctors, departments=departments)


@app.route('/nurses')
def nurses_page():
    if session.get('role') != 'admin': return redirect(url_for('dashboard'))
    conn = get_db_connection()
    nurses = conn.execute(
        'SELECT n.*, dept.DepartmentName, np.Phone FROM Nurse n LEFT JOIN Department dept ON n.DepartmentID = dept.DepartmentID LEFT JOIN Nurse_Phone np ON n.NurseID = np.NurseID GROUP BY n.NurseID').fetchall()
    departments = conn.execute('SELECT * FROM Department').fetchall()
    conn.close()
    return render_template('staff/nurses.html', nurses=nurses, departments=departments)


@app.route('/departments')
def departments_page():
    if session.get('role') != 'admin': return redirect(url_for('dashboard'))
    conn = get_db_connection()
    depts = conn.execute(
        'SELECT d.*, GROUP_CONCAT(dp.Phone) as Phones FROM Department d LEFT JOIN Department_Phone dp ON d.DepartmentID = dp.DepartmentID GROUP BY d.DepartmentID').fetchall()
    conn.close()
    return render_template('admin/departments.html', departments=depts)


@app.route('/doctor_schedule')
def doctor_schedule_page():
    role = session.get('role')
    if role not in ['admin', 'doctor']:
        flash('Access Denied.', 'error')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    if role == 'doctor':
        schedules = conn.execute(
            'SELECT ds.*, d.FirstName, d.LastName FROM DoctorSchedule ds JOIN Doctor d ON ds.DoctorID = d.DoctorID WHERE ds.DoctorID = ?',
            (session.get('doctor_id'),)).fetchall()
    else:
        schedules = conn.execute(
            'SELECT ds.*, d.FirstName, d.LastName FROM DoctorSchedule ds JOIN Doctor d ON ds.DoctorID = d.DoctorID').fetchall()
    doctors = conn.execute('SELECT DoctorID, FirstName, LastName FROM Doctor').fetchall()
    conn.close()
    return render_template('staff/doctor_schedule.html', schedules=schedules, doctors=doctors)


@app.route('/audit')
def audit_page():
    if session.get('role') != 'admin': return redirect(url_for('dashboard'))
    conn = get_db_connection()
    logs = conn.execute(
        'SELECT a.*, u.Username FROM AuditLog a LEFT JOIN User u ON a.UserID = u.UserID ORDER BY ActionDate DESC').fetchall()
    conn.close()
    return render_template('admin/audit.html', logs=logs)


# --- POST ROUTES (CRUD Operations) ---

@app.route('/add_user', methods=['POST'])
def add_user():
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))

    data = request.form
    username = data['username'].strip()
    password = data['password'].strip()
    role = data['role']
    is_active = int(data.get('is_active', 1))

    doctor_id = data.get('doctor_id') if data.get('doctor_id') else None
    nurse_id = data.get('nurse_id') if data.get('nurse_id') else None
    patient_id = data.get('patient_id') if data.get('patient_id') else None

    if role == 'Doctor' and not doctor_id:
        flash('Error: You must select a Doctor profile to link.', 'error')
        return redirect(url_for('users_page'))
    if role == 'Nurse' and not nurse_id:
        flash('Error: You must select a Nurse profile to link.', 'error')
        return redirect(url_for('users_page'))
    if role == 'Patient' and not patient_id:
        flash('Error: You must select a Patient profile to link.', 'error')
        return redirect(url_for('users_page'))

    conn = get_db_connection()

    existing_user = conn.execute('SELECT * FROM User WHERE Username = ?', (username,)).fetchone()
    if existing_user:
        conn.close()
        flash(f"Error: The username '{username}' already exists. Please choose a different one.", 'error')
        return redirect(url_for('users_page'))

    hashed_pw = generate_password_hash(password)

    try:
        conn.execute('''
            INSERT INTO User (Username, PasswordHash, Role, DoctorID, NurseID, PatientID, IsActive)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, hashed_pw, role, doctor_id, nurse_id, patient_id, is_active))
        conn.commit()
        log_audit(session.get('user_id'), f"Created secure user {username}", 'User')
        flash('Secure User Account created successfully.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    conn.close()
    return redirect(url_for('users_page'))


@app.route('/toggle_user/<int:id>', methods=['POST'])
def toggle_user(id):
    if session.get('role') != 'admin': return redirect(url_for('dashboard'))
    conn = get_db_connection()
    conn.execute('UPDATE User SET IsActive = NOT IsActive WHERE UserID = ?', (id,))
    conn.commit()
    conn.close()
    flash('User status updated.', 'success')
    return redirect(url_for('users_page'))


@app.route('/add_patient', methods=['POST'])
def add_patient():
    if session.get('role') not in ['admin', 'doctor', 'nurse']: return redirect(url_for('dashboard'))
    data = request.form
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO Patient (FirstName, LastName, DateOfBirth, Gender, BloodType, Street, City, ZipCode) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (data['first_name'], data['last_name'], data['dob'], data['gender'], data['blood_type'], data.get('street'),
             data.get('city'), data.get('zip_code')))
        patient_id = cursor.lastrowid

        if data.get('phone'):
            cursor.execute('INSERT INTO Patient_Phone (PatientID, Phone) VALUES (?, ?)', (patient_id, data['phone']))
        if data.get('emg_name') and data.get('emg_phone'):
            cursor.execute('INSERT INTO EmergencyContact (PatientID, Name, Relation, Phone) VALUES (?, ?, ?, ?)',
                           (patient_id, data['emg_name'], data.get('emg_relation', ''), data['emg_phone']))
        if data.get('ins_provider') and data.get('ins_policy'):
            cursor.execute('INSERT INTO Insurance (PatientID, Provider, PolicyNumber, Coverage) VALUES (?, ?, ?, ?)',
                           (patient_id, data['ins_provider'], data['ins_policy'], data.get('ins_coverage', 0)))

        conn.commit()
        log_audit(session.get('user_id'), f"Added Patient: {data['first_name']} {data['last_name']}", 'Patient',
                  patient_id)
        flash('Patient added successfully.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    conn.close()
    return redirect(url_for('patients_page'))


@app.route('/delete_patient/<int:id>', methods=['POST'])
def delete_patient(id):
    if session.get('role') not in ['admin', 'doctor']: return redirect(url_for('dashboard'))
    conn = get_db_connection()
    conn.execute('DELETE FROM Patient WHERE PatientID = ?', (id,))
    conn.commit()
    conn.close()
    flash('Patient deleted successfully!', 'success')
    return redirect(url_for('patients_page'))


@app.route('/add_doctor', methods=['POST'])
def add_doctor():
    if session.get('role') != 'admin': return redirect(url_for('dashboard'))
    data = request.form
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Doctor (FirstName, LastName, Gender, Email, Specialization, Salary, HireDate, DepartmentID)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['first_name'], data['last_name'], data['gender'], data['email'], data['specialization'],
            data['salary'],
            data['hire_date'], data['department_id']))
        doctor_id = cursor.lastrowid
        if data.get('phone'):
            cursor.execute('INSERT INTO Doctor_Phone (DoctorID, Phone) VALUES (?, ?)', (doctor_id, data['phone']))
        conn.commit()
        log_audit(session.get('user_id'), f"Added Doctor: {data['first_name']}", 'Doctor', doctor_id)
        flash('Doctor added successfully.', 'success')
    except Exception as e:
        flash(f'Error adding doctor: {str(e)}', 'error')
    conn.close()
    return redirect(url_for('doctors_page'))


@app.route('/add_nurse', methods=['POST'])
def add_nurse():
    if session.get('role') != 'admin': return redirect(url_for('dashboard'))
    data = request.form
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO Nurse (FirstName, LastName, Gender, Email, Salary, HireDate, Shift, DepartmentID) VALUES (?,?,?,?,?,?,?,?)',
            (data['first_name'], data['last_name'], data['gender'], data['email'], data['salary'], data['hire_date'],
             data['shift'], data['department_id']))
        nurse_id = cursor.lastrowid
        if data.get('phone'):
            cursor.execute('INSERT INTO Nurse_Phone (NurseID, Phone) VALUES (?, ?)', (nurse_id, data['phone']))
        conn.commit()
        flash('Nurse added successfully.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    conn.close()
    return redirect(url_for('nurses_page'))


@app.route('/add_department', methods=['POST'])
def add_department():
    if session.get('role') != 'admin': return redirect(url_for('dashboard'))
    data = request.form
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Department (DepartmentName, Building, Floor, Section) VALUES (?, ?, ?, ?)',
                       (data['department_name'], data['building'], data['floor'], data['section']))
        conn.commit()
        flash('Department added successfully.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    conn.close()
    return redirect(url_for('departments_page'))


@app.route('/add_schedule', methods=['POST'])
def add_schedule():
    if session.get('role') not in ['admin', 'doctor']: return redirect(url_for('dashboard'))
    data = request.form
    conn = get_db_connection()
    conn.execute('INSERT INTO DoctorSchedule (DoctorID, DayOfWeek, StartTime, EndTime) VALUES (?, ?, ?, ?)',
                 (data['doctor_id'], data['day_of_week'], data['start_time'], data['end_time']))
    conn.commit()
    conn.close()
    flash('Schedule added successfully.', 'success')
    return redirect(url_for('doctor_schedule_page'))


@app.route('/add_appointment', methods=['POST'])
def add_appointment():
    data = request.form
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO Appointment (PatientID, DoctorID, AppointmentDate, AppointmentTime, EndTime, AppointmentType, Status) 
        VALUES (?, ?, ?, ?, ?, ?, 'Pending')
    ''', (
        data['patient_id'], data['doctor_id'], data['date'], data['time'], data['end_time'], data['appointment_type']))
    conn.commit()
    conn.close()
    flash('Appointment booked successfully.', 'success')
    add_notification(f"New appointment booked for Date: {data['date']}")
    return redirect(url_for('appointments_page'))


@app.route('/update_appointment/<int:id>', methods=['POST'])
def update_appointment(id):
    status = request.form['status']
    conn = get_db_connection()
    conn.execute('UPDATE Appointment SET Status = ? WHERE AppointmentID = ?', (status, id))
    conn.commit()
    conn.close()
    flash('Appointment status updated.', 'success')
    return redirect(url_for('appointments_page'))


@app.route('/add_bill', methods=['POST'])
def add_bill():
    data = request.form
    today = datetime.today().strftime('%Y-%m-%d')
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO Bill (PatientID, BillDate, TotalAmount, PaidAmount, PaymentStatus) 
        VALUES (?, ?, ?, 0.00, 'Unpaid')
    ''', (data['patient_id'], today, data['total_amount']))
    conn.commit()
    conn.close()
    flash('Invoice generated successfully.', 'success')
    return redirect(url_for('billing_page'))


@app.route('/pay_bill/<int:id>', methods=['POST'])
def pay_bill(id):
    payment_amount = float(request.form['payment_amount'])
    method = request.form['payment_method']

    conn = get_db_connection()
    bill = conn.execute('SELECT * FROM Bill WHERE BillID = ?', (id,)).fetchone()

    new_paid = bill['PaidAmount'] + payment_amount
    status = 'Paid' if new_paid >= bill['TotalAmount'] else 'Partial'

    conn.execute('UPDATE Bill SET PaidAmount = ?, PaymentStatus = ?, PaymentMethod = ? WHERE BillID = ?',
                 (new_paid, status, method, id))
    conn.commit()
    conn.close()
    flash('Payment processed successfully.', 'success')
    add_notification(f"Payment of {payment_amount} received for Bill #{id}")
    return redirect(url_for('billing_page'))


@app.route('/add_record', methods=['POST'])
def add_record():
    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO MedicalRecord (PatientID, DoctorID, VisitDate, Diagnosis, Treatment, Notes) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data['patient_id'], data['doctor_id'], data['visit_date'], data['diagnosis'], data.get('treatment', ''),
          data.get('doctor_notes', '')))

    record_id = cursor.lastrowid

    if data.get('allergies'):
        allergies = [a.strip() for a in data['allergies'].split(',')]
        for a in allergies:
            if a:
                cursor.execute('INSERT INTO MedicalRecord_Allergy (RecordID, Allergy) VALUES (?, ?)', (record_id, a))

    conn.commit()
    conn.close()
    flash('Medical record created successfully.', 'success')
    return redirect(url_for('records_page'))


@app.route('/update_record/<int:id>', methods=['POST'])
def update_record(id):
    data = request.form
    conn = get_db_connection()
    conn.execute('UPDATE MedicalRecord SET Diagnosis = ?, Treatment = ?, Notes = ? WHERE RecordID = ?',
                 (data['diagnosis'], data['treatment'], data['doctor_notes'], id))
    conn.commit()
    conn.close()
    flash('Medical record updated.', 'success')
    return redirect(url_for('records_page'))


@app.route('/add_medical_test', methods=['POST'])
def add_medical_test():
    if session.get('role') not in ['admin', 'doctor']: return redirect(url_for('records_page'))
    data = request.form
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO MedicalTest (RecordID, DoctorID, TestName, Result, Unit, TestDate) VALUES (?, ?, ?, ?, ?, ?)',
        (data['record_id'], session.get('doctor_id'), data['test_name'], data['result'], data['unit'],
         data['test_date']))
    conn.commit()
    conn.close()
    flash('Medical test result added successfully.', 'success')
    return redirect(url_for('records_page'))


@app.route('/add_prescription', methods=['POST'])
def add_prescription():
    data = request.form
    today = datetime.today().strftime('%Y-%m-%d')
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('INSERT INTO Prescription (RecordID, Date) VALUES (?, ?)', (data['record_id'], today))
    rx_id = cursor.lastrowid

    cursor.execute('INSERT INTO Prescription_Item (PrescriptionID, MedicineName, Dosage, Duration) VALUES (?, ?, ?, ?)',
                   (rx_id, data['medicine_name'], data['dosage'], data['duration']))

    conn.commit()
    conn.close()
    flash('Prescription written successfully.', 'success')
    return redirect(url_for('prescriptions_page'))


@app.route('/assign_room/<int:id>', methods=['POST'])
def assign_room(id):
    patient_id = request.form['patient_id']
    today = datetime.today().strftime('%Y-%m-%d')
    conn = get_db_connection()

    conn.execute('UPDATE Room SET Status = "Occupied", PatientID = ? WHERE RoomID = ?', (patient_id, id))
    conn.execute('INSERT INTO RoomAssignment (RoomID, PatientID, StartDate) VALUES (?, ?, ?)', (id, patient_id, today))

    conn.commit()
    conn.close()
    flash('Patient assigned to room successfully.', 'success')
    add_notification(f"Room {id} assigned to a new patient.")
    return redirect(url_for('rooms_page'))


@app.route('/release_room/<int:id>', methods=['POST'])
def release_room(id):
    today = datetime.today().strftime('%Y-%m-%d')
    conn = get_db_connection()
    room = conn.execute('SELECT PatientID, Status FROM Room WHERE RoomID = ?', (id,)).fetchone()

    if room['Status'] == 'Occupied':
        conn.execute('UPDATE RoomAssignment SET EndDate = ? WHERE RoomID = ? AND PatientID = ? AND EndDate IS NULL',
                     (today, id, room['PatientID']))
        conn.execute('UPDATE Room SET Status = "Available", PatientID = NULL WHERE RoomID = ?', (id,))
        flash('Patient discharged and room released.', 'success')
    elif room['Status'] == 'Maintenance':
        conn.execute('UPDATE Room SET Status = "Available" WHERE RoomID = ?', (id,))
        flash('Room maintenance completed. Now available.', 'success')

    conn.commit()
    conn.close()
    return redirect(url_for('rooms_page'))


# --- GROK AI PREDICTION ROUTES ---
@app.route('/ai_prediction')
def ai_prediction_page():
    conn = get_db_connection()
    role = session.get('role')

    if role == 'patient':
        query = '''
            SELECT a.AppointmentID, p.FirstName, p.LastName, a.AppointmentDate 
            FROM Appointment a
            JOIN Patient p ON a.PatientID = p.PatientID
            WHERE p.PatientID = ? AND a.Status = 'Pending'
        '''
        appointments = conn.execute(query, (session.get('patient_id'),)).fetchall()
    else:
        query = '''
            SELECT a.AppointmentID, p.FirstName, p.LastName, a.AppointmentDate 
            FROM Appointment a
            JOIN Patient p ON a.PatientID = p.PatientID
            WHERE a.Status = 'Pending'
        '''
        appointments = conn.execute(query).fetchall()

    conn.close()
    return render_template('clinical/ai_prediction.html', appointments=appointments)


@app.route('/api/predict', methods=['POST'])
def analyze_symptoms():
    appointment_id = request.form.get('appointment_id')
    symptoms = request.form.get('symptoms')

    file = request.files.get('document')
    file_info = ""

    if file and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_info = f"\n[Note to AI: The user also uploaded a medical document related to these symptoms.]"

    if not symptoms and not file:
        return jsonify({'status': 'error', 'message': 'Please provide symptoms or upload a medical document.'})

    try:
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        if not GROQ_API_KEY:
            return jsonify({'status': 'error', 'message': 'API Key missing in .env file.'})

        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )

        prompt = f"Analyze these symptoms: {symptoms}. {file_info}\nReturn ONLY a valid JSON object: {{\"Predicted_Disease\": \"Disease Name\", \"Confidence_Score\": 95.5}}"

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are Medcare AI diagnostic assistant. Output ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"}
        )

        result_text = completion.choices[0].message.content
        result_json = json.loads(result_text)

        disease = result_json.get('Predicted_Disease', 'Unknown')
        score = float(result_json.get('Confidence_Score', 0.0))

        if appointment_id:
            conn = get_db_connection()
            conn.execute('DELETE FROM AI_Prediction WHERE AppointmentID = ?', (appointment_id,))
            conn.execute('''
                INSERT INTO AI_Prediction (AppointmentID, Symptoms_Input, Predicted_Disease, Confidence_Score)
                VALUES (?, ?, ?, ?)
            ''', (appointment_id, symptoms, disease, score))
            conn.commit()
            conn.close()

        add_notification(f"AI Prediction generated: {disease}")

        return jsonify({
            'status': 'success',
            'disease': disease,
            'score': score
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/chat', methods=['POST'])
def ai_chat():
    data = request.json
    messages_history = data.get('messages', [])

    try:
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        if not GROQ_API_KEY:
            return jsonify({'status': 'error', 'message': 'API Key is missing.'})

        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )

        api_messages = [
            {"role": "system",
             "content": "You are Medcare AI, a professional and helpful medical assistant. Provide concise and accurate answers."}
        ]

        for msg in messages_history:
            api_messages.append({"role": msg['role'], "content": msg['content']})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=api_messages,
        )

        reply = completion.choices[0].message.content
        return jsonify({'status': 'success', 'reply': reply})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    try:
        conn = get_db_connection()

        diseases_data = conn.execute('''
            SELECT Predicted_Disease as name, COUNT(*) as count 
            FROM AI_Prediction 
            GROUP BY Predicted_Disease 
            ORDER BY count DESC 
            LIMIT 5
        ''').fetchall()

        doctors_data = conn.execute('''
            SELECT d.LastName as name, COUNT(a.AppointmentID) as count 
            FROM Appointment a
            JOIN Doctor d ON a.DoctorID = d.DoctorID
            GROUP BY a.DoctorID
            ORDER BY count DESC
            LIMIT 5
        ''').fetchall()

        conn.close()

        diseases_list = [{"name": row["name"], "count": row["count"]} for row in diseases_data]
        doctors_list = [{"name": f"Dr. {row['name']}", "count": row["count"]} for row in doctors_data]

        return jsonify({
            'status': 'success',
            'diseases': diseases_list if diseases_list else [{"name": "No data yet", "count": 0}],
            'doctors': doctors_list if doctors_list else [{"name": "No data yet", "count": 0}]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/predict_schedule', methods=['GET'])
def predict_schedule():
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY: return jsonify({"status": "error", "message": "API Key missing."})
    try:
        conn = get_db_connection()
        total_appts = conn.execute('SELECT COUNT(*) FROM Appointment').fetchone()[0]
        pending_appts = conn.execute('SELECT COUNT(*) FROM Appointment WHERE Status = "Pending"').fetchone()[0]
        conn.close()
        client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        prompt = f"Analyze hospital load: {total_appts} appts, {pending_appts} waiting. Suggest best slots to book in 3 bullet points. English only."
        response = client.chat.completions.create(model="llama-3.3-70b-versatile",
                                                  messages=[{"role": "system", "content": "Hospital Management AI."},
                                                            {"role": "user", "content": prompt}], temperature=0.3)
        return jsonify({"status": "success", "prediction": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/api/feedback', methods=['POST'])
def ai_feedback():
    data = request.json
    appt_id = data.get('appointment_id')
    is_accurate = data.get('is_accurate')

    conn = get_db_connection()
    conn.execute('UPDATE AI_Prediction SET Is_Accurate = ? WHERE AppointmentID = ?', (is_accurate, appt_id))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(debug=True)