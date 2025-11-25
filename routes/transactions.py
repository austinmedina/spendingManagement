"""
Transaction routes - Upload, manual entry, search
"""

from flask import Blueprint, render_template, request, jsonify, send_from_directory
from auth import login_required, get_current_user
from models import TransactionModel, SplitModel
from services.azure_service import azure_service
from services.notification_service import notification_service
from utils.helpers import (
    save_receipt_image, get_person_groups, 
    calculate_splits, generate_unique_id
)
from config import Config
import os
import shutil

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/upload')
@login_required
def upload_page():
    """Receipt upload page"""
    user = get_current_user()
    person = user['full_name']
    groups = get_person_groups(person)
    
    from models import AccountModel
    account_model = AccountModel()
    accounts = account_model.get_by_person(person)
    
    return render_template(
        'upload.html',
        categories=Config.EXPENSE_CATEGORIES,
        groups=groups,
        accounts=accounts,
        current_person=person
    )

@transactions_bp.route('/manual')
@login_required
def manual_page():
    """Manual entry page"""
    user = get_current_user()
    person = user['full_name']
    groups = get_person_groups(person)
    
    from models import AccountModel
    account_model = AccountModel()
    accounts = account_model.get_by_person(person)
    
    return render_template(
        'manual.html',
        categories=Config.EXPENSE_CATEGORIES,
        income_categories=Config.INCOME_CATEGORIES,
        groups=groups,
        accounts=accounts,
        current_person=person
    )

@transactions_bp.route('/search')
@login_required
def search_page():
    """Transaction search page"""
    user = get_current_user()
    person = user['full_name']
    groups = get_person_groups(person)
    
    return render_template(
        'search.html',
        categories=Config.EXPENSE_CATEGORIES,
        groups=groups,
        current_person=person
    )

@transactions_bp.route('/receipts/<filename>')
def serve_receipt(filename):
    """Serve receipt image"""
    return send_from_directory(Config.RECEIPT_FOLDER, filename)

@transactions_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_receipt():
    """Upload and process receipt"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    from werkzeug.utils import secure_filename
    if not file or not '.' in file.filename:
        return jsonify({'success': False, 'error': 'Invalid file'}), 400
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in Config.ALLOWED_EXTENSIONS:
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    # Save temporarily
    filename = secure_filename(file.filename)
    temp_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(temp_path)
    
    # Process with Azure
    result = azure_service.analyze_receipt(temp_path)
    
    if result['success']:
        # Move to permanent storage
        receipt_filename = f"{generate_unique_id()}.{ext}"
        permanent_path = os.path.join(Config.RECEIPT_FOLDER, receipt_filename)
        shutil.move(temp_path, permanent_path)
        result['receipt_image'] = receipt_filename
    else:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    return jsonify(result)

@transactions_bp.route('/api/save-items', methods=['POST'])
@login_required
def save_items():
    """Save receipt items as transactions"""
    user = get_current_user()
    person = user['full_name']
    
    data = request.json
    items = data.get('items', [])
    store = data.get('store', 'Unknown')
    date = data.get('date')
    bank_account = data.get('bank_account', '')
    receipt_image = data.get('receipt_image', '')
    group_id = data.get('group_id', '')
    splits = data.get('splits', [])
    
    # Generate unique receipt group ID
    receipt_group_id = generate_unique_id()
    
    # Save transactions
    transaction_model = TransactionModel()
    split_model = SplitModel()
    
    for item in items:
        transaction_model.create({
            'item_name': item.get('name', 'Unknown'),
            'category': item.get('category', 'Other'),
            'store': store,
            'date': date,
            'price': item.get('price', 0),
            'person': person,
            'bank_account': bank_account,
            'type': 'expense',
            'receipt_image': receipt_image,
            'group_id': group_id,
            'receipt_group_id': receipt_group_id if group_id else ''
        })
    
    # Save splits if group transaction
    if splits and group_id:
        for split in splits:
            split_model.create({
                'receipt_group_id': receipt_group_id,
                'person': split['person'],
                'amount': split['amount'],
                'percentage': split.get('percentage', 0)
            })
    
    # Check for large transaction alert
    total = sum(float(item.get('price', 0)) for item in items)
    notification_service.check_large_transaction_alert(person, total, store)
    
    return jsonify({'success': True, 'saved': len(items)})

@transactions_bp.route('/api/manual-entry', methods=['POST'])
@login_required
def manual_entry():
    """Manual transaction entry"""
    user = get_current_user()
    person = user['full_name']
    
    data = request.json
    group_id = data.get('group_id', '')
    receipt_group_id = generate_unique_id() if group_id else ''
    
    transaction_model = TransactionModel()
    split_model = SplitModel()
    
    # Create transaction
    transaction = transaction_model.create({
        'item_name': data.get('item_name', 'Unknown'),
        'category': data.get('category', 'Other'),
        'store': data.get('store', 'Unknown'),
        'date': data.get('date'),
        'price': data.get('price', 0),
        'person': person,
        'bank_account': data.get('bank_account', ''),
        'type': data.get('type', 'expense'),
        'receipt_image': '',
        'group_id': group_id,
        'receipt_group_id': receipt_group_id
    })
    
    # Save splits
    splits = data.get('splits', [])
    if splits and group_id:
        for split in splits:
            split_model.create({
                'receipt_group_id': receipt_group_id,
                'person': split['person'],
                'amount': split['amount'],
                'percentage': split.get('percentage', 0)
            })
    
    # Check for alerts
    if data.get('type') == 'expense':
        notification_service.check_large_transaction_alert(
            person, 
            float(data.get('price', 0)), 
            data.get('item_name', 'Unknown')
        )
    
    return jsonify({'success': True, 'transaction': transaction})