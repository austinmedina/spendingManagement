"""
Account management routes
"""

from flask import Blueprint, render_template
from auth import login_required, get_current_user

accounts_bp = Blueprint('accounts', __name__)

@accounts_bp.route('/accounts')
@login_required
def accounts_page():
    """Account management page"""
    user = get_current_user()
    person = user['full_name']
    
    return render_template(
        'accounts.html',
        current_person=person
    )