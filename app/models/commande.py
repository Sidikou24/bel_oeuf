# app/models/commande.py - Version corrigée pour les warnings de session
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
    date_livraison_prevue = db.Column(db.DateTime, nullable=True)
    
    # Statuts
    statut = db.Column(db.String(20), nullable=False, default='en_attente')
    
    # Montants
    montant_total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    montant_paye = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    
    # Commentaires/Notes
    notes_commercial = db.Column(db.Text, nullable=True)
    motif_annulation = db.Column(db.Text, nullable=True)
    commentaires_responsable = db.Column(db.Text, nullable=True)
    
    # Relations
    client = db.relationship('Client', backref=db.backref('commandes', lazy=True))
    commercial = db.relationship('User', foreign_keys=[commercial_id], backref=db.backref('commandes_commercial', lazy=True))
    responsable = db.relationship('User', foreign_keys=[responsable_id], backref=db.backref('commandes_responsable', lazy=True))
    details = db.relationship('DetailCommande', backref='commande', lazy=True, cascade='all, delete-orphan')
    paiements = db.relationship('Paiement', backref='commande', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        # Ne pas générer le numéro dans le constructeur
        super(Commande, self).__init__(**kwargs)
        # Le numéro sera généré lors de l'ajout à la session
        #self.numero_commande = self.generer_numero_commande()  # Génère le numéro ici
    
    @staticmethod
    def generer_numero_commande():
        """Génère un numéro de commande unique - Version sans conflit de session"""
        from datetime import datetime
        import random
        
        # Utiliser une nouvelle session pour éviter les conflits
        with db.engine.begin() as connection:
            # Méthode simple et efficace : timestamp + random
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_suffix = random.randint(100, 999)
            
            # Vérifier l'unicité
            numero_base = f"CMD{timestamp[-8:]}{random_suffix}"
            
            # Si par hasard il existe déjà, ajouter les microsecondes
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
        
        # Créer le détail de commande
        detail = DetailCommande(
            commande_id=self.id,
            product_id=product.id,
            quantite=quantite,
            prix_unitaire=prix_unitaire
        )
        detail.calculer_sous_total()
        db.session.add(detail)
        
        # Recalculer le total
        db.session.flush()
        self.calculer_total()
    
    def peut_etre_validee(self):
        """Vérifie si la commande peut être validée"""
        return (
            self.statut == 'en_attente' and 
            len(self.details) > 0 and 
            self.montant_total > 0
        )
    
    def valider(self, responsable, commentaires=None):
        """Valide la commande"""
        if not self.peut_etre_validee():
            raise ValueError("Cette commande ne peut pas être validée")
        
        self.statut = 'validee'
        self.responsable = responsable
        self.date_validation = datetime.utcnow()
        if commentaires:
            self.commentaires_responsable = commentaires
    
    def annuler(self, responsable, motif):
        """Annule la commande"""
        if self.statut in ['livree']:
            raise ValueError("Cette commande ne peut plus être annulée")
        
        self.statut = 'annulee'
        self.responsable = responsable
        self.date_validation = datetime.utcnow()
        self.motif_annulation = motif
    
    def __repr__(self):
        return f'<Commande {self.numero_commande} - {self.client.nom if self.client else "N/A"}>'