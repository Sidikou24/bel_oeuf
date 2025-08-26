# app/models/commande.py - Version corrigée avec gestion du stock
from app import db
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

class Commande(db.Model):
    __tablename__ = 'commandes'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_commande = db.Column(db.String(20), unique=True, nullable=True)
    
    # Relations
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    commercial_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    responsable_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Dates
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_validation = db.Column(db.DateTime, nullable=True)
    date_annulation = db.Column(db.DateTime, nullable=True)  # Ajouté
    date_livraison_prevue = db.Column(db.DateTime, nullable=True)
    
    # Statuts
    statut = db.Column(db.String(20), nullable=False, default='en_attente')
    
    # Montants
    montant_total = db.Column(db.Integer, nullable=False, default=0)
    montant_paye = db.Column(db.Integer, nullable=False, default=0)
    
    # Commentaires/Notes
    notes_commercial = db.Column(db.Text, nullable=True)
    motif_annulation = db.Column(db.Text, nullable=True)
    commentaires_responsable = db.Column(db.Text, nullable=True)
    commentaires_validation = db.Column(db.Text, nullable=True)
    
    # Relations
    client = db.relationship('Client', backref=db.backref('commandes', lazy=True))
    commercial = db.relationship('User', foreign_keys=[commercial_id], backref=db.backref('commandes_commercial', lazy=True))
    responsable = db.relationship('User', foreign_keys=[responsable_id], backref=db.backref('commandes_responsable', lazy=True))
    details = db.relationship('DetailCommande', backref='commande', lazy=True, cascade='all, delete-orphan')
    paiements = db.relationship('Paiement', backref='commande', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Commande, self).__init__(**kwargs)
    
    @staticmethod
    def generer_numero_commande():
        """Génère un numéro de commande unique"""
        from datetime import datetime
        import random
        
        with db.engine.begin() as connection:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_suffix = random.randint(100, 999)
            
            numero_base = f"CMD{timestamp[-8:]}{random_suffix}"
            
            existing_check = connection.execute(
                db.text("SELECT COUNT(*) FROM commandes WHERE numero_commande = :numero"),
                {"numero": numero_base}
            ).scalar()
            
            if existing_check > 0:
                microsecond = datetime.now().microsecond
                numero_base = f"CMD{timestamp[-8:]}{microsecond:06d}"[:20]
            
            return numero_base
    
    @property
    def montant_restant(self):
        """Calcule le montant restant à payer"""
        return float(self.montant_total) - float(self.montant_paye)
    
    @property
    def pourcentage_paye(self):
        """Calcule le pourcentage payé"""
        if self.montant_total == 0:
            return 0
        return round((float(self.montant_paye) / float(self.montant_total)) * 100, 2)
    
    @property
    def est_payee_entierement(self):
        """Vérifie si la commande est entièrement payée"""
        return self.montant_restant <= 0.01
    
    def calculer_total(self):
        """Recalcule le montant total à partir des détails"""
        if hasattr(self, 'details'):
            total = sum(float(detail.sous_total or 0) for detail in self.details)
            self.montant_total = total
            return total
        return 0
    
    def ajouter_produit(self, product, quantite, prix_unitaire=None):
        """Ajoute un produit à la commande"""
        from app.models.detail_commande import DetailCommande
        
        if prix_unitaire is None:
            prix_unitaire = product.price
        
        detail = DetailCommande(
            commande_id=self.id,
            product_id=product.id,
            quantite=quantite,
            prix_unitaire=prix_unitaire
        )
        detail.calculer_sous_total()
        db.session.add(detail)
        
        db.session.flush()
        self.calculer_total()
    
    def peut_etre_validee(self):
        """Vérifie si la commande peut être validée (avec vérification du stock)"""
        if self.statut != 'en_attente':
            return False, f"Commande déjà {self.statut}"
        
        if not self.details or len(self.details) == 0:
            return False, "Aucun article dans la commande"
        
        if self.montant_total <= 0:
            return False, "Montant total invalide"
        
        # Vérifier la disponibilité du stock pour chaque article
        for detail in self.details:
            product = detail.product
            peut_vendre, message = product.peut_vendre(detail.quantite)
            if not peut_vendre:
                return False, f"Stock insuffisant pour {product.name}: {message}"
        
        return True, "Commande peut être validée"
    
    def valider(self, responsable, commentaires=None):
        """Valide la commande ET diminue le stock"""
        peut_valider, message = self.peut_etre_validee()
        if not peut_valider:
            raise ValueError(message)
        
        # Diminuer le stock de chaque produit
        for detail in self.details:
            product = detail.product
            # Vérifier une dernière fois avant de diminuer
            peut_vendre, stock_message = product.peut_vendre(detail.quantite)
            if not peut_vendre:
                raise ValueError(f"Stock insuffisant pour {product.name}: {stock_message}")
            
            # Diminuer le stock
            product.diminuer_stock(detail.quantite)
            print(f"Stock diminué pour {product.name}: {detail.quantite} {product.unit}")
        
        # Mettre à jour le statut
        self.statut = 'validée'  # Attention: sans accent pour cohérence DB
        self.responsable = responsable
        self.date_validation = datetime.utcnow()
        if commentaires:
            self.commentaires_validation = commentaires
        
        print(f"Commande {self.numero_commande} validée et stock diminué")
    
    def annuler(self, responsable, motif):
        """Annule la commande ET restitue le stock si nécessaire"""
        if self.statut == 'annulee':
            raise ValueError("Cette commande est déjà annulée")
        
        if self.statut == 'livree':
            raise ValueError("Cette commande ne peut plus être annulée car elle est livrée")
        
        # Si la commande était validée, restituer le stock
        if self.statut == 'validée':
            for detail in self.details:
                product = detail.product
                product.augmenter_stock(detail.quantite)
                print(f"Stock restitué pour {product.name}: +{detail.quantite} {product.unit}")
            print(f"Stock restitué pour la commande {self.numero_commande}")
        else:
            print(f"Commande {self.numero_commande} annulée (était en attente, aucun stock à restituer)")
        
        # Mettre à jour le statut
        self.statut = 'annulée'  # Sans accent pour cohérence DB
        self.responsable = responsable
        self.date_annulation = datetime.utcnow()
        self.motif_annulation = motif
    
    def peut_etre_annulee(self):
        """Vérifie si la commande peut être annulée"""
        return self.statut in ['en_attente', 'validée']
    
    def __repr__(self):
        return f'<Commande {self.numero_commande} - {self.client.nom if self.client else "N/A"}>'