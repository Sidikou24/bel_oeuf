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
    page = request.args.get('page', default=1, type=int)
    q = request.args.get('q', default='', type=str) or ''
    pagination = CommercialService.get_clients_paginated(page=page, per_page=20, search=q)
    total_clients = pagination.total
    return render_template(
        'commercial/clients.html',
        pagination=pagination,
        clients=pagination.items,
        q=q,
        total_clients=total_clients
    )

@bp.route('/clients/nouveau', methods=['POST'])
@login_required
@commercial_required
def creer_client():
    try:
        client = CommercialService.creer_client(
            nom=request.form.get('nom'),
            prenom=request.form.get('prenom'),
            telephone=request.form.get('telephone'),
            email=request.form.get('email'),
            adresse=request.form.get('adresse'),
            ville=request.form.get('ville'),
            code_postal=request.form.get('code_postal'),
            notes=request.form.get('notes'),
            created_by_user_id=current_user.id
        )
        flash('Client créé avec succès', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception:
        db.session.rollback()
        flash("Une erreur est survenue lors de la création du client", 'danger')
    return redirect(url_for('commercial.clients'))

@bp.route('/clients/<int:client_id>/modifier', methods=['POST'])
@login_required
@commercial_required
def modifier_client(client_id):
    try:
        data = {
            'nom': request.form.get('nom'),
            'prenom': request.form.get('prenom'),
            'telephone': request.form.get('telephone'),
            'email': request.form.get('email'),
            'adresse': request.form.get('adresse'),
            'ville': request.form.get('ville'),
            'code_postal': request.form.get('code_postal'),
            'notes': request.form.get('notes')
        }
        # Nettoyer les valeurs vides -> None
        data = {k: (v if v is not None and v.strip() != '' else None) for k, v in data.items()}
        CommercialService.modifier_client(client_id, **data)
        flash('Client modifié avec succès', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception:
        db.session.rollback()
        flash("Une erreur est survenue lors de la modification du client", 'danger')
    return redirect(url_for('commercial.clients'))

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

