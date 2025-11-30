"""
Budget management routes
"""

from flask import Blueprint, render_template
from auth import login_required, get_current_user
from config import Config

budgets_bp = Blueprint('budgets', __name__)

@budgets_bp.route('/budgets')
@login_required
def budgets_page():
    """Budget management page"""
    user = get_current_user()
    person = {"id":user["id"], "full_name":user["full_name"]}
    
    return render_template(
        'budgets.html',
        categories=Config.EXPENSE_CATEGORIES,
        current_person=person
    )