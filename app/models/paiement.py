# app/models/paiement.py
from app import db
from datetime import datetime

class Paiement(db.Model):
    __tablename__ = 'paiements'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relations
    commande_id = db.Column(db.Integer, db.ForeignKey('commandes.id'), nullable=False)
    
    # Montant et mode
    montant = db.Column(db.Numeric(10, 2), nullable=False)
    mode_paiement = db.Column(db.String(50), nullable=False)  # 'especes', 'cheque', 'virement', 'carte'
    
    # Dates
    date_paiement = db.Column(db.DateTime, default=datetime.utcnow)
    date_encaissement = db.Column(db.DateTime, nullable=True)  # Pour les chèques
    
    # Statut et références
    statut = db.Column(db.String(20), default='en_attente')  # 'en_attente', 'encaisse', 'refuse'
    reference = db.Column(db.String(100), nullable=True)  # Numéro chèque, référence virement
    
    # Gestion
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    validated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Notes
    notes = db.Column(db.Text, nullable=True)
    
    # Relations
    created_by = db.relationship('User', foreign_keys=[created_by_user_id], backref=db.backref('paiements_crees', lazy=True))
    validated_by = db.relationship('User', foreign_keys=[validated_by_user_id], backref=db.backref('paiements_valides', lazy=True))
    
    @staticmethod
    def get_modes_paiement():
        """Retourne les modes de paiement disponibles"""
        return [
            ('especes', 'Espèces'),
            ('cheque', 'Chèque'),
            ('virement', 'Virement'),
            ('carte', 'Carte bancaire')
        ]
    
    @property
    def mode_paiement_display(self):
        """Retourne le libellé du mode de paiement"""
        modes = dict(self.get_modes_paiement())
        return modes.get(self.mode_paiement, self.mode_paiement)
    
    def est_encaisse(self):
        """Vérifie si le paiement est encaissé"""
        return self.statut == 'encaisse'
    
    def peut_etre_valide(self):
        """Vérifie si le paiement peut être validé"""
        return self.statut == 'en_attente'
    
    def valider(self, user, date_encaissement=None):
        """Valide le paiement"""
        if not self.peut_etre_valide():
            raise ValueError("Ce paiement ne peut pas être validé")
        
        self.statut = 'encaisse'
        self.validated_by = user
        self.date_encaissement = date_encaissement or datetime.utcnow()
        
        # Mettre à jour le montant payé de la commande
        self.commande.montant_paye += self.montant
    
    def refuser(self, user, motif=None):
        """Refuse le paiement"""
        if not self.peut_etre_valide():
            raise ValueError("Ce paiement ne peut pas être refusé")
        
        self.statut = 'refuse'
        self.validated_by = user
        if motif:
            self.notes = f"Refusé: {motif}"
    
    def __repr__(self):
        return f'<Paiement {self.montant}€ - {self.mode_paiement} - {self.statut}>'
