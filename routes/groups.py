"""
Group management routes
"""

from flask import Blueprint, render_template
from auth import login_required, get_current_user

groups_bp = Blueprint('groups', __name__)

@groups_bp.route('/groups')
@login_required
def groups_page():
    """Group management page"""
    user = get_current_user()
    person = user['full_name']
    
    return render_template(
        'groups.html',
        current_person=person
    )