"""
Authentication module with first-time password change and email reset
"""

import os
import csv
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, flash
from dotenv import load_dotenv

load_dotenv()

USERS_FILE = 'csv/users.csv'
RESET_CODES_FILE = 'csv/reset_codes.csv'
USER_HEADERS = ['id', 'username', 'password_hash', 'full_name', 'email', 'is_admin', 'active', 'must_change_password']
RESET_HEADERS = ['code', 'username', 'expires', 'used']

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM = os.getenv('SMTP_FROM', SMTP_USERNAME)

def init_users():
    """Initialize users file with default admin"""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=USER_HEADERS)
            writer.writeheader()
            # Default admin - must change password on first login
            writer.writerow({
                'id': '1',
                'username': 'admin',
                'password_hash': hash_password('admin123'),
                'full_name': 'Administrator',
                'email': 'admin@example.com',
                'is_admin': 'true',
                'active': 'true',
                'must_change_password': 'true'
            })
    
    # Initialize reset codes file
    if not os.path.exists(RESET_CODES_FILE):
        with open(RESET_CODES_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=RESET_HEADERS)
            writer.writeheader()

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

def get_user_by_full_name(username):
    """Get user by full name"""
    users = read_users()
    for user in users:
        if user['full_name'] == username:
            return user
    return None

def get_user_by_email(email):
    """Get user by email"""
    users = read_users()
    for user in users:
        if user.get('email', '').lower() == email.lower():
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

def must_change_password(user_id):
    """Check if user must change password"""
    user = get_user_by_id(user_id)
    return user and user.get('must_change_password', 'false') == 'true'

def change_password(user_id, new_password):
    """Change user password and clear must_change flag"""
    users = read_users()
    for user in users:
        if user['id'] == str(user_id):
            user['password_hash'] = hash_password(new_password)
            user['must_change_password'] = 'false'
    rewrite_users(users)

def create_user(username, password, full_name, email, is_admin=False):
    """Create a new user"""
    if get_user_by_username(username):
        return None
    if get_user_by_email(email):
        return None
    
    users = read_users()
    new_id = max([int(u['id']) for u in users]) + 1 if users else 1
    
    user = {
        'id': str(new_id),
        'username': username,
        'password_hash': hash_password(password),
        'full_name': full_name,
        'email': email,
        'is_admin': 'true' if is_admin else 'false',
        'active': 'true',
        'must_change_password': 'true'
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
            if 'email' in data:
                user['email'] = data['email']
            if 'password' in data and data['password']:
                user['password_hash'] = hash_password(data['password'])
                user['must_change_password'] = 'false'
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

# Password Reset Functions
def generate_reset_code():
    """Generate a 6-digit reset code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

def create_reset_code(username):
    """Create a password reset code"""
    user = get_user_by_username(username)
    if not user or user.get('active') != 'true':
        return None
    
    code = generate_reset_code()
    expires = (datetime.now() + timedelta(hours=1)).isoformat()
    
    # Read existing codes
    codes = []
    try:
        with open(RESET_CODES_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            codes = list(reader)
    except FileNotFoundError:
        init_users()
    
    # Add new code
    codes.append({
        'code': code,
        'username': username,
        'expires': expires,
        'used': 'false'
    })
    
    # Write back
    with open(RESET_CODES_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=RESET_HEADERS)
        writer.writeheader()
        for c in codes:
            writer.writerow(c)
    
    return code

def verify_reset_code(username, code):
    """Verify a reset code is valid"""
    try:
        with open(RESET_CODES_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            codes = list(reader)
    except FileNotFoundError:
        return False
    
    for c in codes:
        if c['username'] == username and c['code'] == code and c['used'] == 'false':
            expires = datetime.fromisoformat(c['expires'])
            if datetime.now() < expires:
                return True
    return False

def use_reset_code(username, code):
    """Mark a reset code as used"""
    try:
        with open(RESET_CODES_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            codes = list(reader)
    except FileNotFoundError:
        return
    
    for c in codes:
        if c['username'] == username and c['code'] == code:
            c['used'] = 'true'
    
    with open(RESET_CODES_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=RESET_HEADERS)
        writer.writeheader()
        for c in codes:
            writer.writerow(c)

def send_reset_email(username, code):
    """Send password reset email"""
    user = get_user_by_username(username)
    if not user:
        return False
    
    email = user.get('email')
    if not email or not SMTP_USERNAME or not SMTP_PASSWORD:
        # Email not configured, print code to console for development
        print(f"\n{'='*50}")
        print(f"PASSWORD RESET CODE FOR {username}: {code}")
        print(f"{'='*50}\n")
        return True
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Receipt Tracker - Password Reset Code'
        msg['From'] = SMTP_FROM
        msg['To'] = email
        
        text = f"""
Hello {user['full_name']},

Your password reset code is: {code}

This code will expire in 1 hour.

If you did not request this reset, please ignore this email.

- Receipt Tracker Team
        """
        
        html = f"""
<html>
  <body style="font-family: Arial, sans-serif;">
    <h2>Password Reset Request</h2>
    <p>Hello {user['full_name']},</p>
    <p>Your password reset code is:</p>
    <h1 style="background: #4361ee; color: white; padding: 20px; text-align: center; letter-spacing: 5px;">{code}</h1>
    <p>This code will expire in 1 hour.</p>
    <p>If you did not request this reset, please ignore this email.</p>
    <hr>
    <p style="color: #666; font-size: 12px;">Receipt Tracker Team</p>
  </body>
</html>
        """
        
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        # Fallback to console
        print(f"\n{'='*50}")
        print(f"PASSWORD RESET CODE FOR {username}: {code}")
        print(f"{'='*50}\n")
        return True

# Decorators
def login_required(f):
    """Require user to be logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('main.login'))
        
        # Check if password change required
        if must_change_password(session['user_id']):
            if f.__name__ != 'change_password_page' and f.__name__ != 'change_password_submit':
                flash('You must change your password before continuing.', 'warning')
                return redirect(url_for('main.change_password_page'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Require user to be admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('main.login'))
        
        user = get_user_by_id(session['user_id'])
        if not user or user.get('is_admin') != 'true':
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        
        if must_change_password(session['user_id']):
            flash('You must change your password before continuing.', 'warning')
            return redirect(url_for('main.change_password_page'))
        
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
