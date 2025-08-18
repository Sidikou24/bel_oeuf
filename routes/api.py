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
