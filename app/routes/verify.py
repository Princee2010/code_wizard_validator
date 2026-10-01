from flask import (Blueprint, render_template, request, current_app,
                   send_from_directory)
import sqlite3
from app.hashing import compute_certificate_hash

verify_bp = Blueprint('verify', __name__)


def get_db():
    db = sqlite3.connect(current_app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db


def log_verification(cert_id, result):
    db = sqlite3.connect(current_app.config['DATABASE'])
    db.execute('''
        INSERT INTO verification_logs
        (certificate_id, result, ip_address, user_agent, verifier_name, verifier_org)
        VALUES (?,?,?,?,?,?)
    ''', (cert_id, result, request.remote_addr,
          request.user_agent.string[:200] if request.user_agent else '',
          request.form.get('verifier_name', ''),
          request.form.get('verifier_org', '')))
    db.commit()
    db.close()


@verify_bp.route('/', methods=['GET', 'POST'])
def verify_index():
    result = None
    cert_id = ''

    if request.method == 'POST':
        cert_id = request.form.get('certificate_id', '').strip().upper()
        result = _do_verify(cert_id)

    return render_template('verify/index.html', result=result, cert_id=cert_id)


@verify_bp.route('/<cert_id>')
def verify_by_id(cert_id):
    cert_id = cert_id.strip().upper()
    result = _do_verify(cert_id)
    return render_template('verify/index.html', result=result, cert_id=cert_id)


def _do_verify(cert_id):
    if not cert_id:
        return None

    db = get_db()
    cert = db.execute(
        'SELECT * FROM certificates WHERE certificate_id=?', (cert_id,)
    ).fetchone()
    db.close()

    if not cert:
        log_verification(cert_id, 'INVALID')
        return {'status': 'NOT_FOUND', 'cert_id': cert_id}

    if cert['status'] == 'REVOKED':
        log_verification(cert_id, 'REVOKED')
        return {
            'status': 'REVOKED',
            'cert': dict(cert),
            'cert_id': cert_id,
        }

    # Hash verification
    check_data = {
        'certificate_id': cert['certificate_id'],
        'student_id':     cert['student_id'],
        'student_name':   cert['student_name'],
        'course':         cert['course'],
        'branch':         cert['branch'],
        'grade':          cert['grade'] or '',
        'issue_date':     cert['issue_date'],
        'institution_name': cert['institution_name'],
    }
    computed_hash = compute_certificate_hash(check_data)
    hash_match = computed_hash == cert['certificate_hash']

    if hash_match and cert['status'] == 'ACTIVE':
        log_verification(cert_id, 'VALID')
        return {'status': 'VALID', 'cert': dict(cert), 'cert_id': cert_id,
                'computed_hash': computed_hash}
    else:
        log_verification(cert_id, 'TAMPERED')
        return {'status': 'TAMPERED', 'cert': dict(cert), 'cert_id': cert_id,
                'computed_hash': computed_hash,
                'stored_hash': cert['certificate_hash']}
