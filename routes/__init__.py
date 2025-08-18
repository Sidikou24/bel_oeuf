from flask import Flask
from .auth import bp as auth_bp
from .commercial import bp as commercial_bp
from .responsable import bp as responsable_bp
from .admin import bp as admin_bp
from .api import bp as api_bp

def init_routes(app):
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(commercial_bp, url_prefix='/commercial')
    app.register_blueprint(responsable_bp, url_prefix='/responsable')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
