import sqlite3
from werkzeug.security import generate_password_hash
from flask import current_app
from datetime import datetime


def seed_data():
    """Seed initial admin, verifier, student users and institution info."""
    db = sqlite3.connect(current_app.config['DATABASE'])
    db.row_factory = sqlite3.Row

    # Check if already seeded
    existing = db.execute('SELECT COUNT(*) as c FROM users').fetchone()
    if existing['c'] > 0:
        db.close()
        return

    # Admin user
    db.execute('''
        INSERT INTO users (name, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    ''', ('Admin', 'admin@acv.edu', generate_password_hash('admin123'), 'admin'))

    # Verifier user
    db.execute('''
        INSERT INTO users (name, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    ''', ('Verifier', 'verify@company.com', generate_password_hash('verify123'), 'verifier'))

    # Sample student record
    db.execute('''
        INSERT INTO students (student_id, enrollment_number, name, email, phone,
            course, branch, semester, batch, college, admission_year, graduation_year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('24IT006', 'EN24IT006', 'Princee Bhingradiya', 'princee@student.edu',
          '9876543210', 'B.Tech', 'Information Technology', '6',
          '2024-2028', 'XYZ University', 2024, 2028))

    # Student user linked to student record
    db.execute('''
        INSERT INTO users (name, email, password_hash, role, student_id)
        VALUES (?, ?, ?, ?, ?)
    ''', ('Princee Bhingradiya', 'princee@student.edu',
          generate_password_hash('student123'), 'student', '24IT006'))

    # Institution info
    db.execute('''
        INSERT INTO institution_info (name, address, city, state, country,
            phone, email, website, established_year, accreditation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('XYZ University', '123 University Road', 'Ahmedabad', 'Gujarat', 'India',
          '+91-79-12345678', 'info@xyz.edu', 'www.xyz.edu', 1994,
          'NAAC A++ | NBA Accredited'))

    db.commit()
    db.close()
