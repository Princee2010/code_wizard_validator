from flask_login import UserMixin
import sqlite3
from flask import current_app


class User(UserMixin):
    def __init__(self, id, name, email, role, student_id=None, is_active=True):
        self.id = id
        self.name = name
        self.email = email
        self.role = role
        self.student_id = student_id
        self._is_active = is_active

    @property
    def is_active(self):
        return bool(self._is_active)

    @staticmethod
    def get_by_id(user_id):
        db = sqlite3.connect(current_app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        db.close()
        if row:
            return User(row['id'], row['name'], row['email'], row['role'],
                        row['student_id'], row['is_active'])
        return None

    @staticmethod
    def get_by_email(email):
        db = sqlite3.connect(current_app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        row = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        db.close()
        if row:
            return User(row['id'], row['name'], row['email'], row['role'],
                        row['student_id'], row['is_active'])
        return None

    @staticmethod
    def get_password_hash(email):
        db = sqlite3.connect(current_app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        row = db.execute('SELECT password_hash FROM users WHERE email = ?', (email,)).fetchone()
        db.close()
        return row['password_hash'] if row else None
