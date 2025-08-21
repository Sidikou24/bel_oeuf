from app import db
from app.models import Commande, DetailCommande, Client, Product, User
from datetime import datetime
from sqlalchemy import func

class CommandeService:
    
    @staticmethod
    def creer_commande_complete(client_id, commercial_id, produits_data, notes=None, date_livraison=None):
        """
        Crée une nouvelle commande complète avec validation
        
        Args:
            client_id: ID du client
            commercial_id: ID du commercial
            produits_data: Liste de dict avec 'product_id', 'quantite', 'prix_unitaire' (optionnel)
            notes: Notes optionnelles
            date_livraison: Date prévue de livraison
            
        Returns:
            dict: {'success': bool, 'commande': Commande, 'message': str}
        """
        try:
            # Validation du client
            client = Client.query.get(client_id)
            if not client or not client.is_active:
                return {'success': False, 'message': 'Client introuvable ou inactif'}
            
            # Validation du commercial
            commercial = User.query.get(commercial_id)
            if not commercial or not commercial.is_active:
                return {'success': False, 'message': 'Commercial introuvable ou inactif'}
            
            # Validation des produits
            if not produits_data or len(produits_data) == 0:
                return {'success': False, 'message': 'Aucun produit sélectionné'}
            
            # Vérification des stocks et validation des produits
            produits_valides = []
            for item in produits_data:
                product = Product.query.get(item['product_id'])
                if not product or not product.is_active:
                    return {'success': False, 'message': f"Produit {item.get('product_id', 'inconnu')} introuvable ou inactif"}
                
                quantite = int(item.get('quantite', 0))
                if quantite <= 0:
                    return {'success': False, 'message': f"Quantité invalide pour {product.name}"}
                
                if product.stock_quantity < quantite:
                    return {'success': False, 'message': f"Stock insuffisant pour {product.name} (disponible: {product.stock_quantity})"}
                
                prix_unitaire = float(item.get('prix_unitaire', product.price))
                if prix_unitaire <= 0:
                    return {'success': False, 'message': f"Prix invalide pour {product.name}"}
                
                produits_valides.append({
                    'product': product,
                    'quantite': quantite,
                    'prix_unitaire': prix_unitaire
                })
            
            # Création de la commande
            commande = Commande(
                client_id=client_id,
                commercial_id=commercial_id,
                notes_commercial=notes,
                date_livraison_prevue=datetime.strptime(date_livraison, '%Y-%m-%d') if date_livraison else None
            )
            
            db.session.add(commande)
            db.session.flush()
            
            # Ajout des détails de commande
            for item in produits_valides:
                detail = DetailCommande(
                    commande_id=commande.id,
                    product_id=item['product'].id,
                    quantite=item['quantite'],
                    prix_unitaire=item['prix_unitaire']
                )
                db.session.add(detail)
            
            # Calcul du total
            commande.calculer_total()
            db.session.commit()
            
            return {
                'success': True, 
                'commande': commande,
                'message': f'Commande {commande.numero_commande} créée avec succès'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Erreur lors de la création: {str(e)}'}
    
    @staticmethod
    def get_commandes_commercial_json(commercial_id, page=1, per_page=10):
        """Récupère les commandes au format JSON pour AJAX"""
        try:
            commandes = Commande.query.filter_by(commercial_id=commercial_id)\
                .order_by(Commande.date_creation.desc())\
                .paginate(page=page, per_page=per_page, error_out=False)
            
            data = []
            for cmd in commandes.items:
                data.append({
                    'id': cmd.id,
                    'numero_commande': cmd.numero_commande,
                    'date_creation': cmd.date_creation.strftime('%d/%m/%Y %H:%M'),
                    'date_livraison_prevue': cmd.date_livraison_prevue.strftime('%d/%m/%Y') if cmd.date_livraison_prevue else None,
                    'client': {
                        'id': cmd.client.id,
                        'nom': cmd.client.nom,
                        'prenom': cmd.client.prenom,
                        'nom_complet': f"{cmd.client.nom} {cmd.client.prenom}"
                    },
                    'total': float(cmd.montant_total),
                    'statut': cmd.statut,
                    'statut_label': {
                        'en_attente': 'En attente',
                        'validee': 'Validée',
                        'annulee': 'Annulée',
                        'livree': 'Livrée'
                    }.get(cmd.statut, cmd.statut),
                    'details_count': len(cmd.details)
                })
            
            return {
                'success': True,
                'data': data,
                'pagination': {
                    'page': commandes.page,
                    'pages': commandes.pages,
                    'total': commandes.total,
                    'has_prev': commandes.has_prev,
                    'has_next': commandes.has_next
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def get_clients_json(commercial_id):
        """Récupère la liste des clients au format JSON"""
        try:
            clients = Client.query.filter_by(is_active=True)\
                .order_by(Client.nom, Client.prenom)\
                .all()
            
            data = [{
                'id': c.id,
                'nom': c.nom,
                'prenom': c.prenom,
                'nom_complet': f"{c.nom} {c.prenom}",
                'telephone': c.telephone,
                'email': c.email
            } for c in clients]
            
            return {'success': True, 'data': data}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def get_produits_json():
        """Récupère la liste des produits au format JSON"""
        try:
            produits = Product.query.filter_by(is_active=True)\
                .order_by(Product.category, Product.name)\
                .all()
            
            data = [{
                'id': p.id,
                'name': p.name,
                'category': p.category,
                'price': float(p.price),
                'stock_quantity': p.stock_quantity,
                'stock_minimum': p.stock_minimum,
                'unit': p.unit
            } for p in produits]
            
            return {'success': True, 'data': data}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
