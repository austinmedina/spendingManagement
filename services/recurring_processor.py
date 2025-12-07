"""
Recurring Transaction Processor
Handles automatic generation of recurring transactions
"""

from datetime import datetime, timedelta
from models import RecurringModel, TransactionModel

def process_recurring_transactions():
    """Process all active recurring transactions and generate new transactions"""
    recurring_model = RecurringModel()
    transaction_model = TransactionModel()
    
    recurring_items = recurring_model.get_active()
    today = datetime.now().date()
    updated = False
    
    for item in recurring_items:
        next_date = datetime.strptime(item['next_date'], '%Y-%m-%d').date()
        
        # Process all overdue recurring transactions
        while next_date <= today:
            # Create transaction
            transaction_model.create({
                'item_name': item['item_name'],
                'category': item['category'],
                'store': item['store'],
                'date': next_date.strftime('%Y-%m-%d'),
                'price': item['price'],
                'user_id': item.get('user_id'),
                'bank_account_id': item.get('bank_account_id'),
                'type': item['type'],
                'receipt_image': '',
                'group_id': item.get('group_id', '')
            })
            
            # Calculate next date based on frequency
            if item['frequency'] == 'daily':
                next_date += timedelta(days=1)
            elif item['frequency'] == 'weekly':
                next_date += timedelta(weeks=1)
            elif item['frequency'] == 'biweekly':
                next_date += timedelta(weeks=2)
            elif item['frequency'] == 'monthly':
                # Handle month increment properly
                month = next_date.month
                year = next_date.year
                
                if month == 12:
                    month = 1
                    year += 1
                else:
                    month += 1
                
                # Handle day overflow (e.g., Jan 31 -> Feb 28)
                day = min(next_date.day, [31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
                next_date = next_date.replace(year=year, month=month, day=day)
            
            elif item['frequency'] == 'yearly':
                next_date = next_date.replace(year=next_date.year + 1)
            
            # Update next date
            recurring_model.update_by_id(int(item['id']), {
                'next_date': next_date.strftime('%Y-%m-%d')
            })
            updated = True
    
    return updated