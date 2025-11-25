# Receipt Tracker - Refactored & Enhanced

A professional Flask-based expense tracking application with receipt scanning, notifications, analytics, and multi-user support.

## 🎯 Features

### Core Features
- 📸 **Receipt Scanning** - Azure AI-powered automatic item extraction
- 💳 **Multi-Account Tracking** - Manage multiple bank accounts and payment methods
- 👥 **Multi-User Support** - Secure authentication with user and admin roles
- 🏘️ **Expense Groups** - Share and split expenses with household/roommates
- 💰 **Budget Management** - Set limits and track progress per category
- 🔄 **Recurring Transactions** - Auto-generate regular expenses/income
- 🔍 **Advanced Search** - Filter and export transaction history

### Enhanced Features (NEW)
- 🔔 **Smart Notifications** - Budget alerts, recurring reminders, large transaction alerts
- 📊 **Analytics Dashboard** - Insights, predictions, spending patterns, trends
- 📈 **Month-End Projections** - Predict spending based on current pace
- 📅 **Spending Patterns** - Day-of-week analysis, weekend vs weekday
- 🎯 **Actionable Insights** - AI-generated spending recommendations
- 💌 **Email Notifications** - Optional SMTP email alerts

## 📦 Project Structure

```
receipt-tracker/
├── app.py                          # Main Flask application
├── config.py                       # Configuration management
├── models.py                       # Data models & CSV operations
├── auth.py                         # Authentication module
├── services/
│   ├── __init__.py
│   ├── azure_service.py            # Receipt scanning service
│   ├── notification_service.py     # Notification & reminder service
│   ├── analytics_service.py        # Dashboard analytics service
│   └── recurring_processor.py      # Recurring transaction processor
├── routes/
│   ├── __init__.py
│   ├── main.py                     # Dashboard & core pages
│   ├── api.py                      # REST API endpoints
│   ├── transactions.py             # Upload, manual, search
│   ├── budgets.py                  # Budget management
│   ├── recurring.py                # Recurring transactions
│   ├── accounts.py                 # Account management
│   ├── groups.py                   # Group management
│   └── admin.py                    # Admin panel
├── utils/
│   ├── __init__.py
│   ├── helpers.py                  # Helper functions
│   └── decorators.py               # Custom decorators
├── templates/                      # HTML templates
│   ├── base.html
│   ├── dashboard_enhanced.html     # Enhanced dashboard (NEW)
│   ├── login.html
│   └── ... (other templates)
├── static/                         # Static files (CSS, JS, images)
├── uploads/                        # Temporary upload folder
├── receipts/                       # Receipt image storage
├── *.csv                          # Data storage (CSV mode)
├── requirements.txt               # Python dependencies
├── setup.sh                       # Setup script
├── .env                           # Environment configuration
└── README.md                      # This file
```

## 🚀 Quick Start

### 1. Clone or Download

```bash
git clone <your-repo-url>
cd receipt-tracker
```

### 2. Run Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

This creates:
- Directory structure
- Empty CSV files
- .env configuration file
- .gitignore file

### 3. Configure Environment

Edit `.env` file with your settings:

```env
# Required
SECRET_KEY=your-random-secret-key-here

# Optional: Azure Document Intelligence
AZURE_DOC_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com
AZURE_DOC_INTELLIGENCE_KEY=your-api-key

# Optional: Email Notifications
ENABLE_EMAIL_NOTIFICATIONS=true
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Notification Thresholds
BUDGET_WARNING_THRESHOLD=0.75
BUDGET_CRITICAL_THRESHOLD=0.90
```

### 4. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Run Application

```bash
python app.py
```

Access at: `http://localhost:5000`

### 6. Login

Default credentials:
- **Admin**: `admin` / `admin123`
- **User 1**: `john` / `password`
- **User 2**: `jane` / `password`

⚠️ **Change default passwords immediately after first login!**

## 📖 User Guide

### For Regular Users

#### Dashboard
- View enhanced analytics with insights and predictions
- See notifications via bell icon (top right)
- Toggle between personal and group views
- View spending trends, patterns, and projections

#### Upload Receipt
1. Go to **Upload** page
2. Drag & drop or click to select receipt image
3. Click "Process Receipt"
4. Review extracted items
5. Select group (if shared expense)
6. Adjust split percentages if needed
7. Click "Save All Items"

#### Manual Entry
1. Go to **Manual** page
2. Choose Expense or Income tab
3. Fill in details
4. Select group (optional)
5. Adjust splits (if group selected)
6. Click "Add Expense" or "Add Income"

#### Set Budgets
1. Go to **Budgets** page
2. Click "Add Budget"
3. Select category and set monthly limit
4. Save budget
5. View progress on dashboard

#### Manage Recurring
1. Go to **Recurring** page
2. Click "Add Recurring"
3. Fill in details and frequency
4. Save
5. Transactions auto-generate on schedule

#### Notifications
- Click bell icon to view notifications
- Types:
  - 🚨 Budget Critical (90%+)
  - ⚠️ Budget Warning (75%+)
  - 📅 Recurring Reminders (3 days before)
  - 💰 Recurring Due Today
  - 💸 Large Transaction Alerts
  - 🎉 Achievements
- Click notification to mark as read
- "Mark all read" button available

### For Administrators

#### Admin Panel
Access via: **Settings** → **Admin Panel**

**Capabilities:**
- Create new user accounts
- Reset passwords
- Activate/deactivate users
- Grant admin privileges
- View system statistics
- Manage all groups

#### Create User
1. Go to Admin Panel
2. Click "Create User"
3. Fill in username, full name, email, password
4. Check "Administrator privileges" if admin
5. Save

#### Reset Password
1. Go to Admin Panel
2. Click edit icon on user row
3. Enter new password
4. Save

## 🔔 Notification System

### Automatic Notifications

| Type | Trigger | Action |
|------|---------|--------|
| Budget Warning | Spending reaches 75% | Alert + Email (if enabled) |
| Budget Critical | Spending reaches 90% | Alert + Email (if enabled) |
| Recurring Reminder | 3 days before due date | Notification |
| Recurring Due | Day of due date | Notification |
| Large Transaction | 3x average spending | Alert |

### Email Notifications

To enable email notifications:

1. Update `.env`:
```env
ENABLE_EMAIL_NOTIFICATIONS=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

2. For Gmail:
   - Enable 2-Factor Authentication
   - Generate App Password at: https://myaccount.google.com/apppasswords
   - Use app password in `.env`

## 📊 Analytics Dashboard

### Insights Available

- **Spending Trends**: Month-over-month comparisons
- **Top Categories**: Where you spend most
- **Top Stores**: Highest spending locations
- **Spending Patterns**: Day-of-week analysis
- **Weekend vs Weekday**: Comparative spending
- **Month-End Projection**: Predicted total spending
- **Budget Performance**: Category-wise progress
- **Recurring Impact**: Monthly/annual recurring costs
- **Actionable Recommendations**: AI-generated tips

### Understanding Insights

**Spending Increase Detected**
- Your spending is up X% from last month
- Action: Review recent expenses

**Budget Exceeded**
- N categories over budget
- Action: Adjust budget or reduce spending

**Weekend Spending Pattern**
- You spend $X more on weekends
- Action: Plan weekend activities with budget

## 🔧 Configuration

### Database Options

**CSV Mode (Default)**
```env
USE_CSV=true
```
- Simple, no installation required
- Data stored in `.csv` files
- Perfect for personal use

**PostgreSQL Mode**
```env
USE_CSV=false
DB_HOST=localhost
DB_NAME=receipt_tracker
DB_USER=postgres
DB_PASSWORD=your-password
```
- Scalable for production
- Better performance
- Requires PostgreSQL installation

### Notification Thresholds

Adjust in `.env`:
```env
BUDGET_WARNING_THRESHOLD=0.75   # 75%
BUDGET_CRITICAL_THRESHOLD=0.90  # 90%
```

### Recurring Processing

Recurring transactions are automatically processed when:
- Dashboard is loaded
- User logs in
- Manual trigger via recurring page

## 🛠️ Development

### Adding New Features

**Add New Route:**
```python
# In routes/my_feature.py
from flask import Blueprint
my_bp = Blueprint('my_feature', __name__)

@my_bp.route('/my-feature')
def my_page():
    return render_template('my_feature.html')

# In app.py, register blueprint
from routes.my_feature import my_bp
app.register_blueprint(my_bp)
```

**Add New Service:**
```python
# In services/my_service.py
class MyService:
    def do_something(self):
        pass

my_service = MyService()

# Import in services/__init__.py
from .my_service import my_service
```

**Add New Model:**
```python
# In models.py
class MyModel(CSVModel):
    def __init__(self):
        super().__init__('my_table')
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
pytest
```

## 📱 Mobile Support

The web interface is responsive and works on:
- Desktop browsers
- Tablets
- Mobile phones (iOS & Android)

Access via mobile browser at: `http://your-raspberry-pi-ip:5000`

## 🔒 Security

### Best Practices

1. **Change Default Passwords** immediately
2. **Use Strong Passwords** (8+ characters, mixed case, numbers)
3. **Enable HTTPS** in production
4. **Update SECRET_KEY** in `.env`
5. **Regular Backups** of CSV files
6. **Keep Dependencies Updated**: `pip install --upgrade -r requirements.txt`

### Data Privacy

- Each user sees only their own data
- Group members see shared group expenses
- Admins can manage users but don't see transaction data
- Passwords are hashed (SHA-256)

## 🐛 Troubleshooting

### Notifications Not Appearing
```bash
# Check notifications.csv exists
ls -la notifications.csv

# Check permissions
chmod 644 notifications.csv

# Check browser console for errors
F12 → Console tab
```

### Dashboard Not Loading
```bash
# Check all services exist
ls -la services/

# Verify imports
python -c "from services import notification_service, analytics_service"

# Check Flask logs
tail -f app.log
```

### Email Not Sending
```bash
# Test SMTP settings
python -c "
from config import Config
print('SMTP Server:', Config.SMTP_SERVER)
print('SMTP User:', Config.SMTP_USERNAME)
print('Enabled:', Config.ENABLE_EMAIL_NOTIFICATIONS)
"
```

## 📝 API Documentation

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard-enhanced` | GET | Enhanced analytics data |
| `/api/notifications` | GET | User notifications |
| `/api/notifications/:id/read` | POST | Mark notification read |
| `/api/transactions` | GET | Get transactions (filtered) |
| `/api/budgets` | GET/POST | Budget CRUD |
| `/api/recurring` | GET/POST | Recurring CRUD |
| `/api/accounts` | GET/POST | Account CRUD |
| `/api/groups` | GET/POST | Group CRUD |

Full API documentation available in `routes/api.py`

## 🚀 Deployment

### Raspberry Pi (systemd)

1. Create service file:
```bash
sudo nano /etc/systemd/system/receipt-tracker.service
```

2. Add content:
```ini
[Unit]
Description=Receipt Tracker
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/receipt-tracker
Environment="PATH=/home/pi/receipt-tracker/venv/bin"
ExecStart=/home/pi/receipt-tracker/venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl enable receipt-tracker
sudo systemctl start receipt-tracker
sudo systemctl status receipt-tracker
```

### Docker (Optional)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
```

```bash
docker build -t receipt-tracker .
docker run -p 5000:5000 -v $(pwd)/data:/app receipt-tracker
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## 📄 License

MIT License - feel free to use for personal or commercial projects.

## 💡 Support

For issues or questions:
1. Check troubleshooting section
2. Review logs: `tail -f app.log`
3. Check GitHub issues
4. Create new issue with details

## 🎉 Acknowledgments

- Flask framework
- Bootstrap UI
- Chart.js for visualizations
- Azure Cognitive Services
- All contributors

---

**Version**: 2.0.0 (Refactored & Enhanced)
**Last Updated**: 2025