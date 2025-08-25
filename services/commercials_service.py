from app import db
from app.models import Fournisseur, MatierePremiere, Approvisionnement

# --- LOGIQUE MATIERE PREMIERE ---
def get_matieres():
    """
    Retourne la liste des matières premières actives.
    """
    return MatierePremiere.query.filter_by(is_active=True).all()

def get_stats_matieres():
    """
    Retourne les statistiques des matières premières
    """
    stats = {
        'total_matieres': MatierePremiere.query.filter_by(is_active=True).count(),
        'stock_ok': MatierePremiere.query.filter(
            MatierePremiere.stock_actuel > MatierePremiere.stock_minimum,
            MatierePremiere.is_active == True
        ).count(),
        'stock_faible': MatierePremiere.query.filter(
            MatierePremiere.stock_actuel <= MatierePremiere.stock_minimum,
            MatierePremiere.stock_actuel > 0,
            MatierePremiere.is_active == True
        ).count(),
        'rupture': MatierePremiere.query.filter(
            MatierePremiere.stock_actuel == 0,
            MatierePremiere.is_active == True
        ).count()
    }
    
    # Calculer la valeur totale du stock
    valeur_totale = db.session.query(
        db.func.sum(MatierePremiere.stock_actuel * MatierePremiere.prix_unitaire)
    ).filter(MatierePremiere.is_active == True).scalar() or 0
    
    stats['valeur_totale'] = round(valeur_totale, 2)
    return stats

def ajouter_matiere_service(form_data):
    """
    Ajoute une matière première à partir des données du formulaire
    """
    try:
        # Validation des champs requis
        required_fields = ['nom', 'categorie', 'unite']
        for field in required_fields:
            if not form_data.get(field):
                return None, f"Le champ {field} est requis"

        # Convertir et valider les valeurs numériques
        try:
            prix_unitaire = float(form_data.get('prix_unitaire') or 0)
            stock_actuel = int(form_data.get('stock_actuel') or 0)
            stock_minimum = int(form_data.get('stock_minimum') or 5)
        except ValueError:
            return None, "Les valeurs numériques sont invalides"

        matiere = MatierePremiere(
            nom=form_data.get('nom'),
            description=form_data.get('description'),
            categorie=form_data.get('categorie'),
            sous_categorie=form_data.get('sous_categorie'),
            unite=form_data.get('unite'),
            prix_unitaire=prix_unitaire,
            stock_actuel=stock_actuel,
            stock_minimum=stock_minimum
        )
        db.session.add(matiere)
        db.session.commit()
        return matiere, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)

def modifier_matiere_service(matiere_id, form_data):
    """
    Modifie une matière première existante
    """
    try:
        matiere = MatierePremiere.query.get(matiere_id)
        if not matiere:
            return None, "Matière première non trouvée"
            
        # Validation des champs requis
        if 'nom' in form_data and not form_data.get('nom'):
            return None, "Le nom est requis"
        if 'categorie' in form_data and not form_data.get('categorie'):
            return None, "La catégorie est requise"
        if 'unite' in form_data and not form_data.get('unite'):
            return None, "L'unité est requise"

        # Mise à jour des champs texte
        if form_data.get('nom'):
            matiere.nom = form_data['nom']
        if 'description' in form_data:
            matiere.description = form_data.get('description')
        if form_data.get('categorie'):
            matiere.categorie = form_data['categorie']
        if 'sous_categorie' in form_data:
            matiere.sous_categorie = form_data.get('sous_categorie')
        if form_data.get('unite'):
            matiere.unite = form_data['unite']
        
        # Mise à jour des valeurs numériques
        try:
            if 'prix_unitaire' in form_data:
                matiere.prix_unitaire = float(form_data.get('prix_unitaire') or 0)
            if 'stock_actuel' in form_data:
                matiere.stock_actuel = int(form_data.get('stock_actuel') or 0)
            if 'stock_minimum' in form_data:
                matiere.stock_minimum = int(form_data.get('stock_minimum') or 5)
        except ValueError:
            return None, "Les valeurs numériques sont invalides"
            
        db.session.commit()
        return matiere, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)

def supprimer_matiere_service(matiere_id):
    """
    Supprime une matière première (soft delete)
    """
    try:
        matiere = MatierePremiere.query.get(matiere_id)
        if not matiere:
            return False, "Matière première non trouvée"
            
        matiere.is_active = False
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def get_categories_matieres():
    """
    Retourne la liste des catégories uniques des matières premières
    """
    return [cat[0] for cat in db.session.query(MatierePremiere.categorie).distinct().all() if cat[0]]

def get_sous_categories_matieres(categorie):
    """
    Retourne la liste des sous-catégories pour une catégorie donnée
    """
    return [
        scat[0] for scat in db.session.query(MatierePremiere.sous_categorie)
        .filter(MatierePremiere.categorie == categorie)
        .distinct().all() if scat[0]
    ]

# --- LOGIQUE APPROVISIONNEMENT ---
def get_achats():
    """
    Retourne la liste des achats (approvisionnements).
    """
    return Approvisionnement.query.all()



def ajouter_achat_service(form_data):
    """
    Ajoute un achat (approvisionnement) à la base de données à partir des données du formulaire.
    Le stock n'est pas mis à jour tant que l'achat n'est pas validé et livré.
    """
    try:
        # Validation des données
        fournisseur_id = form_data.get('fournisseur_id')
        matiere_id = form_data.get('matiere_id')
        quantite = float(form_data.get('quantite', 0))
        
        # Récupérer la matière première
        matiere = MatierePremiere.query.get(matiere_id)
        if not matiere:
            raise ValueError("Matière première non trouvée")
            
        # Dates
        from datetime import datetime, date
        def parse_date(val):
            if val:
                return datetime.strptime(val, "%Y-%m-%d").date()
            return None
            
        date_achat = parse_date(form_data.get('date_achat')) or date.today()
        date_livraison_prevue = parse_date(form_data.get('date_livraison_prevue'))
        
        # Création de l'achat (initialement en attente de validation)
        nouvel_achat = Approvisionnement(
            date_achat=date_achat,
            fournisseur_id=fournisseur_id,
            matiere_id=matiere_id,
            quantite=quantite,
            prix_unitaire=matiere.prix_unitaire,
            montant_total=quantite * matiere.prix_unitaire,
            statut='En attente de validation',
            date_livraison_prevue=date_livraison_prevue
        )
        
        # Sauvegarder l'achat
        db.session.add(nouvel_achat)
        db.session.commit()
        
        return nouvel_achat
        
    except Exception as e:
        db.session.rollback()
        raise e

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
    Met à jour le stock uniquement quand l'achat est validé et livré.
    """
    try:
        from datetime import datetime
        def parse_date(val):
            if val:
                return datetime.strptime(val, "%Y-%m-%d").date()
            return None

        # Récupérer l'achat
        achat_id = form_data.get('id')
        achat = Approvisionnement.query.get(achat_id)
        if not achat:
            return None

        # Sauvegarder l'ancien statut pour comparaison
        ancien_statut = achat.statut
        nouveau_statut = form_data.get('statut', ancien_statut)

        # Récupérer la matière première
        matiere = MatierePremiere.query.get(achat.matiere_id)
        if not matiere:
            return None

        # Vérifier la validité du changement de statut
        if nouveau_statut == 'Livré' and ancien_statut not in ['Validé', 'En attente de livraison']:
            raise ValueError("Un achat doit être validé avant d'être livré")

        # Mettre à jour les champs de base
        achat.date_achat = parse_date(form_data.get('date_achat')) or achat.date_achat
        achat.quantite = float(form_data.get('quantite', achat.quantite))
        achat.statut = nouveau_statut
        achat.date_livraison_prevue = parse_date(form_data.get('date_livraison_prevue'))

        # Gestion des différents changements de statut
        if nouveau_statut == 'Validé' and ancien_statut == 'En attente de validation':
            # L'achat vient d'être validé, on le met en attente de livraison
            achat.statut = 'En attente de livraison'
        elif nouveau_statut == 'Non validé':
            # L'achat est refusé
            if ancien_statut == 'Livré':
                # Si l'achat était livré, on retire du stock
                matiere.stock_actuel = matiere.stock_actuel - int(achat.quantite)
                achat.date_livraison_reelle = None
        elif nouveau_statut == 'Livré' and ancien_statut != 'Livré':
            # L'achat validé vient d'être livré
            matiere.stock_actuel = matiere.stock_actuel + int(achat.quantite)
            achat.date_livraison_reelle = datetime.now().date()

        # Recalculer le montant total
        achat.prix_unitaire = matiere.prix_unitaire
        achat.montant_total = achat.quantite * achat.prix_unitaire

        db.session.commit()
        return achat

    except Exception as e:
        db.session.rollback()
        raise e
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

def confirmer_livraison_service(form_data):
    """
    Confirme la livraison d'un achat et met à jour le stock.
    """
    try:
        # Récupérer l'achat
        achat_id = form_data.get('achat_id')
        achat = Approvisionnement.query.get(achat_id)
        if not achat:
            raise ValueError("Achat non trouvé")
            
        # Vérifier que l'achat est en attente
        if achat.statut != 'En attente':
            raise ValueError("Impossible de confirmer la livraison: l'achat n'est pas en attente")
            
        # Récupérer et valider la date de livraison
        from datetime import datetime
        date_livraison = datetime.strptime(form_data.get('date_livraison'), "%Y-%m-%d").date()
        
        # Mise à jour de l'achat
        achat.statut = 'Livrée'
        achat.date_livraison_reelle = date_livraison
        achat.notes_livraison = form_data.get('notes_livraison')
        
        # Mise à jour du stock de la matière première
        matiere = MatierePremiere.query.get(achat.matiere_id)
        if not matiere:
            raise ValueError("Matière première non trouvée")
            
        matiere.stock_actuel += achat.quantite
        
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        raise e

def get_stats_achats():
    """
    Retourne les statistiques globales des achats (approvisionnements).
    Le total des achats ne prend en compte que les achats validés et livrés.
    """
    # Total des achats validés/livrés uniquement
    total_achats = sum(a.montant_total for a in Approvisionnement.query.filter(
        Approvisionnement.statut.in_(['Livré', 'En attente de livraison'])
    ).all())

    # Comptage des différents statuts
    achats_livres = Approvisionnement.query.filter_by(statut='Livré').count()
    achats_en_attente_validation = Approvisionnement.query.filter_by(statut='En attente de validation').count()
    achats_en_attente_livraison = Approvisionnement.query.filter_by(statut='En attente de livraison').count()
    achats_non_valides = Approvisionnement.query.filter_by(statut='Non validé').count()
    
    return {
        'total_achats': round(total_achats, 2),
        'achats_livres': achats_livres,
        'achats_en_attente_validation': achats_en_attente_validation,
        'achats_en_attente_livraison': achats_en_attente_livraison,
        'achats_non_valides': achats_non_valides,
        'achats_en_attente': achats_en_attente_validation + achats_en_attente_livraison  # Pour l'affichage dans la carte
    }

