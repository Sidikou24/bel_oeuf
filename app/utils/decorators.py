# app/utils/decorators.py
from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user

def commercial_required(f):
    """Décorateur pour restreindre l'accès aux commerciaux"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Vous devez être connecté pour accéder à cette page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not (current_user.is_commercial() or current_user.is_responsable()):
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def responsable_required(f):
    """Décorateur pour restreindre l'accès aux responsables"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Vous devez être connecté pour accéder à cette page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_responsable():
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function