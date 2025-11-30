"""
Helper utilities for Receipt Tracker
Common functions used across the application
"""

import os
import uuid
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_receipt_image(file) -> str:
    """Save uploaded receipt image and return filename"""
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(Config.RECEIPT_FOLDER, filename)
        file.save(filepath)
        return filename
    return None

def format_currency(amount: float) -> str:
    """Format amount as currency string"""
    return f"${amount:,.2f}"

def get_person_groups(personID: str):
    """Get all groups a person belongs to"""
    from models import GroupModel
    group_model = GroupModel()
    return group_model.get_by_member(personID)

def filter_by_person_access(items: list, personID: str) -> list:
    """Filter items to only show what the current person should see"""
    from models import GroupModel

    if not personID:
        return []
    
    group_model = GroupModel()
    person_groups = group_model.get_by_member(personID)
    group_ids = [g['id'] for g in person_groups]

    filtered = []
    for item in items:
        # Show if person owns it or is in the group
        if item.get('person') == personID or \
           item.get('group_id') in group_ids or \
           not item.get('group_id'):
            filtered.append(item)
    
    return filtered

def calculate_splits(total_amount: float, members: list) -> list:
    """Calculate equal splits for group members"""
    if not members:
        return []
    
    percentage = 100.0 / len(members)
    amount_per_person = total_amount / len(members)
    
    splits = []
    for member in members:
        splits.append({
            'person': member,
            'amount': round(amount_per_person, 2),
            'percentage': round(percentage, 2)
        })
    
    return splits

def get_current_month() -> str:
    """Get current month in YYYY-MM format"""
    from datetime import datetime
    return datetime.now().strftime('%Y-%m')

def get_date_range(months_back: int = 6) -> tuple:
    """Get date range for N months back"""
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30 * months_back)
    
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def parse_csv_safe(value: str, default=''):
    """Safely parse CSV value"""
    return value.strip() if value else default

def generate_unique_id() -> str:
    """Generate unique identifier"""
    return str(uuid.uuid4())