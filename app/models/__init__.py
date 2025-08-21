# app/models/__init__.py
from .user import User, Role
from .client import Client
from .product import Product
from .commande import Commande
from .detail_commande import DetailCommande
from .paiement import Paiement

__all__ = ['User', 'Role', 'Client', 'Product', 'Commande', 'DetailCommande', 'Paiement']
