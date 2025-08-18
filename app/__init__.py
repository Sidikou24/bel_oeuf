from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from app.config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'
    
    # Blueprints
    from routes.auth import bp as auth_bp
    from routes.commercial import bp as commercial_bp
    from routes.responsable import bp as responsable_bp
    from routes.admin import bp as admin_bp
    from routes.api import bp as api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(commercial_bp, url_prefix='/commercial')
    app.register_blueprint(responsable_bp, url_prefix='/responsable')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Route principale
    @app.route('/')
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            if current_user.role.name == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif current_user.role.name == 'commercial':
                return redirect(url_for('commercial.dashboard'))
            elif current_user.role.name == 'responsable_commercial':
                return redirect(url_for('responsable.dashboard'))
        return redirect(url_for('auth.login'))
    
    return app

from app import models
