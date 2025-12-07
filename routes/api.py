"""
API endpoints for AJAX requests
Comprehensive REST API for frontend communication
"""

from flask import Blueprint, jsonify, request
from auth import login_required, get_current_user, admin_required, get_user_by_id, get_user_by_full_name
from models import (
    TransactionModel, BudgetModel, RecurringModel, 
    AccountModel, GroupModel, SplitModel, NotificationModel
)
from services.notification_service import notification_service
from services.analytics_service import analytics_service
from utils.helpers import filter_by_person_access, get_person_groups
from utils.decorators import api_response
from datetime import datetime, timedelta
import json

api_bp = Blueprint('api', __name__, url_prefix='/api')

# ==================== Dashboard ====================

@api_bp.route('/dashboard-data')
@login_required
# @api_response
def get_dashboard_data():
    """Get basic dashboard data (legacy endpoint)"""
    user = get_current_user()
    view_mode = request.args.get('view', 'personal')
    group_id = request.args.get('group_id', '')
    
    transaction_model = TransactionModel()
    budget_model = BudgetModel()
    split_model = SplitModel()
    
    # Get transactions based on view
    if view_mode == 'group' and group_id:
        transactions = [t for t in transaction_model.read_all() if t.get('group_id') == group_id]
    else:
        transactionAll = transaction_model.read_all()
        transactions = filter_by_person_access(transactionAll, user["id"])
        print("Got transactions")
    
    # Calculate basic stats
    now = datetime.now()
    current_month = now.strftime('%Y-%m')
    
    monthly_spending = {}
    monthly_income = {}
    for i in range(6):
        m = (now - timedelta(days=30*i)).strftime('%Y-%m')
        monthly_spending[m] = 0
        monthly_income[m] = 0
    
    category_spending = {}
    account_spending = {}
    total_income = 0
    total_expenses = 0
    month_income = 0
    month_expenses = 0
    
    splits = split_model.read_all()
    for t in transactions:
        # Handle splits
        receipt_group_id = t.get('receipt_group_id', '')
        if receipt_group_id:
            t_splits = [s for s in splits if s['receipt_group_id'] == receipt_group_id]
            if t_splits:
                person_split = next((s for s in t_splits if s['user_id'] == user["id"]), None)
                if not person_split:
                    continue
                total_receipt = sum(float(tr.get('price', 0)) for tr in transactions 
                                  if tr.get('receipt_group_id') == receipt_group_id)
                if total_receipt > 0:
                    split_ratio = float(person_split['amount']) / total_receipt
                    price = float(t.get('price', 0)) * split_ratio
                else:
                    price = 0
            else:
                price = float(t.get('price', 0))
        else:
            if t.get('user_id') != user["id"]:
                continue
            price = float(t.get('price', 0))
        
        month = t['date'][:7]
        is_income = t.get('type', 'expense') == 'income'
        
        if is_income:
            total_income += price
            if month in monthly_income:
                monthly_income[month] += price
            if month == current_month:
                month_income += price
        else:
            total_expenses += price
            if month in monthly_spending:
                monthly_spending[month] += price
            if month == current_month:
                month_expenses += price
            cat = t.get('category', 'Other')
            category_spending[cat] = category_spending.get(cat, 0) + price
            acc = t.get('bank_account_id', 'Unknown')
            account_spending[acc] = account_spending.get(acc, 0) + price
    
    sorted_months = sorted(monthly_spending.keys())
    # Budget status
    budgets = budget_model.get_by_user(user["id"])
    budget_status = []
    for b in budgets:
        spent = category_spending.get(b['category'], 0)
        limit = float(b['amount'])
        budget_status.append({
            'category': b['category'],
            'limit': limit,
            'spent': spent,
            'remaining': limit - spent,
            'percentage': min((spent / limit * 100) if limit else 0, 100)
        })

    
    
    return {
        'monthly_labels': sorted_months,
        'monthly_spending': [monthly_spending[m] for m in sorted_months],
        'monthly_income': [monthly_income[m] for m in sorted_months],
        'category_labels': list(category_spending.keys()),
        'category_values': list(category_spending.values()),
        'account_labels': list(account_spending.keys()),
        'account_values': list(account_spending.values()),
        'total_income': total_income,
        'total_expenses': total_expenses,
        'current_month_income': month_income,
        'current_month_expenses': month_expenses,
        'balance': total_income - total_expenses,
        'budget_status': budget_status
    }

@api_bp.route('/dashboard-enhanced')
@login_required
# @api_response
def get_dashboard_enhanced():
    """Get enhanced dashboard data with analytics"""
    person = json.loads(request.args.get("person"))
    view = request.args.get('view', 'personal')
    group_id = request.args.get('group_id', '')
    
    data = analytics_service.get_enhanced_dashboard_data(person["id"], group_id)
    return data

# ==================== Transactions ====================

@api_bp.route('/transactions')
@login_required
@api_response
def get_transactions():
    """Get filtered transactions"""
    user = get_current_user()
    
    transaction_model = TransactionModel()
    account_model = AccountModel()
    transactions = filter_by_person_access(transaction_model.read_all(), user["id"])
    for t in transactions:
        if t["receipt_group_id"]:
            splits = SplitModel().get_by_receipt_group(t["receipt_group_id"])
            for split in splits:
                if split["user_id"] == user["id"]:
                    t["price"] = split["amount"]
            
    # Apply filters
    filters = {}
    for key in ['category', 'store', 'bank_account_id', 'start_date', 'end_date', 'q', 'type', 'user_id']:
        if request.args.get(key):
            filters[key] = request.args.get(key)
    
    if filters:
        transactions = transaction_model.filter(filters)
        transactions = filter_by_person_access(transactions, user["id"])
    for t in transactions:
        name = get_user_by_id(t['user_id'])
        account = account_model.find_by_id(t['bank_account_id'])
        t['account_name'] = account['name'] if account else 'Unknown'
        t['full_name'] = name['full_name'] if name else 'Unknown'
    return transactions

@api_bp.route('/transaction/<int:tid>')
@login_required
@api_response
def get_transaction(tid):
    """Get single transaction with splits"""
    transaction_model = TransactionModel()
    split_model = SplitModel()
    
    transaction = transaction_model.find_by_id(tid)
    if not transaction:
        return {'error': 'Transaction not found'}, 404
    
    # Get splits
    receipt_group_id = transaction.get('receipt_group_id', '')
    if receipt_group_id:
        transaction['splits'] = split_model.get_by_receipt_group(receipt_group_id)
    else:
        transaction['splits'] = []
    
    return transaction

# ==================== Notifications ====================

@api_bp.route('/notifications')
@login_required
@api_response
def get_notifications():
    """Get user notifications"""
    user = get_current_user()
    notifications = notification_service.get_user_notifications(user["id"])
    return notifications

@api_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
@api_response
def mark_notification_read(notification_id):
    """Mark notification as read"""
    success = notification_service.mark_read(notification_id)
    return {'success': success}

@api_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
@api_response
def mark_all_notifications_read():
    """Mark all notifications as read"""
    user = get_current_user()
    count = notification_service.mark_all_read(user["id"])
    return {'success': True, 'count': count}

# ==================== Categories & Persons ====================

@api_bp.route('/categories')
@api_response
def get_categories():
    """Get all categories"""
    from config import Config
    return Config.EXPENSE_CATEGORIES

@api_bp.route('/persons')
@login_required
@api_response
def get_persons():
    """Get all persons"""
    user = get_current_user()
    
    # store final results here
    all_people = []
    seen_ids = set()
    
    # helper to add people without duplicates
    def add_person(p):
        if p["id"] not in seen_ids:
            all_people.append(p)
            seen_ids.add(p["id"])
    
    # add current user
    add_person({"id": user["id"], "full_name": user["full_name"]})
    
    groups = get_person_groups(user["id"])
    
    for g in groups:
        for member_id in g["members"].split(","):
            member = get_user_by_id(member_id)
            if member:
                add_person({"id": member["id"], "full_name": member["full_name"]})
    
    # sort however you want (e.g. by id)
    return sorted(all_people, key=lambda p: p["id"])

# ==================== Accounts ====================

@api_bp.route('/accounts')
@login_required
@api_response
def get_accounts():
    """Get user accounts"""
    user = get_current_user()
    account_model = AccountModel()
    accounts = account_model.get_by_user(user["id"])

    for a in accounts:
        user = get_user_by_id(a['user_id'])
        a['full_name'] = user['full_name'] if user else 'Unknown'

    return accounts

@api_bp.route('/accounts', methods=['POST'])
@login_required
@api_response
def create_account():
    """Create new account"""
    user = get_current_user()
    
    data = request.json
    data['user_id'] = user["id"]
    
    account_model = AccountModel()
    account = account_model.create(data)
    return {'success': True, 'account': account}

@api_bp.route('/accounts/<int:aid>', methods=['PUT'])
@login_required
@api_response
def update_account(aid):
    """Update account"""
    data = request.json
    account_model = AccountModel()
    success = account_model.update_by_id(aid, data)
    return {'success': success}

@api_bp.route('/accounts/<int:aid>', methods=['DELETE'])
@login_required
@api_response
def delete_account(aid):
    """Delete account"""
    account_model = AccountModel()
    success = account_model.delete_by_id(aid)
    return {'success': success}

# ==================== Budgets ====================

@api_bp.route('/budgets')
@login_required
@api_response
def get_budgets():
    """Get user budgets"""
    user = get_current_user()
    budget_model = BudgetModel()
    budgets = budget_model.get_by_user(user["id"])
    return budgets

@api_bp.route('/budgets', methods=['POST'])
@login_required
@api_response
def create_budget():
    """Create new budget"""
    user = get_current_user()
    
    data = request.json
    data['user_id'] = user["id"]
    data['start_date'] = datetime.now().strftime('%Y-%m-%d')
    
    budget_model = BudgetModel()
    budget = budget_model.create(data)
    return {'success': True, 'budget': budget}

@api_bp.route('/budgets/<int:bid>', methods=['PUT'])
@login_required
@api_response
def update_budget(bid):
    """Update budget"""
    data = request.json
    budget_model = BudgetModel()
    success = budget_model.update_by_id(bid, data)
    return {'success': success}

@api_bp.route('/budgets/<int:bid>', methods=['DELETE'])
@login_required
@api_response
def delete_budget(bid):
    """Delete budget"""
    budget_model = BudgetModel()
    success = budget_model.delete_by_id(bid)
    return {'success': success}

# ==================== Recurring ====================

@api_bp.route('/recurring')
@login_required
@api_response
def get_recurring():
    """Get recurring transactions"""
    user = get_current_user()
    recurring_model = RecurringModel()
    recurring = filter_by_person_access(recurring_model.read_all(), user["id"])
    return recurring

@api_bp.route('/recurring', methods=['POST'])
@login_required
@api_response
def create_recurring():
    """Create recurring transaction"""
    data = request.json
    if not data.get('user_id'):
        user = get_current_user()
        data['user_id'] = user['id']
    
    recurring_model = RecurringModel()
    recurring = recurring_model.create(data)
    return {'success': True, 'recurring': recurring}

@api_bp.route('/recurring/<int:rid>', methods=['DELETE'])
@login_required
@api_response
def delete_recurring(rid):
    """Delete recurring transaction"""
    recurring_model = RecurringModel()
    success = recurring_model.delete_by_id(rid)
    return {'success': success}

@api_bp.route('/recurring/<int:rid>/toggle', methods=['POST'])
@login_required
@api_response
def toggle_recurring(rid):
    """Toggle recurring transaction active status"""
    recurring_model = RecurringModel()
    success = recurring_model.toggle(rid)
    return {'success': success}

# ==================== Groups ====================

@api_bp.route('/groups')
@login_required
@api_response
def get_groups():
    """Get user groups"""
    user = get_current_user()
    person = user['id']
    groups = get_person_groups(person)
    groupMembers = []
    for group in groups:
        modifiedGroup = group
        names = []
        for id in group["members"].split(','):
            names.append(get_user_by_id(id)["full_name"])
        
        modifiedGroup["names"] = names
        groupMembers.append(modifiedGroup)
            
    return groupMembers

@api_bp.route('/groups', methods=['POST'])
@login_required
@api_response
def create_group():
    """Create new group"""
    data = request.json
    user = get_current_user()
    person = user["id"]
    
    members = data.get('members', [])
    if person not in members:
        members.append(person)
    data['members'] = members
    
    group_model = GroupModel()
    group = group_model.create(data)
    return {'success': True, 'group': group}

@api_bp.route('/groups/<int:gid>', methods=['PUT'])
@login_required
@api_response
def update_group(gid):
    """Update group"""
    data = request.json
    user = get_current_user()
    person = user["id"]

    members = []
    membersNames = data.get('members', [])
    for name in membersNames:
        members.append(get_user_by_full_name(name)["id"])
    
    if person not in members:
        members.append(person)
    data['members'] = ','.join(members)

    group_model = GroupModel()
    success = group_model.update_by_id(gid, data)
    return {'success': success}

@api_bp.route('/groups/<int:gid>', methods=['DELETE'])
@login_required
@api_response
def delete_group(gid):
    """Delete group"""
    group_model = GroupModel()
    success = group_model.delete_by_id(gid)
    return {'success': success}

# ==================== Splits ====================

@api_bp.route('/splits/<int:tid>')
@login_required
@api_response
def get_splits(tid):
    """Get splits for a transaction"""
    split_model = SplitModel()
    transaction_model = TransactionModel()
    
    transaction = transaction_model.find_by_id(tid)
    if not transaction:
        return {'error': 'Transaction not found'}, 404
    
    receipt_group_id = transaction.get('receipt_group_id', '')
    if receipt_group_id:
        splits = split_model.get_by_receipt_group(receipt_group_id)
        return splits
    
    return []

# ==================== Admin APIs ====================

@api_bp.route('/admin/users')
@admin_required
@api_response
def get_all_users():
    """Get all users (admin only)"""
    from auth import read_users
    users = read_users()
    # Remove password hashes
    for user in users:
        user.pop('password_hash', None)
    return users

@api_bp.route('/admin/users', methods=['POST'])
@admin_required
@api_response
def create_new_user():
    """Create new user (admin only)"""
    from auth import create_user
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    full_name = data.get('full_name')
    email = data.get('email')
    is_admin_user = data.get('is_admin', False)
    
    if not username or not password or not full_name or not email:
        return {'success': False, 'error': 'Missing required fields'}, 400
    
    user = create_user(username, password, full_name, email, is_admin_user)
    if not user:
        return {'success': False, 'error': 'Username or email already exists'}, 400
    
    user.pop('password_hash', None)
    return {'success': True, 'user': user}

@api_bp.route('/admin/users/<int:uid>', methods=['PUT'])
@admin_required
@api_response
def update_user_admin(uid):
    """Update user (admin only)"""
    from auth import update_user
    data = request.json
    update_user(uid, data)
    return {'success': True}

@api_bp.route('/admin/users/<int:uid>', methods=['DELETE'])
@admin_required
@api_response
def deactivate_user(uid):
    """Deactivate user (admin only)"""
    from flask import session
    from auth import delete_user
    
    if int(uid) == int(session['user_id']):
        return {'success': False, 'error': 'Cannot delete your own account'}, 400
    
    delete_user(uid)
    return {'success': True}

@api_bp.route('/admin/groups/assign', methods=['POST'])
@admin_required
@api_response
def admin_assign_group():
    """Assign users to groups (admin only)"""
    data = request.json
    group_id = data.get('group_id')
    members = data.get('members', [])
    
    group_model = GroupModel()
    success = group_model.update_by_id(int(group_id), {
        'members': ','.join(members)
    })
    
    return {'success': success}