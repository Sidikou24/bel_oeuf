
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
    def get_clients_paginated(page=1, per_page=20, search=''):
        """Clients avec pagination et recherche"""
        query = Client.query.filter_by(is_active=True)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Client.nom.ilike(search_pattern),
                    Client.prenom.ilike(search_pattern),
                    Client.email.ilike(search_pattern),
                    Client.telephone.ilike(search_pattern)
                )
            )
        
        return query.order_by(Client.nom).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
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
    def get_commandes_commercial(commercial_id, page=1, per_page=15, 
                               statut_filter='tous', date_debut=None, date_fin=None):
        """Commandes du commercial avec filtres"""
        query = Commande.query.filter_by(commercial_id=commercial_id)
        
        # Filtre par statut
        if statut_filter != 'tous':
            query = query.filter_by(statut=statut_filter)
        
        # Filtre par date
        if date_debut:
            try:
                debut = datetime.strptime(date_debut, '%Y-%m-%d')
                query = query.filter(Commande.date_creation >= debut)
            except ValueError:
                pass
        
        if date_fin:
            try:
                fin = datetime.strptime(date_fin, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(Commande.date_creation < fin)
            except ValueError:
                pass
        
        return query.order_by(Commande.date_creation.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
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
    def creer_commande(client_id, commercial_id, produits_data, notes=None):
        """Créer une nouvelle commande avec vérification des stocks"""
        
        # Vérifications de base
        client = Client.query.get(client_id)
        if not client:
            raise ValueError("Client introuvable")
        
        if not client.is_active:
            raise ValueError("Ce client n'est plus actif")
        
        if not produits_data:
            raise ValueError("Aucun produit sélectionné")
        
        # Vérifier les stocks AVANT de créer la commande
        for data in produits_data:
            product = Product.query.get(data['product_id'])
            if not product:
                raise ValueError(f"Produit {data['product_id']} introuvable")
            
            if not product.is_active:
                raise ValueError(f"Le produit {product.name} n'est plus disponible")
            
            if not product.peut_vendre(data['quantite']):
                raise ValueError(
                    f"Stock insuffisant pour {product.name}. "
                    f"Demandé: {data['quantite']}, Disponible: {product.stock_quantity}"
                )
        
        # Créer la commande
        commande = Commande(
            client_id=client_id,
            commercial_id=commercial_id,
            notes_commercial=notes
        )
        db.session.add(commande)
        db.session.flush()  # Pour avoir l'ID
        
        # Ajouter les produits
        for data in produits_data:
            product = Product.query.get(data['product_id'])
            detail = DetailCommande(
                commande_id=commande.id,
                product_id=product.id,
                quantite=data['quantite'],
                prix_unitaire=product.price
            )
            db.session.add(detail)
        
        # Calculer le total
        commande.calculer_total()
        
        db.session.commit()
        return commande
    
    @staticmethod
    def get_products_stock(category_filter='tous', stock_filter='tous'):
        """Produits avec filtres de stock"""
        query = Product.query.filter_by(is_active=True)
        
        # Filtre par catégorie
        if category_filter != 'tous':
            query = query.filter_by(category=category_filter)
        
        # Filtre par niveau de stock
        if stock_filter == 'faible':
            query = query.filter(Product.stock_quantity <= Product.stock_minimum)
        elif stock_filter == 'critique':
            query = query.filter(Product.stock_quantity == 0)
        
        return query.order_by(Product.category, Product.name).all()
    
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
