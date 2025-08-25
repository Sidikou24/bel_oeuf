from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import Commande, Client, Product, User
from app import db

bp = Blueprint('api', __name__)

@bp.route('/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'API is running'})

@bp.route('/commandes', methods=['GET'])
@login_required
def get_commandes():
    """Get all commandes"""
    commandes = Commande.query.all()
    return jsonify([{
        'id': c.id,
        'client_id': c.client_id,
        'date_commande': c.date_commande.isoformat(),
        'statut': c.statut
    } for c in commandes])

@bp.route('/products', methods=['GET'])
def get_products():
    """Get all products"""
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'stock': p.stock
    } for p in products])

@bp.route('/commande/<int:commande_id>', methods=['GET'])
@login_required
def get_commande_details(commande_id):
    """Get detailed information for a specific commande"""
    try:
        commande = Commande.query.get_or_404(commande_id)
        
        # Build the response with all necessary details
        response = {
            'id': commande.id,
            'numero_commande': commande.numero_commande,
            'date_creation': commande.date_creation.strftime('%d/%m/%Y %H:%M') if commande.date_creation else None,
            'date_livraison_prevue': commande.date_livraison_prevue.strftime('%d/%m/%Y') if commande.date_livraison_prevue else None,
            'statut': commande.statut,
            'montant_total': float(commande.montant_total) if commande.montant_total else 0,
            'montant_paye': float(commande.montant_paye) if commande.montant_paye else 0,
            'montant_restant': float(commande.montant_restant) if hasattr(commande, 'montant_restant') else 0,
            'pourcentage_paye': float(commande.pourcentage_paye) if hasattr(commande, 'pourcentage_paye') else 0,
            'client': {
                'id': commande.client.id,
                'nom_complet': f"{commande.client.prenom} {commande.client.nom}",
                'telephone': commande.client.telephone,
                'email': commande.client.email,
                'adresse': commande.client.adresse
            } if commande.client else None,
            'commercial': {
                'id': commande.commercial.id,
                'nom_complet': commande.commercial.nom_complet
            } if commande.commercial else None,
            'details': [],
            'notes_commercial': commande.notes_commercial,
            'commentaires_responsable': commande.commentaires_responsable
        }
        
        # Add order details (articles)
        for detail in commande.details:
            detail_data = {
                'id': detail.id,
                'product_id': detail.product_id,
                'nom_produit': detail.nom_produit,
                'quantite': detail.quantite,
                'prix_unitaire': float(detail.prix_unitaire) if detail.prix_unitaire else 0,
                'sous_total': float(detail.sous_total) if detail.sous_total else 0,
                'unite': detail.unite_produit,
                'notes': detail.notes
            }
            response['details'].append(detail_data)
        
        # Add payment history if available
        if hasattr(commande, 'paiements') and commande.paiements:
            response['paiements'] = [{
                'id': p.id,
                'date': p.date_paiement.strftime('%d/%m/%Y %H:%M') if p.date_paiement else None,
                'montant': float(p.montant) if p.montant else 0,
                'mode_paiement': p.mode_paiement,
                'reference': p.reference
            } for p in commande.paiements]
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
