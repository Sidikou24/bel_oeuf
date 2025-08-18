# app/models/user.py
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    
    # Relations
    users = db.relationship('User', backref='role', lazy=True)
    
    def __repr__(self):
        return f'<Role {self.name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    # Informations personnelles
    prenom = db.Column(db.String(100), nullable=True)
    nom = db.Column(db.String(100), nullable=True)
    telephone = db.Column(db.String(20), nullable=True)
    
    # Relations et statut
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        """Hash et stocke le mot de passe"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    def is_commercial(self):
        """Vérifie si l'utilisateur est un commercial"""
        return self.role and self.role.name == 'commercial'
    
    def is_responsable(self):
        """Vérifie si l'utilisateur est un responsable commercial"""
        return self.role and self.role.name == 'responsable_commercial'
    
    @property
    def nom_complet(self):
        """Retourne le nom complet"""
        if self.prenom and self.nom:
            return f"{self.prenom} {self.nom}"
        return self.username
    
    def __repr__(self):
        return f'<User {self.username}>'
