## Usage Workflow

### For Regular Users

1. **Login** → Use your credentials
2. **Dashboard** → View your spending and group expenses
3. **Upload Receipt** → Scan receipt, assign to group if shared
4. **Set Budgets** → Create monthly spending limits
5. **Manage Accounts** → Add your bank accounts/cards
6. **Join Groups** → Ask admin to add you to expense groups

### For Administrators

1. **Login as Admin** → Use admin credentials
2. **Admin Panel** → Click Settings → Admin Panel
3. **Create Users** → Add new user accounts
4. **Manage Groups** → View and organize all groups
5. **Reset Passwords** → Help users regain access
6. **Deactivate Users** → Disable accounts as needed# Receipt Tracker - Raspberry Pi Web Application

A Flask-based expense tracking app with receipt scanning, budgets, recurring transactions, and multi-user authentication.

## Key Features

- 🔐 **User Authentication** - Secure login system with admin and regular user roles
- 📸 **Receipt Scanning** - Azure AI automatically extracts items from receipt images
- 👥 **Multi-User Support** - Each user has their own dashboard and data
- 👨‍👩‍👧 **Expense Groups** - Create groups for shared expenses (household, roommates)
- 💰 **Split Transactions** - Automatically split costs among group members
- 💳 **Account Management** - Track multiple bank accounts and payment methods
- 📊 **Budget Tracking** - Set limits per category with progress monitoring
- 🔄 **Recurring Transactions** - Auto-generate regular expenses/income
- 🔍 **Advanced Search** - Filter and export transaction history
- 👑 **Admin Panel** - Manage users and groups system-wide

## Project Structure

```
receipt-tracker/
├── app.py                 # Main Flask application
├── auth.py                # Authentication module
├── database.py            # PostgreSQL module (production)
├── requirements.txt       # Python dependencies
├── .env                   # Environment config
├── database.csv           # Transaction data (CSV mode)
├── budgets.csv            # Budget data (CSV mode)
├── recurring.csv          # Recurring transactions (CSV mode)
├── accounts.csv           # Bank accounts (CSV mode)
├── groups.csv             # Expense sharing groups (CSV mode)
├── splits.csv             # Transaction splits (CSV mode)
├── users.csv              # User accounts (CSV mode)
├── uploads/               # Temp upload folder
├── receipts/              # Stored receipt images
└── templates/
    ├── base.html          # Base template
    ├── login.html         # Login page
    ├── dashboard.html     # Main dashboard
    ├── upload.html        # Receipt upload
    ├── search.html        # Transaction search
    ├── manual.html        # Manual entry
    ├── budgets.html       # Budget management
    ├── recurring.html     # Recurring transactions
    ├── accounts.html      # Account management
    ├── groups.html        # Group management
    └── admin.html         # Admin dashboard
```

## Features

| Feature | Description |
|---------|-------------|
| **Receipt Scanning** | Upload images → Azure AI extracts items → Review & save |
| **Receipt Storage** | View stored receipt images from any transaction |
| **Dashboard** | Charts for spending trends, categories, accounts, budget alerts |
| **Person Filtering** | Filter dashboard by person to see individual spending |
| **Budgets** | Set monthly limits per category with progress tracking |
| **Recurring** | Auto-generate transactions (daily/weekly/biweekly/monthly/yearly) |
| **Accounts** | Manage multiple bank accounts, credit cards, and payment methods |
| **Groups** | Create expense sharing groups (household, roommates, etc.) |
| **Split Transactions** | Automatically split expenses among group members |
| **Search** | Filter by date, category, account, person; export to CSV |
| **Manual Entry** | Add expenses/income without receipts |

## Categories

**Expenses:** Rent, Electric, Investment, Car, Medical, Groceries, Entertainment, Subscriptions, Household, Eating Out, Shopping, Other

**Income:** Salary, Freelance, Investment, Gift, Refund, Other

## Quick Start

### First Time Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Run application
python app.py
```

### Login

1. Navigate to `http://localhost:5000`
2. Use default credentials:
   - **Admin**: username: `admin`, password: `admin123`
   - **User 1**: username: `john`, password: `password`
   - **User 2**: username: `jane`, password: `password`

3. **IMPORTANT**: Change the admin password after first login!

### User Types

**Regular Users:**
- View their own transactions
- See transactions from groups they're in
- Create budgets, accounts, and recurring transactions
- Cannot see other users' personal data

**Administrators:**
- All regular user permissions
- Create new users
- Reset passwords
- Activate/deactivate accounts
- Manage all groups system-wide
- Access admin dashboard at `/admin`

## Azure Document Intelligence Setup

1. Create Azure account and Document Intelligence resource
2. Get endpoint URL and API key from Azure Portal
3. Add to `.env`:
   ```
   AZURE_DOC_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com
   AZURE_DOC_INTELLIGENCE_KEY=your-api-key
   ```

**Note:** Without Azure credentials, app uses mock data for testing.

## Database Options

### CSV Mode (Default)
- Set `USE_CSV=true` in `.env`
- Data stored in `database.csv`, `budgets.csv`, `recurring.csv`
- Receipt images stored in `receipts/` folder

### PostgreSQL Mode

```bash
# Install on Raspberry Pi
sudo apt update && sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE receipt_tracker;
CREATE USER pi WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE receipt_tracker TO pi;
\q
```

Update `.env`:
```
USE_CSV=false
DB_HOST=localhost
DB_NAME=receipt_tracker
DB_USER=pi
DB_PASSWORD=yourpassword
```

## Raspberry Pi Deployment

### systemd Service

```bash
sudo nano /etc/systemd/system/receipt-tracker.service
```

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

```bash
sudo systemctl enable receipt-tracker
sudo systemctl start receipt-tracker
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload receipt image |
| POST | `/api/save-items` | Save extracted items |
| POST | `/api/manual-entry` | Add manual transaction |
| GET | `/api/transactions` | Get filtered transactions |
| GET | `/api/transaction/<id>` | Get single transaction |
| GET | `/api/dashboard-data` | Get chart data |
| GET | `/api/categories` | List categories |
| GET | `/api/accounts` | List accounts |
| GET | `/api/persons` | List persons |
| GET | `/api/budgets` | List budgets |
| POST | `/api/budgets` | Create budget |
| PUT | `/api/budgets/<id>` | Update budget |
| DELETE | `/api/budgets/<id>` | Delete budget |
| GET | `/api/recurring` | List recurring |
| POST | `/api/recurring` | Create recurring |
| POST | `/api/recurring/<id>/toggle` | Pause/resume |
| DELETE | `/api/recurring/<id>` | Delete recurring |
| GET | `/receipts/<filename>` | View receipt image |
