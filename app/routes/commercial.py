#routes/commercial.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import User, Commande, Client, Product, DetailCommande
from app import db
from app.services.commercial_service import CommercialService
from services.commercials_service import get_fournisseurs, ajouter_fournisseur_service, modifier_fournisseur_service, get_achats, ajouter_achat_service, supprimer_achat_service
from app.utils.decorators import commercial_required
from datetime import datetime
import json

bp = Blueprint('commercial', __name__, url_prefix='/commercial')

@bp.route('/dashboard')
@login_required
@commercial_required
def dashboard():
    return render_template('commercial/dashboard.html')

# Liste des ventes
@bp.route('/sales')
@login_required
@commercial_required
def sales():
    commandes = Commande.query.order_by(Commande.date_creation.desc()).all()
    clients = Client.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    
    # Convert products to serializable format for JSON
    products_json = [
        {
            'id': p.id,
            'name': p.name,
            'price': float(p.price),
            'stock': p.stock_quantity,
            'description': p.description,
            'category': p.category
        }
        for p in products
    ]
    
    # Calcul du nombre total de commandes
    total_ventes = len(commandes)

    # Calcul du chiffre d'affaires (somme des commandes validées ou livrées)
    chiffre_affaires = sum(
        float(c.montant_total)
        for c in commandes
        if c.statut in ['validée', 'livrée']
    )
    
    return render_template(
        'commercial/sales.html',
        commandes=commandes,
        clients=clients,
        products=products,
        products_json=products_json,
        total_ventes=total_ventes,
        chiffre_affaires=chiffre_affaires
    )

# Création d'une nouvelle vente
# routes/commercial.py - Version corrigée pour les warnings de session
@bp.route('/sales/new', methods=['POST'])
@login_required
@commercial_required
def new_sale():
    try:
        # 1. Validation des données d'entrée
        client_id = request.form.get('client_id')
        date_livraison = request.form.get('date_livraison')
        items_json = request.form.get('items')
        montant_paye = request.form.get('montant_paye', '0')

        # Validations de base
        if not client_id:
            flash("Veuillez sélectionner un client", "danger")
            return redirect(url_for('commercial.sales'))

        if not items_json:
            flash("Aucun article sélectionné", "danger")
            return redirect(url_for('commercial.sales'))

        # 2. Vérifier que le client existe
        client = Client.query.get(client_id)
        if not client:
            flash("Client introuvable", "danger")
            return redirect(url_for('commercial.sales'))

        # 3. Parser et valider les items
        try:
            items = json.loads(items_json)
            if not items or len(items) == 0:
                flash("Aucun article valide dans la commande", "danger")
                return redirect(url_for('commercial.sales'))
        except json.JSONDecodeError:
            flash("Format des articles invalide", "danger")
            return redirect(url_for('commercial.sales'))

        # 4. Valider le montant payé
        try:
            montant_paye_float = float(montant_paye) if montant_paye else 0.0
            if montant_paye_float < 0:
                flash("Le montant payé ne peut pas être négatif", "danger")
                return redirect(url_for('commercial.sales'))
        except (ValueError, TypeError):
            montant_paye_float = 0.0

        # 5. Créer la commande AVEC un numéro généré immédiatement
        commande = Commande(
            client=client,
            commercial=current_user,
            statut="en_attente",
            montant_paye=montant_paye_float,
            numero_commande=Commande.generer_numero_commande()  # Générer le numéro ici
        )

        # Parser la date de livraison si fournie
        if date_livraison:
            try:
                commande.date_livraison_prevue = datetime.strptime(date_livraison, "%Y-%m-%d")
            except ValueError:
                flash("Format de date invalide", "warning")

        # 6. Ajouter à la session
        db.session.add(commande)
        db.session.flush()  # Obtenir l'ID

        # 7. Traiter chaque article
        total_calcule = 0
        articles_ajoutes = 0

        for item in items:
            try:
                product_id = item.get('product_id')
                quantite = item.get('quantite')
                prix_unitaire = item.get('prix_unitaire')

                # Validation des données de l'article
                if not product_id or not quantite or not prix_unitaire:
                    continue

                # Conversion en types appropriés
                product_id = int(product_id)
                quantite = int(quantite)
                prix_unitaire = float(prix_unitaire)

                if quantite <= 0 or prix_unitaire <= 0:
                    continue

                # Vérifier que le produit existe
                product = Product.query.get(product_id)
                if not product:
                    flash(f"Produit avec ID {product_id} introuvable", "warning")
                    continue

                # Vérifier le stock
                peut_vendre, message = product.peut_vendre(quantite)
                if not peut_vendre:
                    flash(message, "warning")  # Affiche le message personnalisé
                    continue

                # Créer le détail de commande
                detail = DetailCommande(
                    commande_id=commande.id,
                    product_id=product_id,
                    quantite=quantite,
                    prix_unitaire=prix_unitaire
                )

                # Calculer le sous-total
                detail.calculer_sous_total()
                db.session.add(detail)

                # Mettre à jour le stock
                if hasattr(product, 'diminuer_stock'):
                    product.diminuer_stock(quantite)

                total_calcule += float(detail.sous_total)
                articles_ajoutes += 1

            except (ValueError, TypeError, KeyError) as e:
                print(f"Erreur lors du traitement de l'article: {e}")
                continue

        # 8. Vérifier qu'au moins un article a été ajouté
        if articles_ajoutes == 0:
            db.session.rollback()
            flash("Aucun article valide n'a pu être ajouté à la commande", "danger")
            return redirect(url_for('commercial.sales'))

        # 9. Mettre à jour le montant total de la commande
        commande.montant_total = total_calcule

        # 10. Commit final
        db.session.commit()

        #flash(f"Commande {commande.numero_commande} créée avec succès ✅ ({articles_ajoutes} articles)", "success")
        print(f"Commande créée: {commande.numero_commande}, Total: {commande.montant_total} FCFA")

    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la création de la commande: {str(e)}")
        flash(f"Erreur lors de la création de la commande: {str(e)}", "danger")

    return redirect(url_for('commercial.sales'))

# Détails d'une vente - VERSION AMÉLIORÉE
@bp.route('/sale/<int:commande_id>/details')
@login_required
@commercial_required
def sale_details(commande_id):
    """Retourne les détails complets d'une vente spécifique avec gestion d'erreurs améliorée"""
    try:
        commande = Commande.query.get_or_404(commande_id)
        
        # Vérifier que l'utilisateur a accès à cette commande
        if commande.commercial_id != current_user.id and not current_user.is_admin:
            return jsonify({'error': 'Accès non autorisé'}), 403
        
        # Préparer les données du client avec gestion des valeurs nulles
        client_data = {
            'id': commande.client.id,
            'nom_complet': commande.client.nom_complet or 'Non spécifié',
            'telephone': commande.client.telephone or '',
            'email': commande.client.email or '',
            'adresse': commande.client.adresse or 'Non spécifiée'
        }
        
        # Calculer les montants avec protection contre les erreurs
        montant_total = float(commande.montant_total or 0)
        montant_paye = float(commande.montant_paye or 0)
        montant_restant = max(0, montant_total - montant_paye)
        pourcentage_paye = round((montant_paye / montant_total * 100) if montant_total > 0 else 0, 1)
        
        # Préparer les données de la commande
        commande_data = {
            'id': commande.id,
            'numero_commande': commande.numero_commande or f'CMD-{commande.id}',
            'date_creation': commande.date_creation.strftime('%d/%m/%Y à %H:%M'),
            'client': client_data,
            'montant_total': montant_total,
            'montant_paye': montant_paye,
            'montant_restant': montant_restant,
            'pourcentage_paye': pourcentage_paye,
            'statut': commande.statut or 'en_attente',
            'date_livraison_prevue': commande.date_livraison_prevue.strftime('%d/%m/%Y') if commande.date_livraison_prevue else None,
            'notes_commercial': commande.notes_commercial or '',
            'articles': []
        }
        
        # Ajouter les articles de la commande avec gestion des produits supprimés
        for detail in commande.details:
            try:
                # Gérer le cas où le produit pourrait être supprimé
                if detail.product:
                    nom_produit = detail.product.name
                    description = detail.product.description or ''
                    unite = getattr(detail.product, 'unit', 'unité')
                else:
                    nom_produit = 'Produit supprimé'
                    description = 'Ce produit n\'est plus disponible'
                    unite = 'unité'
                
                article = {
                    'id': detail.id,
                    'product_id': detail.product_id,
                    'nom_produit': nom_produit,
                    'description': description,
                    'quantite': int(detail.quantite or 0),
                    'prix_unitaire': float(detail.prix_unitaire or 0),
                    'sous_total': float(detail.sous_total or 0),
                    'unite': unite
                }
                commande_data['articles'].append(article)
                
            except Exception as detail_error:
                print(f"Erreur lors du traitement du détail {detail.id}: {detail_error}")
                # Ajouter un article d'erreur plutôt que de faire échouer toute la requête
                article_erreur = {
                    'id': detail.id,
                    'product_id': detail.product_id,
                    'nom_produit': 'Erreur de chargement',
                    'description': 'Impossible de charger cet article',
                    'quantite': int(detail.quantite or 0),
                    'prix_unitaire': float(detail.prix_unitaire or 0),
                    'sous_total': float(detail.sous_total or 0),
                    'unite': 'unité'
                }
                commande_data['articles'].append(article_erreur)
        
        return jsonify(commande_data)
        
    except Exception as e:
        print(f"Erreur lors du chargement des détails de la commande {commande_id}: {str(e)}")
        return jsonify({
            'error': 'Erreur lors du chargement des détails',
            'message': 'Une erreur technique est survenue. Veuillez réessayer.'
        }), 500


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
        #flash('Client créé avec succès', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception:
        db.session.rollback()
        #flash("Une erreur est survenue lors de la création du client", 'danger')
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
        #flash('Client modifié avec succès', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception:
        db.session.rollback()
        #flash("Une erreur est survenue lors de la modification du client", 'danger')
    return redirect(url_for('commercial.clients'))

#Début gestion Stock
@bp.route('/stock')
@login_required
@commercial_required
def stock():
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


@bp.route('/stock/new', methods=['GET', 'POST'])
@login_required
@commercial_required
def new_product():
    """Ajouter un nouveau produit"""
    if request.method == 'POST':
        try:
            # Vérification des données requises
            required_fields = ['name', 'category', 'subcategory', 'price', 'unit', 'stock_quantity', 'stock_minimum']
            for field in required_fields:
                if not request.form.get(field):
                    return jsonify({'success': False, 'error': f'Le champ {field} est requis'}), 400
            
            product = Product(
                name=request.form.get('name'),
                description=request.form.get('description', ''),
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
            
        except ValueError as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': 'Valeurs numériques invalides'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 400
    
    return jsonify({'error': 'Méthode non autorisée'}), 405


@bp.route('/stock/<int:id>')
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

@bp.route('/stock/<int:id>/edit', methods=['POST'])
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


@bp.route('/stock/categories')
@login_required
@commercial_required
def get_categories():
    """Obtenir les catégories disponibles"""
    return jsonify({'categories': Product.get_categories()})

@bp.route('/stock/subcategories/<category>')
@login_required
@commercial_required
def get_subcategories(category):
    """Obtenir les sous-catégories pour une catégorie"""
    return jsonify({'subcategories': Product.get_subcategories_by_category(category)})

@bp.route('/stock/<int:id>/delete', methods=['DELETE'])
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
    
#Fin gestion Stock


@bp.route('/purchases')
def purchases():
    fournisseurs = get_fournisseurs()
    from services.commercials_service import get_matieres, get_stats_achats
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
## ------------------------- ROUTES FOURNISSEURS -----------------------------

@bp.route('/suppliers')
def suppliers():
    from services.commercials_service import get_stats_fournisseurs
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
    from services.commercials_service import supprimer_fournisseur_service
    supprimer_fournisseur_service(fournisseur_id)
    return redirect(url_for('commercial.suppliers'))

@bp.route('/purchases/modifier', methods=['POST'])
def modifier_achat():
    from services.commercials_service import modifier_achat_service
    modifier_achat_service(request.form)
    return redirect(url_for('commercial.purchases'))


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

