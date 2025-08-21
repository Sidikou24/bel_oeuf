from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Product
from app import db
from app.utils.decorators import commercial_required
from datetime import datetime

bp = Blueprint('stock', __name__, url_prefix='/commercial/stock')

@bp.route('/')
@login_required
@commercial_required
def index():
    """Lister tous les produits avec leur stock"""
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    
    # Calcul des statistiques
    stock_ok = Product.query.filter(
        Product.stock_quantity > Product.stock_minimum,
        Product.is_active == True
    ).count()
    
    stock_faible = Product.query.filter(
        Product.stock_quantity <= Product.stock_minimum,
        Product.stock_quantity > 0,
        Product.is_active == True
    ).count()
    
    rupture = Product.query.filter(
        Product.stock_quantity == 0,
        Product.is_active == True
    ).count()
    
    total_quantite = db.session.query(
        db.func.sum(Product.stock_quantity)
    ).filter(Product.is_active == True).scalar() or 0
    
    return render_template(
        'commercial/stock.html',
        products=products,
        stock_ok=stock_ok,
        stock_faible=stock_faible,
        rupture=rupture,
        total_quantite=total_quantite
    )

@bp.route('/new', methods=['GET', 'POST'])
@login_required
@commercial_required
def new_product():
    """Ajouter un nouveau produit"""
    if request.method == 'POST':
        try:
            product = Product(
                name=request.form.get('name'),
                description=request.form.get('description'),
                category=request.form.get('category'),
                subcategory=request.form.get('subcategory'),
                price=float(request.form.get('price')),
                unit=request.form.get('unit'),
                stock_quantity=int(request.form.get('stock_quantity')),
                stock_minimum=int(request.form.get('stock_minimum'))
            )
            
            db.session.add(product)
            db.session.commit()
            
            flash(f'Produit "{product.name}" créé avec succès!', 'success')
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 400
    
    return jsonify({'error': 'Méthode non autorisée'}), 405

@bp.route('/<int:id>')
@login_required
@commercial_required
def get_product(id):
    """Obtenir les détails d'un produit"""
    product = Product.query.get_or_404(id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'category': product.category,
        'subcategory': product.subcategory,
        'price': float(product.price),
        'unit': product.unit,
        'stock_quantity': product.stock_quantity,
        'stock_minimum': product.stock_minimum,
        'created_at': product.created_at.strftime('%d/%m/%Y %H:%M'),
        'updated_at': product.updated_at.strftime('%d/%m/%Y %H:%M')
    })

@bp.route('/<int:id>/edit', methods=['POST'])
@login_required
@commercial_required
def edit_product(id):
    """Modifier un produit"""
    product = Product.query.get_or_404(id)
    
    try:
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.category = request.form.get('category')
        product.subcategory = request.form.get('subcategory')
        product.price = float(request.form.get('price'))
        product.unit = request.form.get('unit')
        product.stock_quantity = int(request.form.get('stock_quantity'))
        product.stock_minimum = int(request.form.get('stock_minimum'))
        product.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Produit "{product.name}" modifié avec succès!', 'success')
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/<int:id>/delete', methods=['DELETE'])
@login_required
@commercial_required
def delete_product(id):
    """Supprimer un produit (soft delete)"""
    product = Product.query.get_or_404(id)
    
    try:
        product.is_active = False
        db.session.commit()
        
        flash(f'Produit "{product.name}" supprimé avec succès!', 'success')
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/categories')
@login_required
@commercial_required
def get_categories():
    """Obtenir les catégories disponibles"""
    return jsonify({'categories': Product.get_categories()})

@bp.route('/subcategories/<category>')
@login_required
@commercial_required
def get_subcategories(category):
    """Obtenir les sous-catégories pour une catégorie"""
    return jsonify({'subcategories': Product.get_subcategories_by_category(category)})
