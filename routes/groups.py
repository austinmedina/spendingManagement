"""
Group management routes
"""

from flask import Blueprint, render_template
from auth import login_required, get_current_user, read_users

groups_bp = Blueprint('groups', __name__)

@groups_bp.route('/groups')
@login_required
def groups_page():
    """Group management page"""
    user = get_current_user()
    person = {"id":user["id"], "full_name":user["full_name"]}
    users = read_users()
    username = []
    for user in users:
        username.append({"full_name":user['full_name'], "id":user['id']})
    
    return render_template(
        'groups.html',
        current_person=person,
        users=users
    )