from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import User, Commande, Client, Product, Paiement
from app import db
from sqlalchemy import or_
from datetime import datetime

bp = Blueprint('responsable', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('responsable/dashboard.html')

@bp.route('/commandes')
@login_required
def commandes():
    page = request.args.get('page', default=1, type=int)
    q = request.args.get('q', default='', type=str) or ''
    statut = request.args.get('statut', default='tous', type=str) or 'tous'

    # Mapping convivial -> statut en base
    statut_map = {
        'en_cours': 'en_attente'
    }
    statut_val = statut_map.get(statut, statut)

    query = Commande.query.join(Client).order_by(Commande.date_creation.desc())

    if statut_val and statut_val != 'tous':
        query = query.filter(Commande.statut == statut_val)

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Commande.numero_commande.ilike(pattern),
                Client.nom.ilike(pattern),
                Client.prenom.ilike(pattern)
            )
        )

    pagination = query.paginate(page=page, per_page=20, error_out=False)

    return render_template(
        'responsable/commandes.html',
        pagination=pagination,
        commandes=pagination.items,
        q=q,
        statut=statut,
        total_commandes=pagination.total
    )

@bp.route('/commandes/<int:commande_id>/details', methods=['GET'])
@login_required
def commande_details(commande_id):
    cmd = Commande.query.get_or_404(commande_id)
    details = []
    try:
        for d in cmd.details:
            produit_nom = getattr(d.product, 'name', 'Produit') if hasattr(d, 'product') else 'Produit'
            prix = float(getattr(d, 'prix_unitaire', 0) or 0)
            total = float(getattr(d, 'sous_total', prix * float(getattr(d, 'quantite', 0) or 0)))
            details.append({
                'produit': produit_nom,
                'quantite': int(getattr(d, 'quantite', 0) or 0),
                'prix_unitaire': prix,
                'total': total
            })
    except Exception:
        details = []

    paiements = []
    try:
        for p in cmd.paiements:
            montant = float(getattr(p, 'montant', 0) or 0)
            date = getattr(p, 'date_paiement', None)
            paiements.append({
                'date': date.strftime('%d/%m/%Y') if date else '',
                'montant': montant,
                'mode': p.mode_paiement_display
            })
    except Exception:
        paiements = []

    return jsonify({
        'id': cmd.id,
        'numero_commande': cmd.numero_commande,
        'client': {
            'nom': cmd.client.nom if cmd.client else '',
            'prenom': cmd.client.prenom if cmd.client else ''
        },
        'date_creation': cmd.date_creation.strftime('%d/%m/%Y') if cmd.date_creation else '',
        'statut': cmd.statut,
        'montant_total': float(cmd.montant_total or 0),
        'montant_paye': float(cmd.montant_paye or 0),
        'pourcentage_paye': cmd.pourcentage_paye,
        'details': details,
        'paiements': paiements
    })

@bp.route('/commandes/<int:commande_id>/valider', methods=['POST'])
@login_required
def commande_valider(commande_id):
    cmd = Commande.query.get_or_404(commande_id)
    try:
        data = request.get_json(silent=True) or request.form
        commentaires = (data.get('commentaires') or '').strip() if data else None
        cmd.valider(current_user, commentaires=commentaires)
        db.session.commit()
        return jsonify({'success': True, 'statut': cmd.statut})
    except ValueError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': "Erreur serveur lors de la validation"}), 500

@bp.route('/commandes/<int:commande_id>/annuler', methods=['POST'])
@login_required
def commande_annuler(commande_id):
    cmd = Commande.query.get_or_404(commande_id)
    try:
        data = request.get_json(silent=True) or request.form
        motif = (data.get('motif') or '').strip() if data else ''
        if not motif:
            return jsonify({'success': False, 'error': 'Le motif est obligatoire'}), 400
        cmd.annuler(current_user, motif)
        db.session.commit()
        return jsonify({'success': True, 'statut': cmd.statut})
    except ValueError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': "Erreur serveur lors de l'annulation"}), 500

@bp.route('/paiements')
@login_required
def paiements():
    page = request.args.get('page', default=1, type=int)
    q = request.args.get('q', default='', type=str) or ''

    # Résumé global
    total_a_recevoir = db.session.query(db.func.coalesce(db.func.sum(Commande.montant_total), 0)).scalar() or 0
    total_paye = db.session.query(db.func.coalesce(db.func.sum(Commande.montant_paye), 0)).scalar() or 0
    diff_reste = float(total_a_recevoir) - float(total_paye)
    reste = diff_reste if diff_reste > 0 else 0.0

    # Listing par commande + client
    query = Commande.query.join(Client).order_by(Commande.date_creation.desc())
    if q:
        pat = f"%{q}%"
        query = query.filter(or_(
            Commande.numero_commande.ilike(pat),
            Client.nom.ilike(pat),
            Client.prenom.ilike(pat)
        ))
    pagination = query.paginate(page=page, per_page=15, error_out=False)

    # Précharger paiements pour chaque commande (lazy access en template)
    return render_template('responsable/paiements.html',
                           pagination=pagination,
                           commandes=pagination.items,
                           q=q,
                           resume={
                               'total_a_recevoir': float(total_a_recevoir),
                               'total_paye': float(total_paye),
                               'reste': float(reste)
                           },
                           modes=Paiement.get_modes_paiement())

@bp.route('/paiements/creer', methods=['POST'])
@login_required
def paiement_creer():
    try:
        data = request.get_json(silent=True) or request.form
        if not data:
            return jsonify({'success': False, 'error': 'Données manquantes'}), 400
        commande_id = data.get('commande_id')
        montant = data.get('montant')
        mode = data.get('mode')
        date_str = data.get('date')

        if not commande_id or not montant or not mode or not date_str:
            return jsonify({'success': False, 'error': 'Champs requis manquants'}), 400
        try:
            commande_id = int(commande_id)
            montant = float(montant)
            if montant <= 0:
                return jsonify({'success': False, 'error': 'Montant invalide'}), 400
        except ValueError:
            return jsonify({'success': False, 'error': 'Paramètres invalides'}), 400

        try:
            date_p = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'error': 'Date invalide (YYYY-MM-DD)'}), 400

        cmd = Commande.query.get_or_404(commande_id)
        modes_valides = {k for k, _ in Paiement.get_modes_paiement()}
        if mode not in modes_valides:
            return jsonify({'success': False, 'error': 'Mode de paiement invalide'}), 400

        paiement = Paiement(
            commande_id=cmd.id,
            montant=montant,
            mode_paiement=mode,
            date_paiement=date_p,
            created_by_user_id=current_user.id,
            statut='encaisse',
            validated_by_user_id=current_user.id,
        )
        db.session.add(paiement)
        # Mettre à jour le montant payé de la commande
        cmd.montant_paye = (float(cmd.montant_paye) if cmd.montant_paye else 0) + montant
        db.session.commit()
        return jsonify({'success': True})
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erreur serveur lors de la création du paiement'}), 500

@bp.route('/stats')
@login_required
def stats():
    return render_template('responsable/stats.html')
