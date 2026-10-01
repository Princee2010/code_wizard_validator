from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models import User
from app.database import get_db, execute_db
import sqlite3
from flask import current_app

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.get_by_email(email)
        pwd_hash = User.get_password_hash(email)

        if user and pwd_hash and check_password_hash(pwd_hash, password) and user.is_active:
            login_user(user, remember=remember)
            _log_audit(user, 'USER_LOGIN', ip=request.remote_addr)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for(f'{user.role}.dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    _log_audit(current_user, 'USER_LOGOUT', ip=request.remote_addr)
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))


def _log_audit(user, action, ip=None, cert_id=None, details=None):
    db = sqlite3.connect(current_app.config['DATABASE'])
    db.execute('''
        INSERT INTO audit_logs (user_id, user_name, action, certificate_id, ip_address, details)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user.id, user.name, action, cert_id, ip, details))
    db.commit()
    db.close()
