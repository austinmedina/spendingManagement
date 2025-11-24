"""
Authentication module for user management
"""

import os
import csv
import hashlib
from functools import wraps
from flask import session, redirect, url_for, flash

USERS_FILE = 'users.csv'
USER_HEADERS = ['id', 'username', 'password_hash', 'full_name', 'is_admin', 'active']

def init_users():
    """Initialize users file with default admin"""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=USER_HEADERS)
            writer.writeheader()
            # Default admin user: admin / admin123
            writer.writerow({
                'id': '1',
                'username': 'admin',
                'password_hash': hash_password('admin123'),
                'full_name': 'Administrator',
                'is_admin': 'true',
                'active': 'true'
            })
            # Default regular users
            writer.writerow({
                'id': '2',
                'username': 'john',
                'password_hash': hash_password('password'),
                'full_name': 'John',
                'is_admin': 'false',
                'active': 'true'
            })
            writer.writerow({
                'id': '3',
                'username': 'jane',
                'password_hash': hash_password('password'),
                'full_name': 'Jane',
                'is_admin': 'false',
                'active': 'true'
            })

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def read_users():
    """Read all users from CSV"""
    users = []
    try:
        with open(USERS_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.append(row)
    except FileNotFoundError:
        init_users()
        return read_users()
    return users

def write_user(user):
    """Write a single user to CSV"""
    with open(USERS_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=USER_HEADERS)
        writer.writerow(user)

def rewrite_users(users):
    """Rewrite entire users file"""
    with open(USERS_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=USER_HEADERS)
        writer.writeheader()
        for user in users:
            writer.writerow(user)

def get_user_by_username(username):
    """Get user by username"""
    users = read_users()
    for user in users:
        if user['username'] == username:
            return user
    return None

def get_user_by_id(user_id):
    """Get user by ID"""
    users = read_users()
    for user in users:
        if user['id'] == str(user_id):
            return user
    return None

def verify_password(username, password):
    """Verify username and password"""
    user = get_user_by_username(username)
    if not user:
        return False
    if user.get('active') != 'true':
        return False
    return user['password_hash'] == hash_password(password)

def create_user(username, password, full_name, is_admin=False):
    """Create a new user"""
    # Check if username exists
    if get_user_by_username(username):
        return None
    
    users = read_users()
    new_id = max([int(u['id']) for u in users]) + 1 if users else 1
    
    user = {
        'id': str(new_id),
        'username': username,
        'password_hash': hash_password(password),
        'full_name': full_name,
        'is_admin': 'true' if is_admin else 'false',
        'active': 'true'
    }
    write_user(user)
    return user

def update_user(user_id, data):
    """Update user data"""
    users = read_users()
    for user in users:
        if user['id'] == str(user_id):
            if 'username' in data:
                user['username'] = data['username']
            if 'full_name' in data:
                user['full_name'] = data['full_name']
            if 'password' in data and data['password']:
                user['password_hash'] = hash_password(data['password'])
            if 'is_admin' in data:
                user['is_admin'] = 'true' if data['is_admin'] else 'false'
            if 'active' in data:
                user['active'] = 'true' if data['active'] else 'false'
    rewrite_users(users)

def delete_user(user_id):
    """Delete a user (set inactive)"""
    users = read_users()
    for user in users:
        if user['id'] == str(user_id):
            user['active'] = 'false'
    rewrite_users(users)

# Decorators for route protection
def login_required(f):
    """Require user to be logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Require user to be admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        user = get_user_by_id(session['user_id'])
        if not user or user.get('is_admin') != 'true':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get currently logged in user"""
    if 'user_id' not in session:
        return None
    return get_user_by_id(session['user_id'])

def is_admin():
    """Check if current user is admin"""
    user = get_current_user()
    return user and user.get('is_admin') == 'true'
