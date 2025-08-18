from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, Commande, Client, Product
from app import db

bp = Blueprint('responsable', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('responsable/dashboard.html')

@bp.route('/commandes')
@login_required
def commandes():
    return render_template('responsable/commandes.html')

@bp.route('/stats')
@login_required
def stats():
    return render_template('responsable/stats.html')
