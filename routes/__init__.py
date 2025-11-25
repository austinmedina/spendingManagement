"""
Routes package initialization
"""

from .main import main_bp
from .api import api_bp
from .transactions import transactions_bp
from .budgets import budgets_bp
from .recurring import recurring_bp
from .accounts import accounts_bp
from .groups import groups_bp
from .admin import admin_bp

__all__ = [
    'main_bp',
    'api_bp',
    'transactions_bp',
    'budgets_bp',
    'recurring_bp',
    'accounts_bp',
    'groups_bp',
    'admin_bp'
]