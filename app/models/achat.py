from app import db
from datetime import datetime

class Achat(db.Model):
    __tablename__ = 'achats'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_achat = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseurs.id'), nullable=False)
    matiere_id = db.Column(db.Integer, db.ForeignKey('matieres_premieres.id'), nullable=False)
    matiere = db.relationship('MatierePremiere')
    quantite = db.Column(db.Float, nullable=False)
    prix_unitaire = db.Column(db.Integer, nullable=False)
    montant_total = db.Column(db.Integer, nullable=False)
    statut = db.Column(db.String(20), default='En attente')
    date_livraison_prevue = db.Column(db.Date, nullable=True)
    date_livraison_reelle = db.Column(db.Date, nullable=True)

    fournisseur = db.relationship('Fournisseur', backref='achats')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Calcul automatique du montant total si non fourni
        if 'montant_total' not in kwargs:
            self.montant_total = self.quantite * self.prix_unitaire

    def __repr__(self):
        return f'<Achat {self.id} - {self.matiere}>'
