"""
Receipt Tracker Web Application
Flask backend with Azure Document Intelligence integration
Multi-user support with groups and split transactions
"""

import os
import csv
import json
import uuid
import shutil
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from werkzeug.utils import secure_filename
import requests
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RECEIPT_FOLDER'] = 'receipts'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'pdf'}

# Categories
CATEGORIES = ['Rent', 'Electric', 'Investment', 'Car', 'Medical', 'Groceries',
              'Entertainment', 'Subscriptions', 'Household', 'Eating Out', 'Shopping', 'Other']
INCOME_CATEGORIES = ['Salary', 'Freelance', 'Investment', 'Gift', 'Refund', 'Other']

# Database configuration
USE_CSV = os.getenv('USE_CSV', 'true').lower() == 'true'
CSV_FILES = {
    'transactions': 'database.csv',
    'budgets': 'budgets.csv',
    'recurring': 'recurring.csv',
    'accounts': 'accounts.csv',
    'groups': 'groups.csv',
    'splits': 'splits.csv'
}

# Azure Document Intelligence
AZURE_ENDPOINT = os.getenv('AZURE_DOC_INTELLIGENCE_ENDPOINT', '')
AZURE_KEY = os.getenv('AZURE_DOC_INTELLIGENCE_KEY', '')

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RECEIPT_FOLDER'], exist_ok=True)

# CSV Headers
CSV_HEADERS = {
    'transactions': ['id', 'item_name', 'category', 'store', 'date', 'price', 'person', 'bank_account', 'type', 'receipt_image', 'group_id', 'paid_by'],
    'budgets': ['id', 'category', 'amount', 'period', 'start_date', 'person'],
    'recurring': ['id', 'item_name', 'category', 'store', 'price', 'person', 'bank_account', 'type', 'frequency', 'next_date', 'active', 'group_id'],
    'accounts': ['id', 'name', 'type', 'person'],
    'groups': ['id', 'name', 'members'],
    'splits': ['id', 'transaction_id', 'person', 'amount', 'percentage']
}

def init_csv():
    # Transactions
    if not os.path.exists(CSV_FILES['transactions']):
        with open(CSV_FILES['transactions'], 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS['transactions'])
            writer.writeheader()
            samples = [
                {'id': '1', 'item_name': 'Weekly Groceries', 'category': 'Groceries', 'store': 'Walmart', 'date': '2025-01-15', 'price': '145.99', 'person': 'John', 'bank_account': 'Chase Checking', 'type': 'expense', 'receipt_image': '', 'group_id': '1', 'paid_by': 'John'},
                {'id': '2', 'item_name': 'Gas', 'category': 'Car', 'store': 'Shell', 'date': '2025-01-14', 'price': '55.00', 'person': 'John', 'bank_account': 'Chase Checking', 'type': 'expense', 'receipt_image': '', 'group_id': '1', 'paid_by': 'John'},
                {'id': '3', 'item_name': 'Salary', 'category': 'Salary', 'store': 'Employer', 'date': '2025-01-01', 'price': '3500.00', 'person': 'John', 'bank_account': 'Chase Checking', 'type': 'income', 'receipt_image': '', 'group_id': '', 'paid_by': 'John'},
            ]
            for row in samples:
                writer.writerow(row)
    
    # Budgets
    if not os.path.exists(CSV_FILES['budgets']):
        with open(CSV_FILES['budgets'], 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS['budgets'])
            writer.writeheader()
            samples = [
                {'id': '1', 'category': 'Groceries', 'amount': '400', 'period': 'monthly', 'start_date': '2025-01-01', 'person': 'John'},
                {'id': '2', 'category': 'Entertainment', 'amount': '100', 'period': 'monthly', 'start_date': '2025-01-01', 'person': 'John'},
            ]
            for row in samples:
                writer.writerow(row)
    
    # Recurring
    if not os.path.exists(CSV_FILES['recurring']):
        with open(CSV_FILES['recurring'], 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS['recurring'])
            writer.writeheader()
            samples = [
                {'id': '1', 'item_name': 'Netflix', 'category': 'Subscriptions', 'store': 'Netflix', 'price': '15.99', 'person': 'John', 'bank_account': 'Visa Credit', 'type': 'expense', 'frequency': 'monthly', 'next_date': '2025-02-10', 'active': 'true', 'group_id': '1'},
                {'id': '2', 'item_name': 'Rent', 'category': 'Rent', 'store': 'Landlord', 'price': '1200.00', 'person': 'John', 'bank_account': 'Chase Checking', 'type': 'expense', 'frequency': 'monthly', 'next_date': '2025-02-01', 'active': 'true', 'group_id': '1'},
            ]
            for row in samples:
                writer.writerow(row)
    
    # Accounts
    if not os.path.exists(CSV_FILES['accounts']):
        with open(CSV_FILES['accounts'], 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS['accounts'])
            writer.writeheader()
            samples = [
                {'id': '1', 'name': 'Chase Checking', 'type': 'checking', 'person': 'John'},
                {'id': '2', 'name': 'Visa Credit', 'type': 'credit', 'person': 'John'},
                {'id': '3', 'name': 'Savings', 'type': 'savings', 'person': 'John'},
            ]
            for row in samples:
                writer.writerow(row)
    
    # Groups
    if not os.path.exists(CSV_FILES['groups']):
        with open(CSV_FILES['groups'], 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS['groups'])
            writer.writeheader()
            samples = [
                {'id': '1', 'name': 'Household', 'members': 'John,Jane'},
                {'id': '2', 'name': 'Roommates', 'members': 'Alice,Bob'},
            ]
            for row in samples:
                writer.writerow(row)
    
    # Splits
    if not os.path.exists(CSV_FILES['splits']):
        with open(CSV_FILES['splits'], 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS['splits'])
            writer.writeheader()

init_csv()

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_next_id(table):
    items = read_csv(table)
    if not items:
        return 1
    return max(int(t['id']) for t in items) + 1

def read_csv(table):
    filename = CSV_FILES[table]
    headers = CSV_HEADERS[table]
    items = []
    try:
        with open(filename, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                items.append(row)
    except FileNotFoundError:
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
    return items

def write_csv_row(table, row):
    filename = CSV_FILES[table]
    headers = CSV_HEADERS[table]
    with open(filename, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writerow(row)

def rewrite_csv(table, rows):
    filename = CSV_FILES[table]
    headers = CSV_HEADERS[table]
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def get_current_person():
    return session.get('current_person', 'John')

def get_person_groups(person):
    groups = read_csv('groups')
    return [g for g in groups if person in g['members'].split(',')]

def get_group_members(group_id):
    groups = read_csv('groups')
    for g in groups:
        if g['id'] == group_id:
            return g['members'].split(',')
    return []

def filter_by_person_access(items, person=None):
    """Filter items to only show what the current person should see"""
    if person is None:
        person = get_current_person()
    
    person_groups = get_person_groups(person)
    group_ids = [g['id'] for g in person_groups]
    
    filtered = []
    for item in items:
        # Show if person owns it or is in the group
        if item.get('person') == person or item.get('group_id') in group_ids or not item.get('group_id'):
            filtered.append(item)
    
    return filtered

def save_receipt_image(file):
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['RECEIPT_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

def categorize_item(item_name):
    item_lower = item_name.lower()
    mappings = {
        'Groceries': ['milk', 'bread', 'cheese', 'meat', 'vegetable', 'fruit', 'grocery', 'food'],
        'Car': ['gas', 'fuel', 'parking', 'toll', 'car wash', 'oil change', 'tire'],
        'Entertainment': ['movie', 'game', 'concert', 'ticket', 'bowling'],
        'Subscriptions': ['netflix', 'spotify', 'hulu', 'disney', 'amazon prime', 'subscription'],
        'Electric': ['electric', 'power', 'utility'],
        'Medical': ['medicine', 'pharmacy', 'doctor', 'medical', 'health', 'hospital'],
        'Household': ['cleaning', 'paper towel', 'toilet paper', 'detergent', 'home'],
        'Eating Out': ['restaurant', 'cafe', 'coffee', 'pizza', 'burger', 'takeout'],
        'Shopping': ['clothes', 'shoes', 'amazon', 'target', 'clothing'],
        'Rent': ['rent', 'lease'],
        'Investment': ['stock', 'etf', 'investment', '401k'],
    }
    for category, keywords in mappings.items():
        if any(kw in item_lower for kw in keywords):
            return category
    return 'Other'

def process_recurring_transactions():
    recurring = read_csv('recurring')
    today = datetime.now().date()
    updated = False
    
    for item in recurring:
        if item['active'] != 'true':
            continue
        next_date = datetime.strptime(item['next_date'], '%Y-%m-%d').date()
        
        while next_date <= today:
            transaction = {
                'id': str(get_next_id('transactions')),
                'item_name': item['item_name'],
                'category': item['category'],
                'store': item['store'],
                'date': next_date.strftime('%Y-%m-%d'),
                'price': item['price'],
                'person': item['person'],
                'bank_account': item['bank_account'],
                'type': item['type'],
                'receipt_image': '',
                'group_id': item.get('group_id', ''),
                'paid_by': item['person']
            }
            write_csv_row('transactions', transaction)
            
            # Update next date
            if item['frequency'] == 'daily':
                next_date += timedelta(days=1)
            elif item['frequency'] == 'weekly':
                next_date += timedelta(weeks=1)
            elif item['frequency'] == 'biweekly':
                next_date += timedelta(weeks=2)
            elif item['frequency'] == 'monthly':
                month = next_date.month + 1
                year = next_date.year + (month - 1) // 12
                month = ((month - 1) % 12) + 1
                day = min(next_date.day, [31,28,31,30,31,30,31,31,30,31,30,31][month-1])
                next_date = next_date.replace(year=year, month=month, day=day)
            elif item['frequency'] == 'yearly':
                next_date = next_date.replace(year=next_date.year + 1)
            
            item['next_date'] = next_date.strftime('%Y-%m-%d')
            updated = True
    
    if updated:
        rewrite_csv('recurring', recurring)

def analyze_receipt_with_azure(image_path):
    if not AZURE_ENDPOINT or not AZURE_KEY:
        return {
            'success': True, 'store': 'Sample Store',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'items': [
                {'name': 'Sample Item 1', 'price': 9.99, 'category': 'Groceries'},
                {'name': 'Sample Item 2', 'price': 14.99, 'category': 'Groceries'},
            ],
            'total': 24.98
        }
    
    analyze_url = f"{AZURE_ENDPOINT}/formrecognizer/documentModels/prebuilt-receipt:analyze?api-version=2023-07-31"
    headers = {'Content-Type': 'application/octet-stream', 'Ocp-Apim-Subscription-Key': AZURE_KEY}
    
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    response = requests.post(analyze_url, headers=headers, data=image_data)
    if response.status_code != 202:
        return {'success': False, 'error': f'Failed: {response.text}'}
    
    operation_url = response.headers.get('Operation-Location')
    import time
    for _ in range(30):
        time.sleep(1)
        result = requests.get(operation_url, headers={'Ocp-Apim-Subscription-Key': AZURE_KEY}).json()
        if result.get('status') == 'succeeded':
            return parse_azure_response(result)
        elif result.get('status') == 'failed':
            return {'success': False, 'error': 'Analysis failed'}
    return {'success': False, 'error': 'Timeout'}

def parse_azure_response(result):
    items, store, date, total = [], 'Unknown', datetime.now().strftime('%Y-%m-%d'), 0.0
    try:
        docs = result.get('analyzeResult', {}).get('documents', [])
        if docs:
            fields = docs[0].get('fields', {})
            if 'MerchantName' in fields:
                store = fields['MerchantName'].get('valueString', 'Unknown')
            if 'TransactionDate' in fields and fields['TransactionDate'].get('valueDate'):
                date = fields['TransactionDate']['valueDate']
            if 'Items' in fields:
                for item in fields['Items'].get('valueArray', []):
                    f = item.get('valueObject', {})
                    name = f.get('Description', {}).get('valueString', 'Unknown')
                    price = f.get('TotalPrice', {}).get('valueCurrency', {}).get('amount', 0)
                    items.append({'name': name, 'price': float(price), 'category': categorize_item(name)})
            if 'Total' in fields:
                total = fields['Total'].get('valueCurrency', {}).get('amount', 0)
    except Exception as e:
        return {'success': False, 'error': str(e)}
    return {'success': True, 'store': store, 'date': date, 'items': items, 'total': float(total)}


# Routes
@app.route('/')
def dashboard():
    process_recurring_transactions()
    person = get_current_person()
    groups = get_person_groups(person)
    all_people = set()
    for g in groups:
        all_people.update(g['members'].split(','))
    return render_template('dashboard.html', categories=CATEGORIES, current_person=person, people=sorted(all_people))

@app.route('/upload')
def upload_page():
    person = get_current_person()
    groups = get_person_groups(person)
    accounts = filter_by_person_access(read_csv('accounts'))
    return render_template('upload.html', categories=CATEGORIES, groups=groups, accounts=accounts, current_person=person)

@app.route('/search')
def search_page():
    person = get_current_person()
    groups = get_person_groups(person)
    return render_template('search.html', categories=CATEGORIES, groups=groups, current_person=person)

@app.route('/manual')
def manual_page():
    person = get_current_person()
    groups = get_person_groups(person)
    accounts = filter_by_person_access(read_csv('accounts'))
    return render_template('manual.html', categories=CATEGORIES, income_categories=INCOME_CATEGORIES, groups=groups, accounts=accounts, current_person=person)

@app.route('/budgets')
def budgets_page():
    person = get_current_person()
    return render_template('budgets.html', categories=CATEGORIES, current_person=person)

@app.route('/recurring')
def recurring_page():
    person = get_current_person()
    groups = get_person_groups(person)
    accounts = filter_by_person_access(read_csv('accounts'))
    return render_template('recurring.html', categories=CATEGORIES, income_categories=INCOME_CATEGORIES, groups=groups, accounts=accounts, current_person=person)

@app.route('/accounts')
def accounts_page():
    person = get_current_person()
    return render_template('accounts.html', current_person=person)

@app.route('/groups')
def groups_page():
    person = get_current_person()
    return render_template('groups.html', current_person=person)

@app.route('/switch-person/<person>')
def switch_person(person):
    session['current_person'] = person
    return redirect(url_for('dashboard'))

@app.route('/receipts/<filename>')
def serve_receipt(filename):
    return send_from_directory(app.config['RECEIPT_FOLDER'], filename)

# API Routes
@app.route('/api/upload', methods=['POST'])
def upload_receipt():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file'}), 400
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file'}), 400
    
    filename = secure_filename(file.filename)
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(temp_path)
    
    result = analyze_receipt_with_azure(temp_path)
    
    if result['success']:
        receipt_filename = f"{uuid.uuid4().hex}.{filename.rsplit('.', 1)[1].lower()}"
        shutil.move(temp_path, os.path.join(app.config['RECEIPT_FOLDER'], receipt_filename))
        result['receipt_image'] = receipt_filename
    else:
        os.remove(temp_path)
    
    return jsonify(result)

@app.route('/api/save-items', methods=['POST'])
def save_items():
    data = request.json
    items = data.get('items', [])
    store, date = data.get('store', 'Unknown'), data.get('date', datetime.now().strftime('%Y-%m-%d'))
    person = data.get('person', get_current_person())
    bank = data.get('bank_account', 'Unknown')
    receipt_image = data.get('receipt_image', '')
    group_id = data.get('group_id', '')
    paid_by = data.get('paid_by', person)
    splits = data.get('splits', [])
    
    transaction_ids = []
    for item in items:
        tid = str(get_next_id('transactions'))
        write_csv_row('transactions', {
            'id': tid,
            'item_name': item.get('name', 'Unknown'),
            'category': item.get('category', 'Other'),
            'store': store, 'date': date, 'price': item.get('price', 0),
            'person': person, 'bank_account': bank, 'type': 'expense',
            'receipt_image': receipt_image, 'group_id': group_id, 'paid_by': paid_by
        })
        transaction_ids.append(tid)
        
        # Save splits if provided
        if splits:
            for split in splits:
                write_csv_row('splits', {
                    'id': str(get_next_id('splits')),
                    'transaction_id': tid,
                    'person': split['person'],
                    'amount': split['amount'],
                    'percentage': split.get('percentage', 0)
                })
    
    return jsonify({'success': True, 'saved': len(items)})

@app.route('/api/manual-entry', methods=['POST'])
def manual_entry():
    data = request.json
    person = data.get('person', get_current_person())
    tid = str(get_next_id('transactions'))
    
    transaction = {
        'id': tid,
        'item_name': data.get('item_name', 'Unknown'),
        'category': data.get('category', 'Other'),
        'store': data.get('store', 'Unknown'),
        'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
        'price': data.get('price', 0),
        'person': person,
        'bank_account': data.get('bank_account', 'Unknown'),
        'type': data.get('type', 'expense'),
        'receipt_image': '',
        'group_id': data.get('group_id', ''),
        'paid_by': data.get('paid_by', person)
    }
    write_csv_row('transactions', transaction)
    
    # Save splits
    splits = data.get('splits', [])
    for split in splits:
        write_csv_row('splits', {
            'id': str(get_next_id('splits')),
            'transaction_id': tid,
            'person': split['person'],
            'amount': split['amount'],
            'percentage': split.get('percentage', 0)
        })
    
    return jsonify({'success': True, 'transaction': transaction})

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    person = get_current_person()
    transactions = filter_by_person_access(read_csv('transactions'), person)
    
    # Apply filters
    cat, store = request.args.get('category'), request.args.get('store')
    acc, start, end = request.args.get('bank_account'), request.args.get('start_date'), request.args.get('end_date')
    q, t_type = request.args.get('q'), request.args.get('type')
    filter_person = request.args.get('person')
    
    if cat: transactions = [t for t in transactions if t['category'].lower() == cat.lower()]
    if store: transactions = [t for t in transactions if store.lower() in t['store'].lower()]
    if filter_person: transactions = [t for t in transactions if t['person'].lower() == filter_person.lower()]
    if acc: transactions = [t for t in transactions if t['bank_account'].lower() == acc.lower()]
    if start: transactions = [t for t in transactions if t['date'] >= start]
    if end: transactions = [t for t in transactions if t['date'] <= end]
    if q: transactions = [t for t in transactions if q.lower() in t['item_name'].lower() or q.lower() in t['store'].lower()]
    if t_type: transactions = [t for t in transactions if t.get('type', 'expense') == t_type]
    
    return jsonify(transactions)

@app.route('/api/transaction/<int:tid>')
def get_transaction(tid):
    transactions = read_csv('transactions')
    splits = read_csv('splits')
    
    for t in transactions:
        if int(t['id']) == tid:
            t['splits'] = [s for s in splits if s['transaction_id'] == str(tid)]
            return jsonify(t)
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/dashboard-data')
def get_dashboard_data():
    person = get_current_person()
    filter_person = request.args.get('person', person)
    
    transactions = filter_by_person_access(read_csv('transactions'), person)
    budgets = [b for b in read_csv('budgets') if b.get('person') == filter_person]
    splits = read_csv('splits')
    
    # Calculate actual amounts owed based on splits
    now = datetime.now()
    current_month = now.strftime('%Y-%m')
    
    monthly_spending, monthly_income = {}, {}
    for i in range(6):
        m = (now - timedelta(days=30*i)).strftime('%Y-%m')
        monthly_spending[m] = 0
        monthly_income[m] = 0
    
    category_spending, account_spending = {}, {}
    total_income, total_expenses = 0, 0
    month_income, month_expenses = 0, 0
    
    for t in transactions:
        # Calculate this person's share
        t_splits = [s for s in splits if s['transaction_id'] == t['id']]
        if t_splits:
            # Find this person's split
            person_split = next((s for s in t_splits if s['person'] == filter_person), None)
            if not person_split:
                continue
            price = float(person_split['amount'])
        else:
            # No splits, use full amount if they're the person
            if t.get('person') != filter_person and t.get('paid_by') != filter_person:
                continue
            price = float(t.get('price', 0))
        
        month = t['date'][:7]
        is_income = t.get('type', 'expense') == 'income'
        
        if is_income:
            total_income += price
            if month in monthly_income: monthly_income[month] += price
            if month == current_month: month_income += price
        else:
            total_expenses += price
            if month in monthly_spending: monthly_spending[month] += price
            if month == current_month: month_expenses += price
            cat = t.get('category', 'Other')
            category_spending[cat] = category_spending.get(cat, 0) + price
            acc = t.get('bank_account', 'Unknown')
            account_spending[acc] = account_spending.get(acc, 0) + price
    
    sorted_months = sorted(monthly_spending.keys())
    
    # Budget status
    budget_status = []
    for b in budgets:
        spent = category_spending.get(b['category'], 0)
        limit = float(b['amount'])
        budget_status.append({
            'category': b['category'], 'limit': limit, 'spent': spent,
            'remaining': limit - spent, 'percentage': min((spent / limit * 100) if limit else 0, 100)
        })
    
    return jsonify({
        'monthly_labels': sorted_months,
        'monthly_spending': [monthly_spending[m] for m in sorted_months],
        'monthly_income': [monthly_income[m] for m in sorted_months],
        'category_labels': list(category_spending.keys()),
        'category_values': list(category_spending.values()),
        'account_labels': list(account_spending.keys()),
        'account_values': list(account_spending.values()),
        'total_income': total_income, 'total_expenses': total_expenses,
        'current_month_income': month_income, 'current_month_expenses': month_expenses,
        'balance': total_income - total_expenses, 'budget_status': budget_status
    })

@app.route('/api/categories')
def get_categories():
    return jsonify(CATEGORIES)

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    person = get_current_person()
    accounts = filter_by_person_access(read_csv('accounts'), person)
    return jsonify(accounts)

@app.route('/api/accounts', methods=['POST'])
def add_account():
    data = request.json
    person = data.get('person', get_current_person())
    account = {
        'id': str(get_next_id('accounts')),
        'name': data.get('name'),
        'type': data.get('type', 'checking'),
        'person': person
    }
    write_csv_row('accounts', account)
    return jsonify({'success': True, 'account': account})

@app.route('/api/accounts/<int:aid>', methods=['PUT'])
def update_account(aid):
    accounts = read_csv('accounts')
    data = request.json
    for a in accounts:
        if int(a['id']) == aid:
            a['name'] = data.get('name', a['name'])
            a['type'] = data.get('type', a['type'])
    rewrite_csv('accounts', accounts)
    return jsonify({'success': True})

@app.route('/api/accounts/<int:aid>', methods=['DELETE'])
def delete_account(aid):
    accounts = [a for a in read_csv('accounts') if int(a['id']) != aid]
    rewrite_csv('accounts', accounts)
    return jsonify({'success': True})

@app.route('/api/persons')
def get_persons():
    person = get_current_person()
    groups = get_person_groups(person)
    all_people = set([person])
    for g in groups:
        all_people.update(g['members'].split(','))
    return jsonify(sorted(all_people))

# Budget API
@app.route('/api/budgets', methods=['GET'])
def get_budgets():
    person = get_current_person()
    budgets = [b for b in read_csv('budgets') if b.get('person') == person]
    return jsonify(budgets)

@app.route('/api/budgets', methods=['POST'])
def add_budget():
    data = request.json
    person = get_current_person()
    budget = {
        'id': str(get_next_id('budgets')),
        'category': data.get('category'),
        'amount': data.get('amount'),
        'period': data.get('period', 'monthly'),
        'start_date': data.get('start_date', datetime.now().strftime('%Y-%m-%d')),
        'person': person
    }
    write_csv_row('budgets', budget)
    return jsonify({'success': True, 'budget': budget})

@app.route('/api/budgets/<int:bid>', methods=['DELETE'])
def delete_budget(bid):
    budgets = [b for b in read_csv('budgets') if int(b['id']) != bid]
    rewrite_csv('budgets', budgets)
    return jsonify({'success': True})

@app.route('/api/budgets/<int:bid>', methods=['PUT'])
def update_budget(bid):
    budgets = read_csv('budgets')
    data = request.json
    for b in budgets:
        if int(b['id']) == bid:
            b['category'] = data.get('category', b['category'])
            b['amount'] = data.get('amount', b['amount'])
            b['period'] = data.get('period', b['period'])
    rewrite_csv('budgets', budgets)
    return jsonify({'success': True})

# Recurring API
@app.route('/api/recurring', methods=['GET'])
def get_recurring():
    person = get_current_person()
    recurring = filter_by_person_access(read_csv('recurring'), person)
    return jsonify(recurring)

@app.route('/api/recurring', methods=['POST'])
def add_recurring():
    data = request.json
    person = data.get('person', get_current_person())
    recurring = {
        'id': str(get_next_id('recurring')),
        'item_name': data.get('item_name'),
        'category': data.get('category'),
        'store': data.get('store', ''),
        'price': data.get('price'),
        'person': person,
        'bank_account': data.get('bank_account', ''),
        'type': data.get('type', 'expense'),
        'frequency': data.get('frequency', 'monthly'),
        'next_date': data.get('next_date'),
        'active': 'true',
        'group_id': data.get('group_id', '')
    }
    write_csv_row('recurring', recurring)
    return jsonify({'success': True, 'recurring': recurring})

@app.route('/api/recurring/<int:rid>', methods=['DELETE'])
def delete_recurring(rid):
    items = [r for r in read_csv('recurring') if int(r['id']) != rid]
    rewrite_csv('recurring', items)
    return jsonify({'success': True})

@app.route('/api/recurring/<int:rid>/toggle', methods=['POST'])
def toggle_recurring(rid):
    items = read_csv('recurring')
    for r in items:
        if int(r['id']) == rid:
            r['active'] = 'false' if r['active'] == 'true' else 'true'
    rewrite_csv('recurring', items)
    return jsonify({'success': True})

# Groups API
@app.route('/api/groups', methods=['GET'])
def get_groups():
    person = get_current_person()
    return jsonify(get_person_groups(person))

@app.route('/api/groups', methods=['POST'])
def add_group():
    data = request.json
    person = get_current_person()
    members = data.get('members', [])
    if person not in members:
        members.append(person)
    
    group = {
        'id': str(get_next_id('groups')),
        'name': data.get('name'),
        'members': ','.join(members)
    }
    write_csv_row('groups', group)
    return jsonify({'success': True, 'group': group})

@app.route('/api/groups/<int:gid>', methods=['PUT'])
def update_group(gid):
    groups = read_csv('groups')
    data = request.json
    for g in groups:
        if int(g['id']) == gid:
            g['name'] = data.get('name', g['name'])
            g['members'] = ','.join(data.get('members', g['members'].split(',')))
    rewrite_csv('groups', groups)
    return jsonify({'success': True})

@app.route('/api/groups/<int:gid>', methods=['DELETE'])
def delete_group(gid):
    groups = [g for g in read_csv('groups') if int(g['id']) != gid]
    rewrite_csv('groups', groups)
    return jsonify({'success': True})

# Splits API
@app.route('/api/splits/<int:tid>')
def get_splits(tid):
    splits = [s for s in read_csv('splits') if s['transaction_id'] == str(tid)]
    return jsonify(splits)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)