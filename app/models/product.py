# app/models/product.py
from app import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations produit
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Catégorisation
    category = db.Column(db.String(50), nullable=False)  # 'oeufs', 'poules'
    subcategory = db.Column(db.String(100), nullable=False)  # 'bio', 'fermier', 'pondeuse'
    
    # Prix et unité
    price = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # 'piece', 'douzaine', 'kg'
    
    # Stock
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    stock_minimum = db.Column(db.Integer, nullable=False, default=5)
    
    # Statut
    is_active = db.Column(db.Boolean, default=True)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def stock_faible(self):
        """Vérifie si le stock est faible"""
        return self.stock_quantity <= self.stock_minimum
    
    @property
    def stock_critique(self):
        """Vérifie si le stock est critique (0)"""
        return self.stock_quantity == 0
    
    def peut_vendre(self, quantite):
        """Vérifie si on peut vendre la quantité demandée et retourne un message si non."""
        if not self.is_active:
            return (False, f"Le produit {self.name} n'est pas disponible à la vente.")
        if self.stock_quantity < quantite:
            return (False, f"Stock insuffisant pour {self.name} ({self.category}/{self.subcategory}) - Disponible : {self.stock_quantity} {self.unit}")
        return (True, "")

    
    def diminuer_stock(self, quantite):
        """Diminue le stock après une vente"""
        if not self.peut_vendre(quantite):
            raise ValueError(f"Stock insuffisant pour {self.name}")
        self.stock_quantity -= quantite
    
    def augmenter_stock(self, quantite):
        """Augmente le stock (réapprovisionnement ou annulation)"""
        self.stock_quantity += quantite
    
    @staticmethod
    def get_categories():
        """Retourne les catégories disponibles"""
        return ['oeufs', 'poules']
    
    @staticmethod
    def get_subcategories_by_category(category):
        """Retourne les sous-catégories par catégorie"""
        mapping = {
            'oeufs': ['bio', 'fermier', 'plein_air', 'standard'],
            'poules': ['pondeuse', 'chair', 'ornement']
        }
        return mapping.get(category, [])
    
    def __repr__(self):
        return f'<Product {self.name} - {self.price}€/{self.unit}>'
