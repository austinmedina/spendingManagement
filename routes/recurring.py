"""
Recurring transaction routes
"""

from flask import Blueprint, render_template
from auth import login_required, get_current_user
from utils.helpers import get_person_groups
from config import Config

recurring_bp = Blueprint('recurring', __name__)

@recurring_bp.route('/recurring')
@login_required
def recurring_page():
    """Recurring transactions page"""
    user = get_current_user()
    person = user['full_name']
    groups = get_person_groups(person)
    
    from models import AccountModel
    account_model = AccountModel()
    accounts = account_model.get_by_person(person)
    
    return render_template(
        'recurring.html',
        categories=Config.EXPENSE_CATEGORIES,
        income_categories=Config.INCOME_CATEGORIES,
        groups=groups,
        accounts=accounts,
        current_person=person
    )