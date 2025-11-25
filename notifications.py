"""
Email notification system for budgets, recurring charges, and custom reminders
"""

import os
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

NOTIFICATIONS_FILE = 'csv/notifications.csv'
NOTIFICATION_LOG_FILE = 'csv/notification_log.csv'
NOTIFICATION_HEADERS = ['id', 'user_id', 'type', 'title', 'message', 'trigger_date', 'repeat', 'active', 'email_sent']
LOG_HEADERS = ['id', 'notification_id', 'sent_date', 'recipient', 'subject', 'status']

# Email config
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM = os.getenv('SMTP_FROM', SMTP_USERNAME)

def init_notifications():
    """Initialize notification files"""
    if not os.path.exists(NOTIFICATIONS_FILE):
        with open(NOTIFICATIONS_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=NOTIFICATION_HEADERS)
            writer.writeheader()
    
    if not os.path.exists(NOTIFICATION_LOG_FILE):
        with open(NOTIFICATION_LOG_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=LOG_HEADERS)
            writer.writeheader()

def send_email(to_email, subject, body_text, body_html=None):
    """Send an email notification"""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print(f"\n{'='*60}")
        print(f"EMAIL NOTIFICATION (not configured)")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body_text}")
        print(f"{'='*60}\n")
        return True
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_FROM
        msg['To'] = to_email
        
        part1 = MIMEText(body_text, 'plain')
        msg.attach(part1)
        
        if body_html:
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def check_budget_alerts(user_id, username, email, transactions, budgets):
    """Check if any budgets are close to limit and send alerts"""
    from datetime import datetime
    current_month = datetime.now().strftime('%Y-%m')
    
    alerts = []
    for budget in budgets:
        if budget.get('person') != username:
            continue
        
        category = budget['category']
        limit = float(budget['amount'])
        
        # Calculate spending
        spent = sum(
            float(t.get('price', 0)) 
            for t in transactions 
            if t.get('category') == category 
            and t.get('date', '').startswith(current_month)
            and t.get('type', 'expense') == 'expense'
        )
        
        percentage = (spent / limit * 100) if limit > 0 else 0
        
        # Alert at 75%, 90%, and 100%
        if percentage >= 75:
            threshold = 100 if percentage >= 100 else (90 if percentage >= 90 else 75)
            alerts.append({
                'category': category,
                'spent': spent,
                'limit': limit,
                'percentage': percentage,
                'threshold': threshold
            })
    
    if alerts:
        subject = f"Budget Alert: {len(alerts)} Category(s) Need Attention"
        body_text = f"Hello {username},\n\nYou're approaching or exceeding your budget limits:\n\n"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #f72585;">Budget Alerts</h2>
            <p>Hello {username},</p>
            <p>You're approaching or exceeding your budget limits:</p>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background: #f8f9fa;">
                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">Category</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: right;">Spent</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: right;">Limit</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: right;">Status</th>
                </tr>
        """
        
        for alert in alerts:
            color = '#dc3545' if alert['percentage'] >= 100 else ('#ffc107' if alert['percentage'] >= 90 else '#fd7e14')
            status = f"{alert['percentage']:.0f}%"
            
            body_text += f"  • {alert['category']}: ${alert['spent']:.2f} / ${alert['limit']:.2f} ({status})\n"
            body_html += f"""
                <tr>
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{alert['category']}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px; text-align: right;">${alert['spent']:.2f}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px; text-align: right;">${alert['limit']:.2f}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px; text-align: right; color: {color}; font-weight: bold;">{status}</td>
                </tr>
            """
        
        body_html += """
            </table>
            <p style="margin-top: 20px;">Review your spending in the dashboard to stay on track.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">Receipt Tracker - Budget Monitoring</p>
        </body>
        </html>
        """
        
        body_text += "\nReview your spending in the dashboard to stay on track.\n\n- Receipt Tracker"
        
        if send_email(email, subject, body_text, body_html):
            log_notification(user_id, 'budget_alert', email, subject, 'sent')
            return True
    
    return False

def check_recurring_reminders(user_id, username, email, recurring_items):
    """Check for upcoming recurring charges in next 3 days"""
    today = datetime.now().date()
    upcoming = []
    
    for item in recurring_items:
        if item.get('active') != 'true':
            continue
        
        next_date = datetime.strptime(item['next_date'], '%Y-%m-%d').date()
        days_until = (next_date - today).days
        
        if 0 <= days_until <= 3:
            upcoming.append({
                'name': item['item_name'],
                'amount': float(item['price']),
                'date': next_date,
                'days': days_until,
                'frequency': item['frequency']
            })
    
    if upcoming:
        upcoming.sort(key=lambda x: x['days'])
        subject = f"Upcoming Charges: {len(upcoming)} Payment(s) Due Soon"
        
        body_text = f"Hello {username},\n\nYou have upcoming recurring charges:\n\n"
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #4361ee;">Upcoming Recurring Charges</h2>
            <p>Hello {username},</p>
            <p>You have upcoming recurring charges:</p>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background: #f8f9fa;">
                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">Item</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: right;">Amount</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">Date</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">Due In</th>
                </tr>
        """
        
        for item in upcoming:
            due_text = "Today!" if item['days'] == 0 else f"{item['days']} day{'s' if item['days'] > 1 else ''}"
            color = '#dc3545' if item['days'] == 0 else '#ffc107'
            
            body_text += f"  • {item['name']}: ${item['amount']:.2f} on {item['date']} ({due_text})\n"
            body_html += f"""
                <tr>
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{item['name']}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px; text-align: right;">${item['amount']:.2f}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{item['date']}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; color: {color}; font-weight: bold;">{due_text}</td>
                </tr>
            """
        
        total = sum(i['amount'] for i in upcoming)
        body_text += f"\nTotal: ${total:.2f}\n\n- Receipt Tracker"
        body_html += f"""
                <tr style="background: #e9ecef; font-weight: bold;">
                    <td style="border: 1px solid #dee2e6; padding: 8px;">Total</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px; text-align: right;">${total:.2f}</td>
                    <td colspan="2" style="border: 1px solid #dee2e6; padding: 8px;"></td>
                </tr>
            </table>
            <p style="margin-top: 20px;">Make sure you have sufficient funds available.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">Receipt Tracker - Payment Reminders</p>
        </body>
        </html>
        """
        
        if send_email(email, subject, body_text, body_html):
            log_notification(user_id, 'recurring_reminder', email, subject, 'sent')
            return True
    
    return False

def check_custom_reminders(user_id, email, custom_notifications):
    """Check and send custom reminder notifications"""
    today = datetime.now().date()
    sent_count = 0
    
    for notif in custom_notifications:
        if notif.get('active') != 'true' or notif.get('email_sent') == 'true':
            continue
        
        trigger_date = datetime.strptime(notif['trigger_date'], '%Y-%m-%d').date()
        
        if trigger_date <= today:
            subject = notif['title']
            body_text = notif['message']
            body_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #4361ee;">{notif['title']}</h2>
                <p>{notif['message']}</p>
                <hr>
                <p style="color: #666; font-size: 12px;">Receipt Tracker - Custom Reminder</p>
            </body>
            </html>
            """
            
            if send_email(email, subject, body_text, body_html):
                log_notification(user_id, 'custom_reminder', email, subject, 'sent')
                mark_notification_sent(notif['id'])
                sent_count += 1
    
    return sent_count > 0

def mark_notification_sent(notification_id):
    """Mark a notification as sent"""
    try:
        with open(NOTIFICATIONS_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            notifications = list(reader)
        
        for notif in notifications:
            if notif['id'] == str(notification_id):
                notif['email_sent'] = 'true'
                if notif.get('repeat') != 'true':
                    notif['active'] = 'false'
        
        with open(NOTIFICATIONS_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=NOTIFICATION_HEADERS)
            writer.writeheader()
            for notif in notifications:
                writer.writerow(notif)
    except Exception as e:
        print(f"Error marking notification sent: {e}")

def log_notification(user_id, notif_type, recipient, subject, status):
    """Log a sent notification"""
    try:
        with open(NOTIFICATION_LOG_FILE, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=LOG_HEADERS)
            
            # Get next ID
            try:
                with open(NOTIFICATION_LOG_FILE, 'r', newline='') as rf:
                    reader = csv.DictReader(rf)
                    logs = list(reader)
                    next_id = max([int(log['id']) for log in logs]) + 1 if logs else 1
            except:
                next_id = 1
            
            writer.writerow({
                'id': str(next_id),
                'notification_id': user_id,
                'sent_date': datetime.now().isoformat(),
                'recipient': recipient,
                'subject': subject,
                'status': status
            })
    except Exception as e:
        print(f"Error logging notification: {e}")

def run_notification_checks(users, transactions, budgets, recurring_items, custom_notifications):
    """Run all notification checks for all users"""
    results = {'budget_alerts': 0, 'recurring_reminders': 0, 'custom_reminders': 0}
    
    for user in users:
        if user.get('active') != 'true':
            continue
        
        user_id = user['id']
        username = user['full_name']
        email = user.get('email', '')
        
        if not email:
            continue
        
        # Budget alerts
        user_transactions = [t for t in transactions if t.get('person') == username]
        user_budgets = [b for b in budgets if b.get('person') == username]
        if check_budget_alerts(user_id, username, email, user_transactions, user_budgets):
            results['budget_alerts'] += 1
        
        # Recurring charge reminders
        user_recurring = [r for r in recurring_items if r.get('person') == username]
        if check_recurring_reminders(user_id, username, email, user_recurring):
            results['recurring_reminders'] += 1
        
        # Custom reminders
        user_custom = [n for n in custom_notifications if n.get('user_id') == user_id]
        if check_custom_reminders(user_id, email, user_custom):
            results['custom_reminders'] += 1
    
    return results
