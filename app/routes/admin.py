from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, Role, Commande, Client, Product
from app import db

bp = Blueprint('admin', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin/dashboard.html')

@bp.route('/users')
@login_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@bp.route('/roles')
@login_required
def roles():
    roles = Role.query.all()
    return render_template('admin/roles.html', roles=roles)
