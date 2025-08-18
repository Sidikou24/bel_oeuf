from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, Commande, Client, Product, DetailCommande
from app import db

from app.forms.commercial import ClientForm, CommandeForm, ProduitCommandeForm
from app.services.commercial_service import CommercialService
from app.utils.decorators import commercial_required
from datetime import datetime
bp = Blueprint('commercial', __name__)

@bp.route('/dashboard')
@login_required
@commercial_required
def dashboard():
    return render_template('commercial/dashboard.html')

@bp.route('/commandes')
@login_required
@commercial_required
def commandes():
    return render_template('commercial/commandes.html')

@bp.route('/stats')
@login_required
@commercial_required
def stats():
    return render_template('commercial/stats.html')

@bp.route('/clients')
@login_required
@commercial_required
def clients():
    return render_template('commercial/clients.html')

@bp.route('/sales')
@login_required
@commercial_required
def sales():
    return render_template('commercial/sales.html')

@bp.route('/stock')
@login_required
@commercial_required
def stock():
    return render_template('commercial/stock.html')

@bp.route('/purchases')
@login_required
@commercial_required
def purchases():
    return render_template('commercial/purchases.html')

@bp.route('/suppliers')
@login_required
@commercial_required
def suppliers():
    return render_template('commercial/suppliers.html')

@bp.route('/users')
@login_required
@commercial_required
def users():
    return render_template('commercial/users.html')

@bp.route('/reports')
@login_required
@commercial_required
def reports():
    return render_template('commercial/reports.html')

@bp.route('/settings')
@login_required
@commercial_required
def settings():
    return render_template('commercial/settings.html')

