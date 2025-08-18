# app/models/detail_commande.py
from app import db
from datetime import datetime
from app.models.product import Product
# Remove direct import to avoid circular dependency
from sqlalchemy.ext.hybrid import hybrid_property

class DetailCommande(db.Model):
    __tablename__ = 'details_commandes'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relations
    commande_id = db.Column(db.Integer, db.ForeignKey('commandes.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Détails de la ligne
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Numeric(10, 2), nullable=False)  # Prix au moment de la commande
    sous_total = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Notes spécifiques à cette ligne
    notes = db.Column(db.Text, nullable=True)
    
    # Relations
    product = db.relationship('Product', backref=db.backref('details_commandes', lazy=True))
    
    def __init__(self, **kwargs):
        super(DetailCommande, self).__init__(**kwargs)
        if self.quantite and self.prix_unitaire:
            self.calculer_sous_total()
    
    def calculer_sous_total(self):
        """Calcule le sous-total de cette ligne"""
        self.sous_total = float(self.quantite) * float(self.prix_unitaire)
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
        return f'<DetailCommande {self.quantite}x {self.nom_produit} = {self.sous_total}€>'


# Exemple d'utilisation dans un service
class CommandeService:
    @staticmethod
    def creer_commande(client, commercial, produits_data):
        """
        Crée une nouvelle commande avec ses détails
        
        Args:
            client: Instance de Client
            commercial: Instance de User (commercial)
            produits_data: Liste de dict {'product_id': int, 'quantite': int, 'prix_unitaire': float (optionnel)}
        
        Returns:
            Commande: La nouvelle commande créée
        """
        commande = Commande(client=client, commercial=commercial)
        db.session.add(commande)
        db.session.flush()  # Pour avoir l'ID de la commande
        
        for data in produits_data:
            product = Product.query.get(data['product_id'])
            if not product:
                raise ValueError(f"Produit {data['product_id']} introuvable")
            
            prix = data.get('prix_unitaire', product.price)
            commande.ajouter_produit(product, data['quantite'], prix)
        
        db.session.commit()
        return commande
    
    @staticmethod
    def get_commandes_en_attente():
        """Récupère toutes les commandes en attente de validation"""
        return Commande.query.filter_by(statut='en_attente').order_by(Commande.date_creation.desc()).all()
    
    @staticmethod
    def get_resume_paiements():
        """Résumé des paiements par commande"""
        return db.session.query(
            Commande.numero_commande,
            Commande.montant_total,
            Commande.montant_paye,
            (Commande.montant_total - Commande.montant_paye).label('montant_restant')
        ).filter(
            Commande.statut == 'validee',
            Commande.montant_total > Commande.montant_paye
        ).all()
