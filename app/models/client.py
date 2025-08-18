# app/models/client.py
from app import db
from datetime import datetime

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations personnelles
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    
    # Contact
    telephone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    
    # Adresse
    adresse = db.Column(db.Text, nullable=True)
    ville = db.Column(db.String(100), nullable=True)
    code_postal = db.Column(db.String(10), nullable=True)
    
    # Gestion
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Notes
    notes = db.Column(db.Text, nullable=True)
    
    # Relations
    created_by = db.relationship('User', backref=db.backref('clients_crees', lazy=True))
    
    @property
    def nom_complet(self):
        """Retourne le nom complet du client"""
        return f"{self.prenom} {self.nom}"
    
    @property
    def adresse_complete(self):
        """Retourne l'adresse complète"""
        elements = [self.adresse, self.code_postal, self.ville]
        return ", ".join([e for e in elements if e])
    
    def get_total_commandes(self):
        """Retourne le nombre total de commandes"""
        return len(self.commandes)
    
    def get_montant_total_achats(self):
        """Retourne le montant total des achats du client"""
        total = 0
        for commande in self.commandes:
            if commande.statut in ['validee', 'livree']:
                total += float(commande.montant_total)
        return total
    
    def __repr__(self):
        return f'<Client {self.nom_complet}>'

