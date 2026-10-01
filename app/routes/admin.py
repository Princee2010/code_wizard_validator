from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, send_from_directory, current_app, jsonify, abort)
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps
import sqlite3, os
from datetime import datetime

from app.hashing import generate_certificate_id, compute_certificate_hash
from app.qr_generator import generate_qr_code
from app.pdf_generator import generate_certificate_pdf

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated


def get_db():
    return sqlite3.connect(current_app.config['DATABASE'],
                           detect_types=sqlite3.PARSE_DECLTYPES)


def log_audit(action, cert_id=None, student_id=None, details=None):
    db = get_db()
    db.row_factory = sqlite3.Row
    db.execute('''INSERT INTO audit_logs
        (user_id, user_name, action, certificate_id, student_id, ip_address, details)
        VALUES (?,?,?,?,?,?,?)''',
        (current_user.id, current_user.name, action, cert_id, student_id,
         request.remote_addr, details))
    db.commit()
    db.close()


# ── Dashboard ──────────────────────────────────────────────────────────────
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    db = get_db()
    db.row_factory = sqlite3.Row

    stats = {
        'students':     db.execute('SELECT COUNT(*) FROM students').fetchone()[0],
        'issued':       db.execute('SELECT COUNT(*) FROM certificates').fetchone()[0],
        'verified':     db.execute('SELECT COUNT(*) FROM verification_logs').fetchone()[0],
        'revoked':      db.execute("SELECT COUNT(*) FROM certificates WHERE status='REVOKED'").fetchone()[0],
        'invalid':      db.execute("SELECT COUNT(*) FROM verification_logs WHERE result='INVALID'").fetchone()[0],
        'this_month':   db.execute(
            "SELECT COUNT(*) FROM certificates WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
        ).fetchone()[0],
    }

    monthly = [dict(r) for r in db.execute('''
        SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as cnt
        FROM certificates
        GROUP BY month ORDER BY month DESC LIMIT 12
    ''').fetchall()]

    verify_trend = [dict(r) for r in db.execute('''
        SELECT strftime('%Y-%m', verification_time) as month,
               SUM(CASE WHEN result='VALID' THEN 1 ELSE 0 END) as valid,
               SUM(CASE WHEN result!='VALID' THEN 1 ELSE 0 END) as invalid
        FROM verification_logs
        GROUP BY month ORDER BY month DESC LIMIT 6
    ''').fetchall()]

    recent_certs = db.execute('''
        SELECT c.*, s.name as student_name
        FROM certificates c
        LEFT JOIN students s ON c.student_id = s.student_id
        ORDER BY c.created_at DESC LIMIT 8
    ''').fetchall()

    recent_verifications = db.execute('''
        SELECT * FROM verification_logs ORDER BY verification_time DESC LIMIT 8
    ''').fetchall()

    audit_logs = db.execute('''
        SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 10
    ''').fetchall()

    db.close()
    return render_template('admin/dashboard.html',
        stats=stats, monthly=monthly, verify_trend=verify_trend,
        recent_certs=recent_certs, recent_verifications=recent_verifications,
        audit_logs=audit_logs)


# ── Students ───────────────────────────────────────────────────────────────
@admin_bp.route('/students')
@admin_required
def students():
    db = get_db(); db.row_factory = sqlite3.Row
    q = request.args.get('q', '')
    course = request.args.get('course', '')
    batch = request.args.get('batch', '')

    query = 'SELECT * FROM students WHERE 1=1'
    params = []
    if q:
        query += ' AND (name LIKE ? OR student_id LIKE ? OR email LIKE ?)'
        params += [f'%{q}%', f'%{q}%', f'%{q}%']
    if course:
        query += ' AND course = ?'; params.append(course)
    if batch:
        query += ' AND batch = ?'; params.append(batch)
    query += ' ORDER BY created_at DESC'

    students_list = db.execute(query, params).fetchall()
    courses = db.execute('SELECT DISTINCT course FROM students').fetchall()
    batches = db.execute('SELECT DISTINCT batch FROM students').fetchall()
    db.close()
    return render_template('admin/students.html',
        students=students_list, courses=courses, batches=batches,
        q=q, course=course, batch=batch)


@admin_bp.route('/students/add', methods=['GET', 'POST'])
@admin_required
def add_student():
    if request.method == 'POST':
        f = request.form
        db = get_db()
        try:
            db.execute('''
                INSERT INTO students (student_id, enrollment_number, name, email, phone,
                    course, branch, semester, batch, college, admission_year, graduation_year)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (f['student_id'], f.get('enrollment_number'), f['name'], f['email'],
                  f.get('phone'), f['course'], f['branch'], f.get('semester'),
                  f['batch'], f['college'], f.get('admission_year'), f.get('graduation_year')))

            # create student login
            db.execute('''
                INSERT OR IGNORE INTO users (name, email, password_hash, role, student_id)
                VALUES (?,?,?,?,?)
            ''', (f['name'], f['email'],
                  generate_password_hash(f.get('password', 'student123')),
                  'student', f['student_id']))
            db.commit()
            log_audit('STUDENT_ADDED', student_id=f['student_id'],
                      details=f"Added student: {f['name']}")
            flash(f"Student {f['name']} added successfully.", 'success')
        except sqlite3.IntegrityError as e:
            flash(f'Error: {e}', 'error')
        finally:
            db.close()
        return redirect(url_for('admin.students'))

    return render_template('admin/add_student.html')


@admin_bp.route('/students/edit/<student_id>', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    db = get_db(); db.row_factory = sqlite3.Row
    student = db.execute('SELECT * FROM students WHERE student_id=?', (student_id,)).fetchone()
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('admin.students'))

    if request.method == 'POST':
        f = request.form
        db.execute('''UPDATE students SET name=?, email=?, phone=?, course=?, branch=?,
            semester=?, batch=?, college=?, admission_year=?, graduation_year=?
            WHERE student_id=?''',
            (f['name'], f['email'], f.get('phone'), f['course'], f['branch'],
             f.get('semester'), f['batch'], f['college'],
             f.get('admission_year'), f.get('graduation_year'), student_id))
        db.commit()
        log_audit('STUDENT_UPDATED', student_id=student_id)
        flash('Student updated.', 'success')
        db.close()
        return redirect(url_for('admin.students'))

    db.close()
    return render_template('admin/add_student.html', student=student)


@admin_bp.route('/students/delete/<student_id>', methods=['POST'])
@admin_required
def delete_student(student_id):
    db = get_db()
    db.execute('DELETE FROM students WHERE student_id=?', (student_id,))
    db.commit(); db.close()
    log_audit('STUDENT_DELETED', student_id=student_id)
    flash('Student deleted.', 'success')
    return redirect(url_for('admin.students'))


# ── Certificates ───────────────────────────────────────────────────────────
@admin_bp.route('/certificates')
@admin_required
def certificates():
    db = get_db(); db.row_factory = sqlite3.Row
    q = request.args.get('q', '')
    status = request.args.get('status', '')

    query = 'SELECT * FROM certificates WHERE 1=1'
    params = []
    if q:
        query += ' AND (certificate_id LIKE ? OR student_name LIKE ? OR student_id LIKE ?)'
        params += [f'%{q}%', f'%{q}%', f'%{q}%']
    if status:
        query += ' AND status=?'; params.append(status)
    query += ' ORDER BY created_at DESC'

    certs = db.execute(query, params).fetchall()
    db.close()
    return render_template('admin/certificates.html', certificates=certs, q=q, status=status)


@admin_bp.route('/certificates/create', methods=['GET', 'POST'])
@admin_required
def create_certificate():
    db = get_db(); db.row_factory = sqlite3.Row
    students_list = db.execute('SELECT * FROM students ORDER BY name').fetchall()
    institution = db.execute('SELECT * FROM institution_info LIMIT 1').fetchone()

    if request.method == 'POST':
        f = request.form
        student = db.execute('SELECT * FROM students WHERE student_id=?',
                             (f['student_id'],)).fetchone()
        if not student:
            flash('Student not found.', 'error')
            return redirect(url_for('admin.create_certificate'))

        course_code = ''.join([w[0] for w in f['branch'].split()[:3]]).upper() or 'GEN'
        cert_id = generate_certificate_id(course_code)

        cert_data = {
            'certificate_id': cert_id,
            'student_id': f['student_id'],
            'student_name': student['name'],
            'course': f['course'],
            'branch': f['branch'],
            'grade': f.get('grade', ''),
            'issue_date': f['issue_date'],
            'institution_name': institution['name'] if institution else 'XYZ University',
        }
        cert_hash = compute_certificate_hash(cert_data)

        # Generate QR
        base_url = request.host_url.rstrip('/')
        qr_filename = generate_qr_code(cert_id, base_url, current_app.config['QR_FOLDER'])
        qr_path = os.path.join(current_app.config['QR_FOLDER'], qr_filename)

        # Generate PDF
        pdf_cert_data = {**cert_data,
            'certificate_type': f['certificate_type'],
            'achievement': f.get('achievement', ''),
            'percentage': f.get('percentage'),
            'academic_year': f.get('academic_year', ''),
            'issuer_name': f.get('issuer_name', current_user.name),
            'certificate_hash': cert_hash,
            'accreditation': institution['accreditation'] if institution else '',
            'base_url': base_url,
        }
        pdf_filename = generate_certificate_pdf(pdf_cert_data, qr_path, current_app.config['UPLOAD_FOLDER'])

        db.execute('''
            INSERT INTO certificates
            (certificate_id, student_id, student_name, certificate_type, course, branch,
             achievement, grade, percentage, academic_year, issue_date, issuer_name,
             institution_name, certificate_hash, qr_path, pdf_path, created_by)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (cert_id, f['student_id'], student['name'], f['certificate_type'],
              f['course'], f['branch'], f.get('achievement'), f.get('grade'),
              f.get('percentage') or None, f.get('academic_year'),
              f['issue_date'], f.get('issuer_name', current_user.name),
              institution['name'] if institution else 'XYZ University',
              cert_hash, qr_filename, pdf_filename, current_user.id))
        db.commit()
        log_audit('CERTIFICATE_CREATED', cert_id=cert_id,
                  student_id=f['student_id'],
                  details=f"Type: {f['certificate_type']}")
        flash(f'Certificate {cert_id} created successfully!', 'success')
        db.close()
        return redirect(url_for('admin.view_certificate', cert_id=cert_id))

    db.close()
    return render_template('admin/create_certificate.html',
                           students=students_list, institution=institution)


@admin_bp.route('/certificates/<cert_id>')
@admin_required
def view_certificate(cert_id):
    db = get_db(); db.row_factory = sqlite3.Row
    cert = db.execute('SELECT * FROM certificates WHERE certificate_id=?', (cert_id,)).fetchone()
    if not cert:
        flash('Certificate not found.', 'error')
        return redirect(url_for('admin.certificates'))
    verif_logs = db.execute(
        'SELECT * FROM verification_logs WHERE certificate_id=? ORDER BY verification_time DESC',
        (cert_id,)).fetchall()
    db.close()
    return render_template('admin/view_certificate.html', cert=cert, logs=verif_logs)


@admin_bp.route('/certificates/revoke/<cert_id>', methods=['POST'])
@admin_required
def revoke_certificate(cert_id):
    reason = request.form.get('reason', 'No reason provided')
    db = get_db()
    db.execute('''UPDATE certificates SET status='REVOKED', revocation_reason=?,
        revoked_at=CURRENT_TIMESTAMP, revoked_by=? WHERE certificate_id=?''',
        (reason, current_user.id, cert_id))
    db.commit(); db.close()
    log_audit('CERTIFICATE_REVOKED', cert_id=cert_id, details=reason)
    flash(f'Certificate {cert_id} has been revoked.', 'warning')
    return redirect(url_for('admin.view_certificate', cert_id=cert_id))


@admin_bp.route('/certificates/download/<cert_id>')
@admin_required
def download_certificate(cert_id):
    db = get_db(); db.row_factory = sqlite3.Row
    cert = db.execute('SELECT pdf_path FROM certificates WHERE certificate_id=?', (cert_id,)).fetchone()
    db.close()
    if not cert or not cert['pdf_path']:
        flash('PDF not found.', 'error')
        return redirect(url_for('admin.certificates'))
    log_audit('CERTIFICATE_DOWNLOADED', cert_id=cert_id)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'],
                               cert['pdf_path'], as_attachment=True)


# ── Audit Logs ─────────────────────────────────────────────────────────────
@admin_bp.route('/audit-logs')
@admin_required
def audit_logs():
    db = get_db(); db.row_factory = sqlite3.Row
    logs = db.execute('SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 200').fetchall()
    db.close()
    return render_template('admin/audit_logs.html', logs=logs)


# ── Verification History ───────────────────────────────────────────────────
@admin_bp.route('/verification-history')
@admin_required
def verification_history():
    db = get_db(); db.row_factory = sqlite3.Row
    logs = db.execute(
        'SELECT * FROM verification_logs ORDER BY verification_time DESC LIMIT 200'
    ).fetchall()
    db.close()
    return render_template('admin/verification_history.html', logs=logs)


# ── Institution Settings ───────────────────────────────────────────────────
@admin_bp.route('/institution', methods=['GET', 'POST'])
@admin_required
def institution():
    db = get_db(); db.row_factory = sqlite3.Row
    inst = db.execute('SELECT * FROM institution_info LIMIT 1').fetchone()

    if request.method == 'POST':
        f = request.form
        if inst:
            db.execute('''UPDATE institution_info SET name=?,address=?,city=?,state=?,country=?,
                phone=?,email=?,website=?,established_year=?,accreditation=?,updated_at=CURRENT_TIMESTAMP
                WHERE id=?''',
                (f['name'], f['address'], f['city'], f['state'], f['country'],
                 f['phone'], f['email'], f['website'], f.get('established_year'),
                 f['accreditation'], inst['id']))
        else:
            db.execute('''INSERT INTO institution_info
                (name,address,city,state,country,phone,email,website,established_year,accreditation)
                VALUES (?,?,?,?,?,?,?,?,?,?)''',
                (f['name'], f['address'], f['city'], f['state'], f['country'],
                 f['phone'], f['email'], f['website'], f.get('established_year'),
                 f['accreditation']))
        db.commit(); db.close()
        log_audit('INSTITUTION_UPDATED')
        flash('Institution info updated.', 'success')
        return redirect(url_for('admin.institution'))

    db.close()
    return render_template('admin/institution.html', institution=inst)
