
# app/services/commercial_service.py
from app import db
from app.models import Client, Product, Commande, DetailCommande, User
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_

class CommercialService:
    
    @staticmethod
    def get_dashboard_stats(commercial_id):
        """Statistiques pour le dashboard"""
        # Commandes du mois
        debut_mois = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        stats = {
            'total_clients': Client.query.filter_by(created_by_user_id=commercial_id, is_active=True).count(),
            'commandes_mois': Commande.query.filter(
                Commande.commercial_id == commercial_id,
                Commande.date_creation >= debut_mois
            ).count(),
            'commandes_en_attente': Commande.query.filter_by(
                commercial_id=commercial_id, 
                statut='en_attente'
            ).count(),
            'produits_stock_faible': Product.query.filter(
                Product.stock_quantity <= Product.stock_minimum,
                Product.is_active == True
            ).count()
        }
        
        return stats
    
    @staticmethod
    def get_commandes_recentes(commercial_id, limit=5):
        """Commandes récentes du commercial"""
        return Commande.query.filter_by(
            commercial_id=commercial_id
        ).order_by(
            Commande.date_creation.desc()
        ).limit(limit).all()
    
    
    @staticmethod
    def get_clients_json(commercial_id=None):
        """
        Récupère la liste des clients au format JSON
        """
        try:
            from app.models.client import Client
            
            query = Client.query.filter_by(is_active=True)
            
            # Si c'est un commercial, on peut filtrer par ses clients assignés
            # (selon votre logique métier)
            if commercial_id:
                # query = query.filter_by(commercial_id=commercial_id)  # si vous avez cette relation
                pass
            
            clients = query.order_by(Client.nom, Client.prenom).all()
            
            clients_data = []
            for client in clients:
                clients_data.append({
                    'id': client.id,
                    'nom': client.nom,
                    'prenom': client.prenom,
                    'nom_complet': client.nom_complet,  # Utilise la propriété du modèle
                    'email': client.email or '',
                    'telephone': client.telephone or '',
                    'ville': client.ville or '',
                    'total_commandes': client.get_total_commandes(),
                    'montant_total_achats': client.get_montant_total_achats()
                })
            
            return {
                'success': True,
                'data': clients_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur lors de la récupération des clients: {str(e)}',
                'data': []
            }

    
    @staticmethod
    def creer_client(nom, prenom, telephone=None, email=None, 
                    adresse=None, ville=None, code_postal=None, 
                    notes=None, created_by_user_id=None):
        """Créer un nouveau client"""
        
        # Vérifications de base
        if not nom or not prenom:
            raise ValueError("Le nom et le prénom sont obligatoires")
        
        # Vérifier l'unicité de l'email si fourni
        if email and Client.query.filter_by(email=email, is_active=True).first():
            raise ValueError("Un client avec cette adresse email existe déjà")
        
        client = Client(
            nom=nom.strip().title(),
            prenom=prenom.strip().title(),
            telephone=telephone.strip() if telephone else None,
            email=email.strip().lower() if email else None,
            adresse=adresse.strip() if adresse else None,
            ville=ville.strip().title() if ville else None,
            code_postal=code_postal.strip() if code_postal else None,
            notes=notes.strip() if notes else None,
            created_by_user_id=created_by_user_id
        )
        
        db.session.add(client)
        db.session.commit()
        
        return client
    
    @staticmethod
    def modifier_client(client_id, **kwargs):
        """Modifier un client existant"""
        client = Client.query.get_or_404(client_id)
        
        # Vérifier l'email s'il est modifié
        if 'email' in kwargs and kwargs['email']:
            existing = Client.query.filter(
                Client.email == kwargs['email'].strip().lower(),
                Client.id != client_id,
                Client.is_active == True
            ).first()
            if existing:
                raise ValueError("Un client avec cette adresse email existe déjà")
        
        # Mettre à jour les champs
        for key, value in kwargs.items():
            if hasattr(client, key):
                if key in ['nom', 'prenom', 'ville']:
                    setattr(client, key, value.strip().title() if value else None)
                elif key == 'email':
                    setattr(client, key, value.strip().lower() if value else None)
                else:
                    setattr(client, key, value.strip() if value and isinstance(value, str) else value)
        
        db.session.commit()
        return client
    

    @staticmethod
    def get_commandes_commercial_json(commercial_id, page=1, per_page=10):
        """
        Récupère les commandes du commercial au format JSON pour l'API
        
        Returns:
            dict: Données formatées pour l'API
        """
        try:
            from app.models.commande import Commande
            
            # Récupérer les commandes paginées
            commandes_paginated = Commande.query.filter_by(
                commercial_id=commercial_id
            ).order_by(
                Commande.date_creation.desc()
            ).paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            # Formater les données
            commandes_data = []
            for commande in commandes_paginated.items:
                # Mapping des statuts pour l'affichage
                statut_labels = {
                    'en_attente': 'En attente',
                    'validée': 'Validée',
                    'livrée': 'Livrée',
                    'annulée': 'Annulée'
                }
                
                commandes_data.append({
                    'id': commande.id,
                    'numero_commande': commande.numero_commande,
                    'date_creation': commande.date_creation.strftime('%d/%m/%Y'),
                    'date_livraison_prevue': commande.date_livraison_prevue.strftime('%d/%m/%Y') if commande.date_livraison_prevue else None,
                    'client': {
                        'id': commande.client.id,
                        'nom_complet': f"{commande.client.nom} {commande.client.prenom}"
                    },
                    'total': float(commande.montant_total),
                    'statut': commande.statut,
                    'statut_label': statut_labels.get(commande.statut, commande.statut),
                    'details_count': len(commande.details),
                    'notes': commande.notes_commercial
                })
            
            return {
                'success': True,
                'data': commandes_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': commandes_paginated.total,
                    'pages': commandes_paginated.pages,
                    'has_prev': commandes_paginated.has_prev,
                    'has_next': commandes_paginated.has_next
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur lors de la récupération des commandes: {str(e)}',
                'data': []
            }

    
    @staticmethod
    def get_stats_commandes_par_statut(commercial_id):
        """Statistiques des commandes par statut"""
        stats = db.session.query(
            Commande.statut,
            func.count(Commande.id).label('count')
        ).filter_by(
            commercial_id=commercial_id
        ).group_by(Commande.statut).all()
        
        return {statut: count for statut, count in stats}
    
    @staticmethod
    def creer_commande_complete(client_id, commercial_id, produits_data, notes=None, date_livraison=None):
        """
        Crée une nouvelle commande complète avec validation et gestion d'erreurs
        
        Args:
            client_id (int): ID du client
            commercial_id (int): ID du commercial
            produits_data (list): Liste de dict {'product_id': int, 'quantite': int}
            notes (str, optional): Notes du commercial
            date_livraison (str, optional): Date de livraison au format 'YYYY-MM-DD'
        
        Returns:
            dict: {'success': bool, 'message': str, 'commande_id': int (si succès)}
        """
        try:
            # 1. Vérifications de base
            from app.models.client import Client
            from app.models.user import User
            from app.models.product import Product
            from app.models.commande import Commande
            from app.models.detail_commande import DetailCommande
            from datetime import datetime
            
            # Vérifier le client
            client = Client.query.get(client_id)
            if not client:
                return {'success': False, 'message': 'Client introuvable'}
            
            if not client.is_active:
                return {'success': False, 'message': 'Ce client n\'est plus actif'}
            
            # Vérifier le commercial
            commercial = User.query.get(commercial_id)
            if not commercial or commercial.role != 'commercial':
                return {'success': False, 'message': 'Commercial introuvable'}
            
            # Vérifier qu'il y a des produits
            if not produits_data or len(produits_data) == 0:
                return {'success': False, 'message': 'Aucun produit sélectionné'}
            
            # 2. Vérifier les stocks et données produits AVANT création
            produits_valides = []
            for data in produits_data:
                if 'product_id' not in data or 'quantite' not in data:
                    return {'success': False, 'message': 'Données produit incomplètes'}
                
                try:
                    product_id = int(data['product_id'])
                    quantite = int(data['quantite'])
                except (ValueError, TypeError):
                    return {'success': False, 'message': 'Données produit invalides'}
                
                if quantite <= 0:
                    return {'success': False, 'message': 'La quantité doit être positive'}
                
                product = Product.query.get(product_id)
                if not product:
                    return {'success': False, 'message': f'Produit {product_id} introuvable'}
                
                if not product.is_active:
                    return {'success': False, 'message': f'Le produit {product.name} n\'est plus disponible'}
                
                # Vérifier le stock (si votre modèle Product a cette méthode)
                if hasattr(product, 'peut_vendre') and not product.peut_vendre(quantite):
                    return {
                        'success': False, 
                        'message': f'Stock insuffisant pour {product.name}. Demandé: {quantite}, Disponible: {product.stock_quantity}'
                    }
                
                # Ajouter à la liste des produits valides
                produits_valides.append({
                    'product': product,
                    'quantite': quantite,
                    'prix_unitaire': float(product.price)  # Prix actuel du produit
                })
            
            # 3. Traiter la date de livraison
            date_livraison_obj = None
            if date_livraison:
                try:
                    date_livraison_obj = datetime.strptime(date_livraison, '%Y-%m-%d')
                except ValueError:
                    return {'success': False, 'message': 'Format de date de livraison invalide'}
            
            # 4. Créer la commande
            commande = Commande(
                client_id=client_id,
                commercial_id=commercial_id,
                date_livraison_prevue=date_livraison_obj,
                notes_commercial=notes
            )
            
            db.session.add(commande)
            db.session.flush()  # Pour avoir l'ID de la commande
            
            # 5. Ajouter les détails de la commande
            for produit_data in produits_valides:
                detail = DetailCommande(
                    commande_id=commande.id,
                    product_id=produit_data['product'].id,
                    quantite=produit_data['quantite'],
                    prix_unitaire=produit_data['prix_unitaire']
                )
                # Le sous_total sera calculé automatiquement dans __init__
                db.session.add(detail)
            
            # 6. Calculer le total de la commande
            commande.calculer_total()
            
            # 7. Optionnel: Diminuer les stocks si vous voulez le faire à la création
            # (ou vous pouvez le faire à la validation de la commande)
            # for produit_data in produits_valides:
            #     produit_data['product'].diminuer_stock(produit_data['quantite'])
            
            # 8. Sauvegarder tout
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Commande {commande.numero_commande} créée avec succès',
                'commande_id': commande.id,
                'numero_commande': commande.numero_commande,
                'montant_total': float(commande.montant_total)
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Erreur lors de la création de la commande: {str(e)}'
            }

    
    @staticmethod
    def get_produits_json():
        """
        Récupère la liste des produits disponibles au format JSON
        """
        try:
            from app.models.product import Product
            
            produits = Product.query.filter_by(is_active=True).order_by(
                Product.category, Product.name
            ).all()
            
            produits_data = []
            for produit in produits:
                produits_data.append({
                    'id': produit.id,
                    'name': produit.name,
                    'category': produit.category,
                    'subcategory': produit.subcategory,
                    'price': float(produit.price),
                    'unit': produit.unit,
                    'stock_quantity': produit.stock_quantity,
                    'stock_minimum': produit.stock_minimum,
                    'stock_faible': produit.stock_faible,
                    'stock_critique': produit.stock_critique,
                    'description': produit.description or ''
                })
            
            return {
                'success': True,
                'data': produits_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur lors de la récupération des produits: {str(e)}',
                'data': []
            }    
            
            
    @staticmethod
    def get_clients_paginated(page=1, per_page=20, search=''):
        """
        Récupère les clients paginés avec recherche optionnelle
        
        Args:
            page (int): Numéro de page
            per_page (int): Nombre d'éléments par page
            search (str): Terme de recherche (nom, prénom, téléphone, email)
        
        Returns:
            Pagination: Objet pagination SQLAlchemy
        """
        query = Client.query.filter_by(is_active=True)
        
        # Appliquer la recherche si fournie
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Client.nom.ilike(search_term),
                    Client.prenom.ilike(search_term),
                    Client.telephone.ilike(search_term),
                    Client.email.ilike(search_term)
                )
            )
        
        # Trier par nom et prénom
        query = query.order_by(Client.nom.asc(), Client.prenom.asc())
        
        return query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

    @staticmethod
    def get_stats_stock():
        """Statistiques générales du stock"""
        total_produits = Product.query.filter_by(is_active=True).count()
        stock_faible = Product.query.filter(
            Product.stock_quantity <= Product.stock_minimum,
            Product.is_active == True
        ).count()
        stock_critique = Product.query.filter_by(stock_quantity=0, is_active=True).count()
        
        return {
            'total_produits': total_produits,
            'stock_faible': stock_faible,
            'stock_critique': stock_critique,
            'stock_ok': total_produits - stock_faible
        }
