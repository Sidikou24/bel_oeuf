from app import db
from app.models import Fournisseur, MatierePremiere, Approvisionnement

# --- LOGIQUE MATIERE PREMIERE ---
def get_matieres():
	"""
	Retourne la liste des matières premières actives.
	"""
	return MatierePremiere.query.filter_by(is_active=True).all()
# --- LOGIQUE APPROVISIONNEMENT ---
def get_achats():
	"""
	Retourne la liste des achats (approvisionnements).
	"""
	return Approvisionnement.query.all()



def ajouter_achat_service(form_data):
	"""
	Ajoute un achat (approvisionnement) à la base de données à partir des données du formulaire.
	"""
	from datetime import datetime, date
	def parse_date(val):
		if val:
			return datetime.strptime(val, "%Y-%m-%d").date()
		return None
	date_achat = parse_date(form_data.get('date_achat')) or date.today()
	fournisseur_id = form_data.get('fournisseur_id')
	matiere_id = form_data.get('matiere_id')
	quantite = float(form_data.get('quantite', 0))
	statut = form_data.get('statut', 'En attente')
	date_livraison_prevue = parse_date(form_data.get('date_livraison_prevue'))
	date_livraison_reelle = parse_date(form_data.get('date_livraison_reelle'))
	matiere = MatierePremiere.query.get(matiere_id)
	prix_unitaire = matiere.prix_unitaire if matiere else 0.0
	montant_total = quantite * prix_unitaire
	nouvel_achat = Approvisionnement(
		date_achat=date_achat,
		fournisseur_id=fournisseur_id,
		matiere_id=matiere_id,
		quantite=quantite,
		prix_unitaire=prix_unitaire,
		montant_total=montant_total,
		statut=statut,
		date_livraison_prevue=date_livraison_prevue,
		date_livraison_reelle=date_livraison_reelle
	)
	db.session.add(nouvel_achat)
	db.session.commit()
	return nouvel_achat

def supprimer_achat_service(achat_id):
	"""
	Supprime un achat (approvisionnement) de la base de données par son id.
	"""
	achat = Approvisionnement.query.get(achat_id)
	if achat:
		db.session.delete(achat)
		db.session.commit()
		return True
	return False

def modifier_achat_service(form_data):
	"""
	Modifie un achat (approvisionnement) existant à partir des données du formulaire.
	"""
	from datetime import datetime
	def parse_date(val):
		if val:
			return datetime.strptime(val, "%Y-%m-%d").date()
		return None
	achat_id = form_data.get('id')
	achat = Approvisionnement.query.get(achat_id)
	if not achat:
		return None
	achat.date_achat = parse_date(form_data.get('date_achat')) or achat.date_achat
	achat.fournisseur_id = form_data.get('fournisseur_id', achat.fournisseur_id)
	achat.matiere_id = form_data.get('matiere_id', achat.matiere_id)
	achat.quantite = float(form_data.get('quantite', achat.quantite))
	matiere = MatierePremiere.query.get(achat.matiere_id)
	achat.prix_unitaire = matiere.prix_unitaire if matiere else achat.prix_unitaire
	achat.statut = form_data.get('statut', achat.statut)
	date_livraison_prevue = form_data.get('date_livraison_prevue')
	achat.date_livraison_prevue = parse_date(date_livraison_prevue) if date_livraison_prevue else achat.date_livraison_prevue
	date_livraison_reelle = form_data.get('date_livraison_reelle')
	achat.date_livraison_reelle = parse_date(date_livraison_reelle) if date_livraison_reelle else achat.date_livraison_reelle
	achat.montant_total = achat.quantite * achat.prix_unitaire
	db.session.commit()
	return achat
from app import db
from app.models import Fournisseur, MatierePremiere, Approvisionnement

# --- LOGIQUE FOURNISSEUR ---
def get_stats_fournisseurs():
	"""
	Retourne les stats par fournisseur : nombre d'achats, montant total, etc.
	"""
	stats = {}
	fournisseurs = Fournisseur.query.all()
	for f in fournisseurs:
		achats = Approvisionnement.query.filter_by(fournisseur_id=f.id).all()
		total_achats = len(achats)
		montant_total = sum(a.montant_total for a in achats)
		stats[f.id] = {
			'total_achats': total_achats,
			'montant_total': round(montant_total, 2)
		}
	return stats
# Toutes les fonctions métier liées à la gestion des fournisseurs sont regroupées ici.


def get_fournisseurs():
	"""
	Retourne la liste des fournisseurs.
	"""
	return Fournisseur.query.all()


def ajouter_fournisseur_service(form_data):
	"""
	Ajoute un fournisseur à la base de données à partir des données du formulaire.
	"""
	nom = form_data.get('nom_fournisseur')
	contact = form_data.get('contact')
	adresse = form_data.get('adresse')
	is_active = bool(int(form_data.get('is_active', 1)))
	nouveau_fournisseur = Fournisseur(
		nom_fournisseur=nom,
		contact=contact,
		adresse=adresse,
		is_active=is_active
	)
	db.session.add(nouveau_fournisseur)
	db.session.commit()
	return nouveau_fournisseur


def modifier_fournisseur_service(form_data):
	"""
	Modifie un fournisseur existant à partir des données du formulaire.
	"""
	fournisseur_id = form_data.get('id')
	fournisseur = Fournisseur.query.get(fournisseur_id)
	if not fournisseur:
		return None
	fournisseur.nom_fournisseur = form_data.get('nom_fournisseur', fournisseur.nom_fournisseur)
	fournisseur.contact = form_data.get('contact', fournisseur.contact)
	fournisseur.adresse = form_data.get('adresse', fournisseur.adresse)
	if 'is_active' in form_data:
		fournisseur.is_active = bool(int(form_data.get('is_active')))
	db.session.commit()
	return fournisseur

# --- SUPPRESSION FOURNISSEUR ---
def supprimer_fournisseur_service(fournisseur_id):
	"""
	Supprime un fournisseur de la base de données par son id.
	"""
	fournisseur = Fournisseur.query.get(fournisseur_id)
	if fournisseur:
		db.session.delete(fournisseur)
		db.session.commit()
		return True
	return False


# --- LOGIQUE ACHAT ---
def get_stats_achats():
	"""
	Retourne les statistiques globales des achats (approvisionnements).
	"""
	total_achats = sum(a.montant_total for a in Approvisionnement.query.all())
	achats_livres = Approvisionnement.query.filter_by(statut='Livré').count()
	achats_en_attente = Approvisionnement.query.filter_by(statut='En attente').count()
	achats_annules = Approvisionnement.query.filter_by(statut='Annulé').count()
	return {
		'total_achats': round(total_achats, 2),
		'achats_livres': achats_livres,
		'achats_en_attente': achats_en_attente,
		'achats_annules': achats_annules
	}