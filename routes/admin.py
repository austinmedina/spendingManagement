"""
Admin panel routes
"""

from flask import Blueprint, render_template
from auth import admin_required, get_current_user

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@admin_required
def admin_page():
    """Admin dashboard page"""
    user = get_current_user()
    
    return render_template(
        'admin.html',
        current_user=user
    )