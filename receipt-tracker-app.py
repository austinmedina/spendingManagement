"""
Receipt Tracker Web Application
Flask backend with Azure Document Intelligence integration
"""

import os
import csv
import json
import uuid
import shutil
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RECEIPT_FOLDER'] = 'receipts'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'pdf'}

# Allowed categories
CATEGORIES = [
    'Rent', 'Electric', 'Investment', 'Car', 'Medical', 'Groceries',
    'Entertainment', 'Subscriptions', 'Household', 'Eating Out', 'Shopping', 'Other'
]
INCOME_CATEGORIES = ['Salary', 'Freelance', 'Investment', 'Gift', 'Refund', 'Other']

# Database configuration
USE_CSV = os.getenv('USE_CSV', 'true').lower() == 'true'
CSV_FILE = 'database.csv'
BUDGETS_FILE = 'budgets.csv'
RECURRING_FILE = 'recurring.csv'

# Azure Document Intelligence
AZURE_ENDPOINT = os.getenv('AZURE_DOC_INTELLIGENCE_ENDPOINT', '')
AZURE_KEY = os.getenv('AZURE_DOC_INTELLIGENCE_KEY', '')

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RECEIPT_FOLDER'], exist_ok=True)

# CSV Headers
CSV_HEADERS = ['id', 'item_name', 'category', 'store', 'date', 'price', 'person', 'bank_account', 'type', 'receipt_image']
BUDGET_HEADERS = ['id', 'category', 'amount', 'period', 'start_date']
RECURRING_HEADERS = ['id', 'item_name', 'category', 'store', 'price', 'person', 'bank_account', 'type', 'frequency', 'next_date', 'active']

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            sample = [
                {'id': '1', 'item_name': 'Weekly Groceries', 'category': 'Groceries', 'store': 'Walmart', 'date': '2025-01-15', 'price': '145.99', 'person': 'John', 'bank_account': 'Chase Checking', 'type': 'expense', 'receipt_image': ''},
                {'id': '2', 'item_name': 'Gas', 'category': 'Car', 'store': 'Shell', 'date': '2025-01-14', 'price': '55.00', 'person': 'John', 'bank_account': 'Chase Checking', 'type': 'expense', 'receipt_image': ''},
                {'id': '3', 'item_name': 'Salary', 'category': 'Salary', 'store': 'Employer', 'date': '2025-01-01', 'price': '3500.00', 'person': 'John', 'bank_account': 'Chase Checking', 'type': 'income', 'receipt_image': ''},
                {'id': '4', 'item_name': 'Netflix', 'category': 'Subscriptions', 'store': 'Netflix', 'date': '2025-01-10', 'price': '15.99', 'person': 'John', 'bank_account': 'Visa Credit', 'type': 'expense', 'receipt_image': ''},
                {'id': '5', 'item_name': 'Electric Bill', 'category': 'Electric', 'store': 'Power Co', 'date': '2025-01-05', 'price': '120.00', 'person': 'John', 'bank_account': 'Chase Checking', 'type': 'expense', 'receipt_image': ''},
                {'id': '6', 'item_name': 'Rent', 'category': 'Rent', 'store': 'Landlord', 'date': '2025-01-01', 'price': '1200.00', 'person': 'John', 'bank_account': 'Chase Checking', 'type': 'expense', 'receipt_image': ''},
            ]
            for row in sample:
                writer.writerow(row)
    
    if not os.path.exists(BUDGETS_FILE):
        with open(BUDGETS_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=BUDGET_HEADERS)
            writer.writeheader()
            sample_budgets = [
                {'id': '1', 'category': 'Groceries', 'amount': '400', 'period': 'monthly', 'start_date': '2025-01-01'},
                {'id': '2', 'category': 'Entertainment', 'amount': '100', 'period': 'monthly', 'start_date': '2025-01-01'},
                {'id': '3', 'category': 'Eating Out', 'amount': '150', 'period': 'monthly', 'start_date': '2025-01-01'},
            ]
            for row in sample_budgets:
                writer.writerow(row)
    
    if not os.path.exists(RECURRING_FILE):
        with open(RECURRING_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=RECURRING_HEADERS)
            writer.writeheader()
            sample_recurring = [
                {'id': '1', 'item_name': 'Netflix', 'category': 'Subscriptions', 'store': 'Netflix', 'price': '15.99', 'person': 'John', 'bank_account': 'Visa Credit', 'type': 'expense', 'frequency': 'monthly', 'next_date': '2025-02-10', 'active': 'true'},
                {'id': '2', 'item_name': 'Rent', 'category': 'Rent', 'store': 'Landlord', 'price': '1200.00', 'person': 'John', 'bank_account': 'Chase Checking', 'type': 'expense', 'frequency': 'monthly', 'next_date': '2025-02-01', 'active': 'true'},
                {'id': '3', 'item_name': 'Salary', 'category': 'Salary', 'store': 'Employer', 'price': '3500.00', 'person': 'John', 'bank_account': 'Chase Checking', 'type': 'income', 'frequency': 'biweekly', 'next_date': '2025-01-15', 'active': 'true'},
            ]
            for row in sample_recurring:
                writer.writerow(row)

init_csv()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_next_id(filename, headers):
    items = read_csv(filename, headers)
    if not items:
        return 1
    return max(int(t['id']) for t in items) + 1

def read_csv(filename, headers):
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

def write_csv_row(filename, headers, row):
    with open(filename, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writerow(row)

def rewrite_csv(filename, headers, rows):
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def read_all_transactions():
    return read_csv(CSV_FILE, CSV_HEADERS)

def write_transaction(transaction):
    write_csv_row(CSV_FILE, CSV_HEADERS, transaction)

def save_receipt_image(file):
    """Save receipt image and return filename"""
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
    """Check and create transactions for due recurring items"""
    recurring = read_csv(RECURRING_FILE, RECURRING_HEADERS)
    today = datetime.now().date()
    updated = False
    
    for item in recurring:
        if item['active'] != 'true':
            continue
        next_date = datetime.strptime(item['next_date'], '%Y-%m-%d').date()
        while next_date <= today:
            transaction = {
                'id': get_next_id(CSV_FILE, CSV_HEADERS),
                'item_name': item['item_name'],
                'category': item['category'],
                'store': item['store'],
                'date': next_date.strftime('%Y-%m-%d'),
                'price': item['price'],
                'person': item['person'],
                'bank_account': item['bank_account'],
                'type': item['type'],
                'receipt_image': ''
            }
            write_transaction(transaction)
            
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
        rewrite_csv(RECURRING_FILE, RECURRING_HEADERS, recurring)

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
    return render_template('dashboard.html', categories=CATEGORIES)

@app.route('/upload')
def upload_page():
    return render_template('upload.html', categories=CATEGORIES)

@app.route('/search')
def search_page():
    return render_template('search.html', categories=CATEGORIES)

@app.route('/manual')
def manual_page():
    return render_template('manual.html', categories=CATEGORIES, income_categories=INCOME_CATEGORIES)

@app.route('/budgets')
def budgets_page():
    return render_template('budgets.html', categories=CATEGORIES)

@app.route('/recurring')
def recurring_page():
    return render_template('recurring.html', categories=CATEGORIES, income_categories=INCOME_CATEGORIES)

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
    person, bank = data.get('person', 'Unknown'), data.get('bank_account', 'Unknown')
    receipt_image = data.get('receipt_image', '')
    
    for item in items:
        write_transaction({
            'id': get_next_id(CSV_FILE, CSV_HEADERS),
            'item_name': item.get('name', 'Unknown'),
            'category': item.get('category', 'Other'),
            'store': store, 'date': date, 'price': item.get('price', 0),
            'person': person, 'bank_account': bank, 'type': 'expense',
            'receipt_image': receipt_image
        })
    return jsonify({'success': True, 'saved': len(items)})

@app.route('/api/manual-entry', methods=['POST'])
def manual_entry():
    data = request.json
    transaction = {
        'id': get_next_id(CSV_FILE, CSV_HEADERS),
        'item_name': data.get('item_name', 'Unknown'),
        'category': data.get('category', 'Other'),
        'store': data.get('store', 'Unknown'),
        'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
        'price': data.get('price', 0),
        'person': data.get('person', 'Unknown'),
        'bank_account': data.get('bank_account', 'Unknown'),
        'type': data.get('type', 'expense'),
        'receipt_image': ''
    }
    write_transaction(transaction)
    return jsonify({'success': True, 'transaction': transaction})

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    transactions = read_all_transactions()
    cat, store, person = request.args.get('category'), request.args.get('store'), request.args.get('person')
    bank, start, end = request.args.get('bank_account'), request.args.get('start_date'), request.args.get('end_date')
    q, t_type = request.args.get('q'), request.args.get('type')
    
    if cat: transactions = [t for t in transactions if t['category'].lower() == cat.lower()]
    if store: transactions = [t for t in transactions if store.lower() in t['store'].lower()]
    if person: transactions = [t for t in transactions if t['person'].lower() == person.lower()]
    if bank: transactions = [t for t in transactions if t['bank_account'].lower() == bank.lower()]
    if start: transactions = [t for t in transactions if t['date'] >= start]
    if end: transactions = [t for t in transactions if t['date'] <= end]
    if q: transactions = [t for t in transactions if q.lower() in t['item_name'].lower() or q.lower() in t['store'].lower()]
    if t_type: transactions = [t for t in transactions if t.get('type', 'expense') == t_type]
    
    return jsonify(transactions)

@app.route('/api/transaction/<int:tid>')
def get_transaction(tid):
    transactions = read_all_transactions()
    for t in transactions:
        if int(t['id']) == tid:
            return jsonify(t)
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/dashboard-data')
def get_dashboard_data():
    transactions = read_all_transactions()
    budgets = read_csv(BUDGETS_FILE, BUDGET_HEADERS)
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
        price, month = float(t.get('price', 0)), t['date'][:7]
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

@app.route('/api/accounts')
def get_accounts():
    return jsonify(sorted(set(t['bank_account'] for t in read_all_transactions())))

@app.route('/api/persons')
def get_persons():
    return jsonify(sorted(set(t['person'] for t in read_all_transactions())))

# Budget API
@app.route('/api/budgets', methods=['GET'])
def get_budgets():
    return jsonify(read_csv(BUDGETS_FILE, BUDGET_HEADERS))

@app.route('/api/budgets', methods=['POST'])
def add_budget():
    data = request.json
    budget = {
        'id': get_next_id(BUDGETS_FILE, BUDGET_HEADERS),
        'category': data.get('category'), 'amount': data.get('amount'),
        'period': data.get('period', 'monthly'),
        'start_date': data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
    }
    write_csv_row(BUDGETS_FILE, BUDGET_HEADERS, budget)
    return jsonify({'success': True, 'budget': budget})

@app.route('/api/budgets/<int:bid>', methods=['DELETE'])
def delete_budget(bid):
    budgets = [b for b in read_csv(BUDGETS_FILE, BUDGET_HEADERS) if int(b['id']) != bid]
    rewrite_csv(BUDGETS_FILE, BUDGET_HEADERS, budgets)
    return jsonify({'success': True})

@app.route('/api/budgets/<int:bid>', methods=['PUT'])
def update_budget(bid):
    budgets = read_csv(BUDGETS_FILE, BUDGET_HEADERS)
    data = request.json
    for b in budgets:
        if int(b['id']) == bid:
            b['category'] = data.get('category', b['category'])
            b['amount'] = data.get('amount', b['amount'])
            b['period'] = data.get('period', b['period'])
    rewrite_csv(BUDGETS_FILE, BUDGET_HEADERS, budgets)
    return jsonify({'success': True})

# Recurring API
@app.route('/api/recurring', methods=['GET'])
def get_recurring():
    return jsonify(read_csv(RECURRING_FILE, RECURRING_HEADERS))

@app.route('/api/recurring', methods=['POST'])
def add_recurring():
    data = request.json
    recurring = {
        'id': get_next_id(RECURRING_FILE, RECURRING_HEADERS),
        'item_name': data.get('item_name'), 'category': data.get('category'),
        'store': data.get('store', ''), 'price': data.get('price'),
        'person': data.get('person', ''), 'bank_account': data.get('bank_account', ''),
        'type': data.get('type', 'expense'), 'frequency': data.get('frequency', 'monthly'),
        'next_date': data.get('next_date'), 'active': 'true'
    }
    write_csv_row(RECURRING_FILE, RECURRING_HEADERS, recurring)
    return jsonify({'success': True, 'recurring': recurring})

@app.route('/api/recurring/<int:rid>', methods=['DELETE'])
def delete_recurring(rid):
    items = [r for r in read_csv(RECURRING_FILE, RECURRING_HEADERS) if int(r['id']) != rid]
    rewrite_csv(RECURRING_FILE, RECURRING_HEADERS, items)
    return jsonify({'success': True})

@app.route('/api/recurring/<int:rid>/toggle', methods=['POST'])
def toggle_recurring(rid):
    items = read_csv(RECURRING_FILE, RECURRING_HEADERS)
    for r in items:
        if int(r['id']) == rid:
            r['active'] = 'false' if r['active'] == 'true' else 'true'
    rewrite_csv(RECURRING_FILE, RECURRING_HEADERS, items)
    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
