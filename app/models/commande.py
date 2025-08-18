# app/models/commande.py
from app import db
from datetime import datetime
from sqlalchemy import func
# Remove direct import to avoid circular dependency

class Commande(db.Model):
    __tablename__ = 'commandes'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_commande = db.Column(db.String(20), unique=True, nullable=False)
    
    # Relations
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    commercial_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    responsable_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Dates
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_validation = db.Column(db.DateTime, nullable=True)
    date_livraison_prevue = db.Column(db.DateTime, nullable=True)
    
    # Statuts
    statut = db.Column(db.String(20), nullable=False, default='en_attente')  # en_attente, validee, annulee, livree
    
    # Montants (calculés à partir des détails)
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
        super(Commande, self).__init__(**kwargs)
        if not self.numero_commande:
            self.numero_commande = self.generer_numero_commande()
    
    @staticmethod
    def generer_numero_commande():
        """Génère un numéro de commande unique"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d')
        
        # Compter les commandes du jour
        count = db.session.query(func.count(Commande.id)).filter(
            func.date(Commande.date_creation) == func.date(datetime.utcnow())
        ).scalar() or 0
        
        return f"CMD{timestamp}{count + 1:03d}"
    
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
        return self.montant_restant <= 0.01  # Tolérance pour les erreurs d'arrondi
    
    def calculer_total(self):
        """Recalcule le montant total à partir des détails"""
        total = sum(detail.sous_total for detail in self.details)
        self.montant_total = total
        return total
    
    def ajouter_produit(self, product, quantite, prix_unitaire=None):
        """Ajoute un produit à la commande"""
        if prix_unitaire is None:
            prix_unitaire = product.price
            
        # Vérifier si le produit existe déjà dans la commande
        detail_existant = DetailCommande.query.filter_by(
            commande_id=self.id,
            product_id=product.id
        ).first()
        
        if detail_existant:
            # Mettre à jour la quantité
            detail_existant.quantite += quantite
            detail_existant.calculer_sous_total()
        else:
            # Créer un nouveau détail
            detail = DetailCommande(
                commande=self,
                product=product,
                quantite=quantite,
                prix_unitaire=prix_unitaire
            )
            db.session.add(detail)
        
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
