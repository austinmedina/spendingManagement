"""
Main dashboard and core page routes
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from auth import (
    login_required, get_current_user, verify_password, 
    get_user_by_username, must_change_password, change_password
)
from utils.helpers import get_person_groups
from services.recurring_processor import process_recurring_transactions
from services.notification_service import notification_service

main_bp = Blueprint('main', __name__)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if verify_password(username, password):
            user = get_user_by_username(username)
            session['user_id'] = user['id']
            session['username'] = user['username']
            
            # Check if must change password
            if must_change_password(user['id']):
                flash('You must change your password before continuing.', 'warning')
                return redirect(url_for('main.change_password_page'))
            
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

@main_bp.route('/change-password', methods=['GET', 'POST'])
def change_password_page():
    """Change password page"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
        elif new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
        else:
            change_password(session['user_id'], new_password)
            flash('Password changed successfully! Please log in with your new password.', 'success')
            session.clear()
            return redirect(url_for('main.login'))
    
    user = get_current_user()
    return render_template('change_password.html', user=user)

@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if request.method == 'POST':
        username = request.form.get('username')
        from auth import create_reset_code, send_reset_email, get_user_by_username
        
        user = get_user_by_username(username)
        if user:
            code = create_reset_code(username)
            if code:
                send_reset_email(username, code)
                flash('Password reset code sent to your email.', 'success')
                return redirect(url_for('main.reset_password', username=username))
        
        flash('If the username exists, a reset code has been sent.', 'info')
    
    return render_template('forgot_password.html')

@main_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password page"""
    username = request.args.get('username', '')
    
    if request.method == 'POST':
        username = request.form.get('username')
        code = request.form.get('code')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        from auth import verify_reset_code, use_reset_code, get_user_by_username
        
        if not verify_reset_code(username, code):
            flash('Invalid or expired reset code.', 'danger')
        elif len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
        elif new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
        else:
            user = get_user_by_username(username)
            if user:
                change_password(user['id'], new_password)
                use_reset_code(username, code)
                flash('Password reset successfully! You can now log in.', 'success')
                return redirect(url_for('main.login'))
    
    return render_template('reset_password.html', username=username)

@main_bp.route('/')
@login_required
def dashboard():
    """Enhanced dashboard with analytics"""
    user = get_current_user()
    person = {"id":user["id"], "full_name":user["full_name"]}
    
    # Process recurring transactions
    process_recurring_transactions()
    
    # Check for alerts and reminders
    notification_service.check_budget_alerts(person['id'])
    notification_service.check_recurring_reminders(person['id'])
    
    # Get user's groups
    groups = get_person_groups(person["id"])
    
    return render_template(
        'dashboard_enhanced.html',
        current_person=person,
        people_groups=groups,
        current_user=user
    )

@main_bp.route('/switch-person/<person>')
@login_required
def switch_person(person):
    """Switch current person view"""
    session['current_person'] = person
    return redirect(url_for('main.dashboard'))