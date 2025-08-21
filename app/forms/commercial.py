# app/forms/commercial.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired, Email, Optional, NumberRange, Length
from wtforms.widgets import TextArea

class ClientForm(FlaskForm):
    nom = StringField('Nom', validators=[
        DataRequired(message="Le nom est obligatoire"),
        Length(min=2, max=100, message="Le nom doit faire entre 2 et 100 caractères")
    ])
    prenom = StringField('Prénom', validators=[
        DataRequired(message="Le prénom est obligatoire"),
        Length(min=2, max=100, message="Le prénom doit faire entre 2 et 100 caractères")
    ])
    telephone = StringField('Téléphone', validators=[
        Optional(),
        Length(max=20, message="Le téléphone ne peut pas dépasser 20 caractères")
    ])
    email = StringField('Email', validators=[
        Optional(),
        Email(message="Format d'email invalide"),
        Length(max=120, message="L'email ne peut pas dépasser 120 caractères")
    ])
    adresse = TextAreaField('Adresse', validators=[Optional()])
    ville = StringField('Ville', validators=[
        Optional(),
        Length(max=100, message="La ville ne peut pas dépasser 100 caractères")
    ])
    code_postal = StringField('Code postal', validators=[
        Optional(),
        Length(max=10, message="Le code postal ne peut pas dépasser 10 caractères")
    ])
    notes = TextAreaField('Notes', validators=[Optional()])

class ProduitCommandeForm(FlaskForm):
    """Sous-formulaire pour un produit dans une commande"""
    product_id = SelectField('Produit', coerce=int, validators=[Optional()])
    quantite = IntegerField('Quantité', validators=[
        Optional(),
        NumberRange(min=1, message="La quantité doit être positive")
    ])

class CommandeForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[
        DataRequired(message="Vous devez sélectionner un client")
    ])
    notes = TextAreaField('Notes de commande', validators=[Optional()])
    
    # Formulaires dynamiques pour les produits (jusqu'à 10 lignes)
    produits = FieldList(FormField(ProduitCommandeForm), min_entries=5, max_entries=10)
    
    def __init__(self, *args, **kwargs):
        super(CommandeForm, self).__init__(*args, **kwargs)
        
        # Charger les produits disponibles
        from app.models import Product
        products = Product.query.filter_by(is_active=True).order_by(Product.category, Product.name).all()
        
        product_choices = [(0, 'Sélectionner un produit...')]
        current_category = None
        
        for product in products:
            if product.category != current_category:
                if current_category is not None:
                    product_choices.append((f'--- {product.category.upper()} ---', f'--- {product.category.upper()} ---'))
                current_category = product.category
            
            stock_info = f" (Stock: {product.stock_quantity})"
            if product.stock_faible:
                stock_info += " ⚠️"
            
            product_choices.append((
                product.id, 
                f"{product.name} - {product.price}€/{product.unit}{stock_info}"
            ))
        
        # Appliquer les choix à tous les sous-formulaires
        for produit_form in self.produits:
            produit_form.product_id.choices = product_choices
