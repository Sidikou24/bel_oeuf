from app import db
from datetime import datetime

class Approvisionnement(db.Model):
    __tablename__ = 'approvisionnements'

    id = db.Column(db.Integer, primary_key=True)
    date_achat = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseurs.id'), nullable=False)
    matiere_id = db.Column(db.Integer, db.ForeignKey('matieres_premieres.id'), nullable=False)
    quantite = db.Column(db.Numeric(10, 2), nullable=False)
    prix_unitaire = db.Column(db.Numeric(10, 2), nullable=False)
    montant_total = db.Column(db.Numeric(12, 2), nullable=False)
    statut = db.Column(db.String(20), nullable=False, default='En attente')
    date_livraison_prevue = db.Column(db.Date, nullable=True)
    date_livraison_reelle = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    matiere = db.relationship('MatierePremiere', back_populates='approvisionnements')
    fournisseur = db.relationship('Fournisseur', back_populates='approvisionnements')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.quantite is not None and self.prix_unitaire is not None:
            self.montant_total = self.quantite * self.prix_unitaire

    def __repr__(self):
        return f'<Approvisionnement {self.id} - {self.matiere.nom}>'
