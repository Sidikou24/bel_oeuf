from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User, Role
from app import db

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role_name = request.form['role']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Vérifier que le rôle correspond
            if user.role and user.role.name == role_name:
                login_user(user)
                
                # Redirection basée sur le rôle
                if role_name == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif role_name == 'commercial':
                    return redirect(url_for('commercial.dashboard'))
                elif role_name == 'responsable_commercial':
                    return redirect(url_for('responsable.dashboard'))
                else:
                    flash('Rôle non reconnu')
                    return redirect(url_for('auth.login'))
            else:
                flash('Le rôle sélectionné ne correspond pas à votre compte')
                return redirect(url_for('auth.login'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect')
    
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('auth/register.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
