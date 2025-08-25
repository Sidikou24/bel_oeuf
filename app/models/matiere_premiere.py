from app import db
from datetime import datetime

class MatierePremiere(db.Model):
    __tablename__ = 'matieres_premieres'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    categorie = db.Column(db.String(50), nullable=False)
    sous_categorie = db.Column(db.String(100), nullable=True)
    unite = db.Column(db.String(20), nullable=False)
    prix_unitaire = db.Column(db.Integer, nullable=False, default=0.0)
    stock_actuel = db.Column(db.Integer, nullable=False, default=0)
    stock_minimum = db.Column(db.Integer, nullable=False, default=5)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    approvisionnements = db.relationship('Approvisionnement', back_populates='matiere', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<MatierePremiere {self.nom}>'
