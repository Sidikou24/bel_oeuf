import os
from datetime import timedelta

class Config:
    # Base
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-changez-moi-en-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ferme_oeufs.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Flask-WTF
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Uploads (si besoin)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}