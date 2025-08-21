from app import db
from datetime import datetime

class Fournisseur(db.Model):
    __tablename__ = 'fournisseurs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom_fournisseur = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(100), nullable=True)
    adresse = db.Column(db.String(255), nullable=True)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    approvisionnements = db.relationship('Approvisionnement', back_populates='fournisseur', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Fournisseur {self.nom_fournisseur}>'
