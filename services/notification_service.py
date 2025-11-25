"""
Notification and Reminder Service
Handles budget alerts, recurring transaction reminders, and notifications
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict
from config import Config
from models import NotificationModel, BudgetModel, RecurringModel, TransactionModel
from auth import get_user_by_username

class NotificationService:
    """Service for managing notifications and reminders"""
    
    def __init__(self):
        self.notification_model = NotificationModel()
        self.budget_model = BudgetModel()
        self.recurring_model = RecurringModel()
        self.transaction_model = TransactionModel()
    
    def create_notification(self, user: str, type: str, title: str, 
                          message: str, data: str = '') -> Dict:
        """Create a new notification"""
        return self.notification_model.create({
            'user': user,
            'type': type,
            'title': title,
            'message': message,
            'date': datetime.now().isoformat(),
            'data': data
        })
    
    def get_user_notifications(self, user: str, unread_only: bool = False) -> List[Dict]:
        """Get notifications for a user"""
        return self.notification_model.get_by_user(user, unread_only)
    
    def mark_read(self, notification_id: int) -> bool:
        """Mark notification as read"""
        return self.notification_model.mark_read(notification_id)
    
    def mark_all_read(self, user: str) -> int:
        """Mark all notifications as read"""
        return self.notification_model.mark_all_read(user)
    
    def get_unread_count(self, user: str) -> int:
        """Get unread notification count"""
        return self.notification_model.get_unread_count(user)
    
    def check_budget_alerts(self, person: str) -> List[Dict]:
        """Check for budget alerts and create notifications"""
        alerts = []
        budgets = self.budget_model.get_by_person(person)
        
        # Get current month transactions
        now = datetime.now()
        start_of_month = now.replace(day=1).strftime('%Y-%m-%d')
        
        for budget in budgets:
            category = budget['category']
            limit = float(budget['amount'])
            
            # Calculate spending for this category this month
            transactions = self.transaction_model.filter({
                'person': person,
                'category': category,
                'start_date': start_of_month,
                'type': 'expense'
            })
            
            spent = sum(float(t['price']) for t in transactions)
            percentage = (spent / limit * 100) if limit > 0 else 0
            
            # Check thresholds
            if percentage >= Config.BUDGET_CRITICAL_THRESHOLD * 100:
                # Critical: 90%+
                alert = self.create_notification(
                    user=person,
                    type='budget_critical',
                    title=f'🚨 Budget Alert: {category}',
                    message=f'You\'ve used {percentage:.0f}% of your {category} budget (${spent:.2f} of ${limit:.2f})',
                    data=f'{{"category": "{category}", "spent": {spent}, "limit": {limit}, "percentage": {percentage}}}'
                )
                alerts.append(alert)
                
                # Send email if enabled
                if Config.ENABLE_EMAIL_NOTIFICATIONS:
                    self._send_budget_alert_email(person, category, spent, limit, percentage, 'critical')
            
            elif percentage >= Config.BUDGET_WARNING_THRESHOLD * 100:
                # Warning: 75%+
                alert = self.create_notification(
                    user=person,
                    type='budget_warning',
                    title=f'⚠️ Budget Warning: {category}',
                    message=f'You\'ve used {percentage:.0f}% of your {category} budget (${spent:.2f} of ${limit:.2f})',
                    data=f'{{"category": "{category}", "spent": {spent}, "limit": {limit}, "percentage": {percentage}}}'
                )
                alerts.append(alert)
                
                # Send email if enabled
                if Config.ENABLE_EMAIL_NOTIFICATIONS:
                    self._send_budget_alert_email(person, category, spent, limit, percentage, 'warning')
        
        return alerts
    
    def check_recurring_reminders(self, person: str) -> List[Dict]:
        """Check for upcoming recurring transactions and create reminders"""
        reminders = []
        recurring_items = self.recurring_model.get_active()
        
        # Filter for this person's items
        person_items = [item for item in recurring_items if item['person'] == person]
        
        today = datetime.now().date()
        
        for item in person_items:
            next_date = datetime.strptime(item['next_date'], '%Y-%m-%d').date()
            days_until = (next_date - today).days
            
            # Reminder 3 days before
            if days_until == 3:
                reminder = self.create_notification(
                    user=person,
                    type='recurring_reminder',
                    title=f'📅 Upcoming: {item["item_name"]}',
                    message=f'{item["item_name"]} ({item["frequency"]}) is due in 3 days on {item["next_date"]} - ${item["price"]}',
                    data=f'{{"recurring_id": "{item["id"]}", "next_date": "{item["next_date"]}", "amount": {item["price"]}}}'
                )
                reminders.append(reminder)
            
            # Reminder on the day
            elif days_until == 0:
                reminder = self.create_notification(
                    user=person,
                    type='recurring_due',
                    title=f'💰 Due Today: {item["item_name"]}',
                    message=f'{item["item_name"]} is due today - ${item["price"]}',
                    data=f'{{"recurring_id": "{item["id"]}", "next_date": "{item["next_date"]}", "amount": {item["price"]}}}'
                )
                reminders.append(reminder)
        
        return reminders
    
    def check_large_transaction_alert(self, person: str, amount: float, 
                                     item_name: str) -> Dict:
        """Create alert for large transactions"""
        # Calculate average transaction amount
        transactions = self.transaction_model.filter({
            'person': person,
            'type': 'expense'
        })
        
        if len(transactions) < 5:
            return None
        
        avg_amount = sum(float(t['price']) for t in transactions) / len(transactions)
        
        # Alert if transaction is 3x average
        if amount > avg_amount * 3:
            return self.create_notification(
                user=person,
                type='large_transaction',
                title='💸 Large Transaction Detected',
                message=f'You just spent ${amount:.2f} on {item_name} (3x your average transaction)',
                data=f'{{"amount": {amount}, "average": {avg_amount}, "item": "{item_name}"}}'
            )
        
        return None
    
    def create_goal_achievement(self, person: str, goal_type: str, 
                               details: str) -> Dict:
        """Create notification for achieving a goal"""
        titles = {
            'under_budget': '🎉 Budget Success!',
            'savings_milestone': '💰 Savings Milestone!',
            'no_spending': '✨ Spending Freeze Success!'
        }
        
        return self.create_notification(
            user=person,
            type='achievement',
            title=titles.get(goal_type, '🎉 Achievement!'),
            message=details,
            data=f'{{"goal_type": "{goal_type}"}}'
        )
    
    def _send_budget_alert_email(self, person: str, category: str, 
                                spent: float, limit: float, 
                                percentage: float, severity: str):
        """Send budget alert email"""
        user = get_user_by_username(person)
        if not user or not user.get('email'):
            return
        
        email = user['email']
        
        if not Config.SMTP_USERNAME or not Config.SMTP_PASSWORD:
            print(f"Email notification skipped (SMTP not configured) for {person}")
            return
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'Budget Alert: {category}'
            msg['From'] = Config.SMTP_FROM
            msg['To'] = email
            
            # Text version
            text = f"""
Budget Alert: {category}

You've used {percentage:.0f}% of your {category} budget.
Spent: ${spent:.2f}
Limit: ${limit:.2f}
Remaining: ${limit - spent:.2f}

{'⚠️ Warning: Approaching budget limit' if severity == 'warning' else '🚨 Critical: Over or near budget limit'}

- Receipt Tracker
            """
            
            # HTML version
            color = '#ffc107' if severity == 'warning' else '#dc3545'
            html = f"""
<html>
  <body style="font-family: Arial, sans-serif;">
    <div style="background: {color}; color: white; padding: 20px; text-align: center;">
      <h2>{'⚠️' if severity == 'warning' else '🚨'} Budget Alert</h2>
    </div>
    <div style="padding: 20px;">
      <h3>{category} Budget</h3>
      <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
        <p><strong>Usage:</strong> {percentage:.0f}%</p>
        <div style="background: #dee2e6; height: 20px; border-radius: 10px;">
          <div style="background: {color}; width: {min(percentage, 100)}%; height: 20px; border-radius: 10px;"></div>
        </div>
        <p><strong>Spent:</strong> ${spent:.2f}</p>
        <p><strong>Limit:</strong> ${limit:.2f}</p>
        <p><strong>Remaining:</strong> ${limit - spent:.2f}</p>
      </div>
      <p style="margin-top: 20px;">
        {'You\'re approaching your budget limit. Consider reducing spending in this category.' if severity == 'warning' 
         else 'You\'ve reached or exceeded your budget limit. Please review your spending.'}
      </p>
    </div>
    <div style="background: #f8f9fa; padding: 10px; text-align: center; color: #666;">
      <small>Receipt Tracker Budget Alert System</small>
    </div>
  </body>
</html>
            """
            
            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(html, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"Budget alert email sent to {person}")
        
        except Exception as e:
            print(f"Error sending budget alert email: {e}")
    
    def send_daily_summary(self, person: str):
        """Send daily spending summary"""
        user = get_user_by_username(person)
        if not user or not user.get('email'):
            return
        
        # Get today's transactions
        today = datetime.now().strftime('%Y-%m-%d')
        transactions = self.transaction_model.filter({
            'person': person,
            'start_date': today,
            'end_date': today
        })
        
        if not transactions:
            return
        
        total_spent = sum(float(t['price']) for t in transactions if t['type'] == 'expense')
        total_income = sum(float(t['price']) for t in transactions if t['type'] == 'income')
        
        # Create notification
        self.create_notification(
            user=person,
            type='daily_summary',
            title=f'📊 Daily Summary: {today}',
            message=f'Today: {len(transactions)} transactions, ${total_spent:.2f} spent, ${total_income:.2f} income',
            data=f'{{"transactions": {len(transactions)}, "spent": {total_spent}, "income": {total_income}}}'
        )


# Singleton instance
notification_service = NotificationService()