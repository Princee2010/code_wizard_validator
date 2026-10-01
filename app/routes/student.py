from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, send_from_directory, current_app)
from flask_login import login_required, current_user
from functools import wraps
import sqlite3

student_bp = Blueprint('student', __name__)


def student_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'student':
            flash('Access denied.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def get_db():
    db = sqlite3.connect(current_app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db


@student_bp.route('/dashboard')
@student_required
def dashboard():
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE student_id=?',
                         (current_user.student_id,)).fetchone()
    certs = db.execute(
        'SELECT * FROM certificates WHERE student_id=? ORDER BY created_at DESC',
        (current_user.student_id,)).fetchall()
    db.close()
    return render_template('student/dashboard.html', student=student, certificates=certs)


@student_bp.route('/certificate/<cert_id>')
@student_required
def view_certificate(cert_id):
    db = get_db()
    cert = db.execute(
        'SELECT * FROM certificates WHERE certificate_id=? AND student_id=?',
        (cert_id, current_user.student_id)).fetchone()
    if not cert:
        flash('Certificate not found.', 'error')
        return redirect(url_for('student.dashboard'))
    db.close()
    return render_template('student/view_certificate.html', cert=cert)


@student_bp.route('/certificate/download/<cert_id>')
@student_required
def download_certificate(cert_id):
    db = get_db()
    cert = db.execute(
        'SELECT pdf_path FROM certificates WHERE certificate_id=? AND student_id=?',
        (cert_id, current_user.student_id)).fetchone()
    db.close()
    if not cert or not cert['pdf_path']:
        flash('PDF not found.', 'error')
        return redirect(url_for('student.dashboard'))
    return send_from_directory(current_app.config['UPLOAD_FOLDER'],
                               cert['pdf_path'], as_attachment=True)
