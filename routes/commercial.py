from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, Commande, Client, Product
from app import db

bp = Blueprint('commercial', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('commercial/dashboard.html')

@bp.route('/commandes')
@login_required
def commandes():
    return render_template('commercial/commandes.html')

@bp.route('/stats')
@login_required
def stats():
    return render_template('commercial/stats.html')
# @bp.route('/clients')
# def clients():
#     return render_template('commercial/clients.html')

@bp.route('/sales')
def sales():
    return render_template('commercial/sales.html')

@bp.route('/stock')
def stock():
    return render_template('commercial/stock.html')

@bp.route('/purchases')
def purchases():
    return render_template('commercial/purchases.html')

@bp.route('/suppliers')
def suppliers():
    return render_template('commercial/suppliers.html')

@bp.route('/users')
def users():
    return render_template('commercial/users.html')

@bp.route('/reports')
def reports():
    return render_template('commercial/reports.html')

@bp.route('/settings')
def settings():
    return render_template('commercial/settings.html')

