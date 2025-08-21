from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, Commande, Client, Product, Fournisseur
from services.commercial_service import get_fournisseurs, ajouter_fournisseur_service, modifier_fournisseur_service, get_achats, ajouter_achat_service, supprimer_achat_service
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

@bp.route('/clients')
def clients():
    return render_template('commercial/clients.html')

@bp.route('/sales')
def sales():
    return render_template('commercial/sales.html')

@bp.route('/stock')
def stock():
    return render_template('commercial/stock.html')

@bp.route('/purchases')
def purchases():
    fournisseurs = get_fournisseurs()
    from services.commercial_service import get_matieres, get_stats_achats
    matieres = get_matieres()
    achats = get_achats()
    stats_achats = get_stats_achats()
    return render_template('commercial/purchases.html', approvisionnements=achats, fournisseurs=fournisseurs, matieres=matieres, stats_achats=stats_achats)

@bp.route('/purchases/ajouter', methods=['POST'])
def ajouter_achat():
    ajouter_achat_service(request.form)
    return redirect(url_for('commercial.purchases'))


@bp.route('/purchases/supprimer_achat', methods=['POST'])
def supprimer_achat():
    achat_id = request.form.get('id')
    supprimer_achat_service(achat_id)
    return redirect(url_for('commercial.purchases'))


@bp.route('/users')
def users():
    return render_template('commercial/users.html')

@bp.route('/reports')
def reports():
    return render_template('commercial/reports.html')

@bp.route('/settings')
def settings():
    return render_template('commercial/settings.html')



## ------------------------- ROUTES FOURNISSEURS -----------------------------

@bp.route('/suppliers')
def suppliers():
    from services.commercial_service import get_stats_fournisseurs
    fournisseurs = get_fournisseurs()
    stats_fournisseurs = get_stats_fournisseurs()
    return render_template('commercial/suppliers.html', fournisseurs=fournisseurs, stats_fournisseurs=stats_fournisseurs)


@bp.route('/suppliers/ajouter', methods=['POST'])
def ajouter_supplier():
    ajouter_fournisseur_service(request.form)
    return redirect(url_for('commercial.suppliers'))


# Route pour modifier un fournisseur
@bp.route('/suppliers/modifier', methods=['POST'])
def modifier_supplier():
    modifier_fournisseur_service(request.form)
    return redirect(url_for('commercial.suppliers'))


# Route pour supprimer un fournisseur
@bp.route('/suppliers/supprimer', methods=['POST'])
def supprimer_supplier():
    fournisseur_id = request.form.get('id')
    from services.commercial_service import supprimer_fournisseur_service
    supprimer_fournisseur_service(fournisseur_id)
    return redirect(url_for('commercial.suppliers'))

@bp.route('/purchases/modifier', methods=['POST'])
def modifier_achat():
    from services.commercial_service import modifier_achat_service
    modifier_achat_service(request.form)
    return redirect(url_for('commercial.purchases'))





