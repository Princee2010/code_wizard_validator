from flask import Flask
from flask_login import LoginManager
from .database import init_db
from .models import User
import os

login_manager = LoginManager()

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config['SECRET_KEY'] = os.urandom(32).hex()
    app.config['DATABASE'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'certificates.db')
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'certificates')
    app.config['QR_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'qrcodes')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['QR_FOLDER'], exist_ok=True)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))

    with app.app_context():
        init_db()
        from .seed import seed_data
        seed_data()

    from .routes.auth import auth_bp
    from .routes.admin import admin_bp
    from .routes.student import student_bp
    from .routes.verify import verify_bp
    from .routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(verify_bp, url_prefix='/verify')
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
