# app/models/detail_commande.py - Version corrigée
from app import db
from datetime import datetime
from app.models.product import Product
from sqlalchemy.ext.hybrid import hybrid_property

class DetailCommande(db.Model):
    __tablename__ = 'details_commandes'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relations
    commande_id = db.Column(db.Integer, db.ForeignKey('commandes.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Détails de la ligne
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Integer, nullable=False)
    sous_total = db.Column(db.Integer, nullable=False, default=0)
    
    # Notes spécifiques à cette ligne
    notes = db.Column(db.Text, nullable=True)
    
    # Relations
    product = db.relationship('Product', backref=db.backref('details_commandes', lazy=True))
    
    def __init__(self, **kwargs):
        super(DetailCommande, self).__init__(**kwargs)
        # Calculer le sous-total après l'initialisation si les valeurs sont présentes
        if hasattr(self, 'quantite') and hasattr(self, 'prix_unitaire') and self.quantite and self.prix_unitaire:
            self.calculer_sous_total()
    
    def calculer_sous_total(self):
        """Calcule et met à jour le sous-total"""
        if self.quantite is not None and self.prix_unitaire is not None:
            self.sous_total = float(self.quantite) * float(self.prix_unitaire)
        else:
            self.sous_total = 0
        return self.sous_total
    
    @hybrid_property
    def nom_produit(self):
        """Nom du produit (pour éviter les requêtes supplémentaires)"""
        return self.product.name if self.product else "Produit supprimé"
    
    @hybrid_property
    def unite_produit(self):
        """Unité du produit"""
        return self.product.unit if self.product else "unité"
    
    def peut_etre_modifie(self):
        """Vérifie si cette ligne peut être modifiée"""
        return self.commande.statut == 'en_attente'
    
    def modifier_quantite(self, nouvelle_quantite):
        """Modifie la quantité et recalcule"""
        if not self.peut_etre_modifie():
            raise ValueError("Cette ligne ne peut plus être modifiée")
        
        if nouvelle_quantite <= 0:
            raise ValueError("La quantité doit être positive")
        
        self.quantite = nouvelle_quantite
        self.calculer_sous_total()
        self.commande.calculer_total()
    
    def modifier_prix(self, nouveau_prix):
        """Modifie le prix unitaire et recalcule"""
        if not self.peut_etre_modifie():
            raise ValueError("Cette ligne ne peut plus être modifiée")
        
        if nouveau_prix <= 0:
            raise ValueError("Le prix doit être positif")
        
        self.prix_unitaire = nouveau_prix
        self.calculer_sous_total()
        self.commande.calculer_total()
    
    def __repr__(self):
        return f'<DetailCommande {self.quantite}x {self.nom_produit} = {self.sous_total} FCFA>'