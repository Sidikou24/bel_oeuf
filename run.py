import os
from app import create_app, db
from app.models import User, Role, Product, Client, Commande, DetailCommande, Paiement, Fournisseur, Achat, MatierePremiere, Approvisionnement

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Role': Role,
        'Product': Product,
        'Client': Client,
        'Commande': Commande,
        'DetailCommande': DetailCommande,
        'Paiement': Paiement,
        'Fournisseur': Fournisseur,
        'Achat': Achat,
        'MatierePremiere': MatierePremiere,
        'Approvisionnement': Approvisionnement
    }

@app.cli.command()
def init_db():
    """Initialise la base de données avec des données de base"""
    print("🚀 Création des tables...")
    db.create_all()
    
    # 1. Créer les rôles
    print("👥 Création des rôles...")
    if not Role.query.first():
        roles = [
            Role(name='commercial', description='Commercial - Peut créer des commandes'),
            Role(name='responsable_commercial', description='Responsable Commercial - Valide les commandes')
        ]
        for role in roles:
            db.session.add(role)
        db.session.commit()
        print("   ✅ Rôles créés")
    
    # 2. Créer des utilisateurs de test
    print("🧑‍💼 Création des utilisateurs...")
    commercial_role = Role.query.filter_by(name='commercial').first()
    responsable_role = Role.query.filter_by(name='responsable_commercial').first()
    
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@ferme.com',
            prenom='Admin',
            nom='Système',
            role=responsable_role,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("   ✅ Utilisateur admin créé (admin/admin123)")
    
    if not User.query.filter_by(username='commercial1').first():
        commercial = User(
            username='commercial1',
            email='commercial@ferme.com',
            prenom='Jean',
            nom='Dupont',
            telephone='0123456789',
            role=commercial_role,
            is_active=True
        )
        commercial.set_password('commercial123')
        db.session.add(commercial)
        print("   ✅ Utilisateur commercial créé (commercial1/commercial123)")
    
    # 3. Créer des produits de base
    print("🥚 Création des produits...")
    if not Product.query.first():
        products = [
            Product(
                name='Œufs Bio (douzaine)', 
                description='Œufs biologiques de nos poules élevées au grand air',
                category='oeufs', 
                subcategory='bio', 
                price=4.50, 
                stock_quantity=50, 
                stock_minimum=10,
                unit='douzaine'
            ),
            Product(
                name='Œufs Fermiers (douzaine)', 
                description='Œufs de nos poules fermières, alimentation naturelle',
                category='oeufs', 
                subcategory='fermier', 
                price=3.50, 
                stock_quantity=80, 
                stock_minimum=15,
                unit='douzaine'
            ),
            Product(
                name='Œufs Plein Air (douzaine)', 
                description='Œufs de poules élevées en plein air',
                category='oeufs', 
                subcategory='plein_air', 
                price=3.00, 
                stock_quantity=100, 
                stock_minimum=20,
                unit='douzaine'
            ),
            Product(
                name='Poule Pondeuse Sussex', 
                description='Poule pondeuse de race Sussex, excellente productivité',
                category='poules', 
                subcategory='pondeuse', 
                price=15.00, 
                stock_quantity=12, 
                stock_minimum=3,
                unit='pièce'
            ),
            Product(
                name='Poule Pondeuse Rousse', 
                description='Poule pondeuse rousse, très rustique',
                category='poules', 
                subcategory='pondeuse', 
                price=12.00, 
                stock_quantity=18, 
                stock_minimum=5,
                unit='pièce'
            ),
        ]
        for product in products:
            db.session.add(product)
        print("   ✅ 5 produits créés")
    
    # 4. Créer quelques clients de test
    print("👥 Création des clients...")
    admin_user = User.query.filter_by(username='admin').first()
    
    if not Client.query.first():
        clients = [
            Client(
                nom='Martin',
                prenom='Pierre',
                telephone='0123456789',
                email='pierre.martin@email.com',
                adresse='123 Rue de la Ferme',
                ville='Ruralville',
                code_postal='12345',
                created_by=admin_user,
                notes='Client fidèle depuis 2020'
            ),
            Client(
                nom='Durand',
                prenom='Marie',
                telephone='0987654321',
                email='marie.durand@email.com',
                adresse='45 Avenue des Champs',
                ville='Campagnarde',
                code_postal='67890',
                created_by=admin_user,
                notes='Préfère les œufs bio'
            ),
            Client(
                nom='Leblanc',
                prenom='Jean',
                telephone='0147258369',
                email='jean.leblanc@email.com',
                adresse='78 Chemin Rural',
                ville='Villageville',
                code_postal='54321',
                created_by=admin_user
            )
        ]
        for client in clients:
            db.session.add(client)
        print("   ✅ 3 clients créés")
    
    # 5. Créer une commande d'exemple
    print("📦 Création d'une commande d'exemple...")
    commercial_user = User.query.filter_by(username='commercial1').first()
    client_exemple = Client.query.first()
    
    if client_exemple and commercial_user and not Commande.query.first():
        # Créer une commande
        commande = Commande(
            client=client_exemple,
            commercial=commercial_user,
            notes_commercial='Commande de test pour démonstration'
        )
        db.session.add(commande)
        db.session.flush()  # Pour avoir l'ID
        
        # Ajouter des produits
        produit_oeufs_bio = Product.query.filter_by(category='oeufs', subcategory='bio').first()
        produit_poule = Product.query.filter_by(category='poules').first()
        
        if produit_oeufs_bio:
            detail1 = DetailCommande(
                commande=commande,
                product=produit_oeufs_bio,
                quantite=3,
                prix_unitaire=produit_oeufs_bio.price
            )
            db.session.add(detail1)
        
        if produit_poule:
            detail2 = DetailCommande(
                commande=commande,
                product=produit_poule,
                quantite=1,
                prix_unitaire=produit_poule.price
            )
            db.session.add(detail2)
        
        commande.calculer_total()
        print("   ✅ Commande d'exemple créée")
    
    db.session.commit()
    
    # 6. Afficher un résumé
    print("\n" + "="*50)
    print("🎉 BASE DE DONNÉES INITIALISÉE AVEC SUCCÈS!")
    print("="*50)
    print(f"👥 Utilisateurs créés: {User.query.count()}")
    print(f"🏷️  Rôles créés: {Role.query.count()}")
    print(f"🥚 Produits créés: {Product.query.count()}")
    print(f"👤 Clients créés: {Client.query.count()}")
    print(f"📦 Commandes créées: {Commande.query.count()}")
    print(f"💰 Détails commandes: {DetailCommande.query.count()}")
    
    print("\n🔐 COMPTES DE CONNEXION:")
    print("   Admin: admin / admin123")
    print("   Commercial: commercial1 / commercial123")
    
    print(f"\n📊 TABLES CRÉÉES DANS LA DB:")
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    for table in sorted(tables):
        print(f"   📋 {table}")
    
    print("\n🚀 Vous pouvez maintenant lancer l'application!")

@app.cli.command()
def reset_db():
    """Supprime et recrée toutes les tables"""
    print("⚠️  Suppression de toutes les tables...")
    db.drop_all()
    print("✅ Tables supprimées")
    init_db()

@app.cli.command() 
def show_stats():
    """Affiche les statistiques de la base"""
    print("📊 STATISTIQUES DE LA BASE DE DONNÉES")
    print("="*40)
    
    print(f"👥 Utilisateurs: {User.query.count()}")
    for role in Role.query.all():
        count = User.query.filter_by(role=role).count()
        print(f"   - {role.name}: {count}")
    
    print(f"\n🥚 Produits: {Product.query.count()}")
    for category in Product.get_categories():
        count = Product.query.filter_by(category=category).count()
        print(f"   - {category}: {count}")
    
    print(f"\n👤 Clients: {Client.query.count()}")
    print(f"📦 Commandes: {Commande.query.count()}")
    
    for statut in ['en_attente', 'validee', 'annulee', 'livree']:
        count = Commande.query.filter_by(statut=statut).count()
        if count > 0:
            print(f"   - {statut}: {count}")
    
    print(f"💰 Paiements: {Paiement.query.count()}")

if __name__ == '__main__':
    app.run(debug=True)