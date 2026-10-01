from flask import Blueprint, jsonify, request, current_app
import sqlite3

api_bp = Blueprint('api', __name__)


def get_db():
    db = sqlite3.connect(current_app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db


@api_bp.route('/stats')
def stats():
    db = get_db()
    data = {
        'students':   db.execute('SELECT COUNT(*) FROM students').fetchone()[0],
        'issued':     db.execute('SELECT COUNT(*) FROM certificates').fetchone()[0],
        'verified':   db.execute('SELECT COUNT(*) FROM verification_logs').fetchone()[0],
        'revoked':    db.execute("SELECT COUNT(*) FROM certificates WHERE status='REVOKED'").fetchone()[0],
        'monthly': [dict(r) for r in db.execute('''
            SELECT strftime("%Y-%m", created_at) as month, COUNT(*) as cnt
            FROM certificates GROUP BY month ORDER BY month DESC LIMIT 12
        ''').fetchall()],
    }
    db.close()
    return jsonify(data)


@api_bp.route('/verify/<cert_id>')
def verify_api(cert_id):
    db = get_db()
    cert = db.execute('SELECT * FROM certificates WHERE certificate_id=?',
                      (cert_id.upper(),)).fetchone()
    db.close()
    if not cert:
        return jsonify({'status': 'NOT_FOUND'}), 404
    return jsonify({'status': cert['status'], 'certificate_id': cert['certificate_id'],
                    'student_name': cert['student_name'], 'course': cert['course'],
                    'institution': cert['institution_name'], 'issue_date': cert['issue_date']})


@api_bp.route('/students/search')
def search_students():
    q = request.args.get('q', '')
    db = get_db()
    students = db.execute(
        'SELECT student_id, name, course, branch FROM students WHERE name LIKE ? OR student_id LIKE ? LIMIT 10',
        (f'%{q}%', f'%{q}%')).fetchall()
    db.close()
    return jsonify([dict(s) for s in students])
