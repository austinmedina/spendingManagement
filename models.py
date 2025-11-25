"""
Data models and CSV operations for Receipt Tracker
Handles all data persistence operations
"""

import os
import csv
from typing import List, Dict, Optional
from config import Config

class CSVModel:
    """Base class for CSV operations"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.filename = Config.CSV_FILES[table_name]
        self.headers = Config.CSV_HEADERS[table_name]
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Ensure CSV file exists with headers"""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                writer.writeheader()
    
    def read_all(self) -> List[Dict]:
        """Read all rows from CSV"""
        items = []
        try:
            with open(self.filename, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    items.append(row)
        except FileNotFoundError:
            self._ensure_file_exists()
        return items
    
    def write_row(self, row: Dict):
        """Append a single row to CSV"""
        with open(self.filename, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writerow(row)
    
    def rewrite_all(self, rows: List[Dict]):
        """Rewrite entire CSV file"""
        with open(self.filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
    
    def get_next_id(self) -> int:
        """Get next available ID"""
        items = self.read_all()
        if not items:
            return 1
        return max(int(t['id']) for t in items) + 1
    
    def find_by_id(self, item_id: int) -> Optional[Dict]:
        """Find item by ID"""
        items = self.read_all()
        for item in items:
            if int(item['id']) == item_id:
                return item
        return None
    
    def delete_by_id(self, item_id: int) -> bool:
        """Delete item by ID"""
        items = self.read_all()
        filtered = [item for item in items if int(item['id']) != item_id]
        if len(filtered) < len(items):
            self.rewrite_all(filtered)
            return True
        return False
    
    def update_by_id(self, item_id: int, updates: Dict) -> bool:
        """Update item by ID"""
        items = self.read_all()
        found = False
        for item in items:
            if int(item['id']) == item_id:
                item.update(updates)
                found = True
                break
        if found:
            self.rewrite_all(items)
        return found


class TransactionModel(CSVModel):
    """Transaction operations"""
    
    def __init__(self):
        super().__init__('transactions')
    
    def create(self, data: Dict) -> Dict:
        """Create new transaction"""
        transaction = {
            'id': str(self.get_next_id()),
            'item_name': data.get('item_name', 'Unknown'),
            'category': data.get('category', 'Other'),
            'store': data.get('store', ''),
            'date': data.get('date'),
            'price': str(data.get('price', 0)),
            'person': data.get('person', ''),
            'bank_account': data.get('bank_account', ''),
            'type': data.get('type', 'expense'),
            'receipt_image': data.get('receipt_image', ''),
            'group_id': data.get('group_id', ''),
            'receipt_group_id': data.get('receipt_group_id', '')
        }
        self.write_row(transaction)
        return transaction
    
    def filter(self, filters: Dict) -> List[Dict]:
        """Filter transactions"""
        transactions = self.read_all()
        
        if filters.get('category'):
            transactions = [t for t in transactions 
                          if t['category'].lower() == filters['category'].lower()]
        
        if filters.get('store'):
            transactions = [t for t in transactions 
                          if filters['store'].lower() in t['store'].lower()]
        
        if filters.get('person'):
            transactions = [t for t in transactions 
                          if t['person'].lower() == filters['person'].lower()]
        
        if filters.get('bank_account'):
            transactions = [t for t in transactions 
                          if t['bank_account'].lower() == filters['bank_account'].lower()]
        
        if filters.get('start_date'):
            transactions = [t for t in transactions 
                          if t['date'] >= filters['start_date']]
        
        if filters.get('end_date'):
            transactions = [t for t in transactions 
                          if t['date'] <= filters['end_date']]
        
        if filters.get('q'):
            q = filters['q'].lower()
            transactions = [t for t in transactions 
                          if q in t['item_name'].lower() or q in t['store'].lower()]
        
        if filters.get('type'):
            transactions = [t for t in transactions 
                          if t.get('type', 'expense') == filters['type']]
        
        return transactions


class BudgetModel(CSVModel):
    """Budget operations"""
    
    def __init__(self):
        super().__init__('budgets')
    
    def create(self, data: Dict) -> Dict:
        """Create new budget"""
        budget = {
            'id': str(self.get_next_id()),
            'category': data.get('category'),
            'amount': str(data.get('amount')),
            'period': data.get('period', 'monthly'),
            'start_date': data.get('start_date'),
            'person': data.get('person')
        }
        self.write_row(budget)
        return budget
    
    def get_by_person(self, person: str) -> List[Dict]:
        """Get budgets for a specific person"""
        budgets = self.read_all()
        return [b for b in budgets if b.get('person') == person]


class RecurringModel(CSVModel):
    """Recurring transaction operations"""
    
    def __init__(self):
        super().__init__('recurring')
    
    def create(self, data: Dict) -> Dict:
        """Create new recurring transaction"""
        recurring = {
            'id': str(self.get_next_id()),
            'item_name': data.get('item_name'),
            'category': data.get('category', 'Other'),
            'store': data.get('store', ''),
            'price': str(data.get('price')),
            'person': data.get('person', ''),
            'bank_account': data.get('bank_account', ''),
            'type': data.get('type', 'expense'),
            'frequency': data.get('frequency', 'monthly'),
            'next_date': data.get('next_date'),
            'active': 'true',
            'group_id': data.get('group_id', '')
        }
        self.write_row(recurring)
        return recurring
    
    def toggle(self, item_id: int) -> bool:
        """Toggle active status"""
        items = self.read_all()
        for item in items:
            if int(item['id']) == item_id:
                item['active'] = 'false' if item['active'] == 'true' else 'true'
                self.rewrite_all(items)
                return True
        return False
    
    def get_active(self) -> List[Dict]:
        """Get all active recurring transactions"""
        items = self.read_all()
        return [item for item in items if item['active'] == 'true']


class AccountModel(CSVModel):
    """Account operations"""
    
    def __init__(self):
        super().__init__('accounts')
    
    def create(self, data: Dict) -> Dict:
        """Create new account"""
        account = {
            'id': str(self.get_next_id()),
            'name': data.get('name'),
            'type': data.get('type', 'checking'),
            'person': data.get('person')
        }
        self.write_row(account)
        return account
    
    def get_by_person(self, person: str) -> List[Dict]:
        """Get accounts for a specific person"""
        accounts = self.read_all()
        return [a for a in accounts if a.get('person') == person]


class GroupModel(CSVModel):
    """Group operations"""
    
    def __init__(self):
        super().__init__('groups')
    
    def create(self, data: Dict) -> Dict:
        """Create new group"""
        members = data.get('members', [])
        if isinstance(members, list):
            members = ','.join(members)
        
        group = {
            'id': str(self.get_next_id()),
            'name': data.get('name'),
            'members': members
        }
        self.write_row(group)
        return group
    
    def get_by_member(self, person: str) -> List[Dict]:
        """Get all groups a person is a member of"""
        groups = self.read_all()
        return [g for g in groups if person in g['members'].split(',')]
    
    def get_members(self, group_id: int) -> List[str]:
        """Get members of a group"""
        group = self.find_by_id(group_id)
        if group:
            return group['members'].split(',')
        return []


class SplitModel(CSVModel):
    """Split operations"""
    
    def __init__(self):
        super().__init__('splits')
    
    def create(self, data: Dict) -> Dict:
        """Create new split"""
        split = {
            'id': str(self.get_next_id()),
            'receipt_group_id': data.get('receipt_group_id'),
            'person': data.get('person'),
            'amount': str(data.get('amount')),
            'percentage': str(data.get('percentage', 0))
        }
        self.write_row(split)
        return split
    
    def get_by_receipt_group(self, receipt_group_id: str) -> List[Dict]:
        """Get splits for a receipt group"""
        splits = self.read_all()
        return [s for s in splits if s['receipt_group_id'] == receipt_group_id]


class NotificationModel(CSVModel):
    """Notification operations"""
    
    def __init__(self):
        super().__init__('notifications')
    
    def create(self, data: Dict) -> Dict:
        """Create new notification"""
        notification = {
            'id': str(self.get_next_id()),
            'user': data.get('user'),
            'type': data.get('type', 'info'),
            'title': data.get('title'),
            'message': data.get('message'),
            'date': data.get('date'),
            'read': 'false',
            'data': data.get('data', '')
        }
        self.write_row(notification)
        return notification
    
    def get_by_user(self, user: str, unread_only: bool = False) -> List[Dict]:
        """Get notifications for a user"""
        notifications = self.read_all()
        user_notifications = [n for n in notifications if n['user'] == user]
        
        if unread_only:
            user_notifications = [n for n in user_notifications if n['read'] == 'false']
        
        # Sort by date descending
        user_notifications.sort(key=lambda x: x['date'], reverse=True)
        return user_notifications
    
    def mark_read(self, notification_id: int) -> bool:
        """Mark notification as read"""
        return self.update_by_id(notification_id, {'read': 'true'})
    
    def mark_all_read(self, user: str) -> int:
        """Mark all notifications as read for a user"""
        notifications = self.read_all()
        count = 0
        for notification in notifications:
            if notification['user'] == user and notification['read'] == 'false':
                notification['read'] = 'true'
                count += 1
        if count > 0:
            self.rewrite_all(notifications)
        return count
    
    def get_unread_count(self, user: str) -> int:
        """Get count of unread notifications"""
        notifications = self.get_by_user(user, unread_only=True)
        return len(notifications)