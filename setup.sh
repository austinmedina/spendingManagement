#!/bin/bash

# Receipt Tracker - Setup Script
# Creates directory structure and initializes files

echo "=========================================="
echo "Receipt Tracker - Setup Script"
echo "=========================================="
echo ""

# Create directories
echo "Creating directory structure..."
mkdir -p services
mkdir -p routes
mkdir -p utils
mkdir -p uploads
mkdir -p receipts
mkdir -p templates
mkdir -p static

# Create __init__.py files
echo "Creating Python package files..."
touch services/__init__.py
touch routes/__init__.py
touch utils/__init__.py

# Create empty CSV files if they don't exist
echo "Initializing CSV files..."

if [ ! -f "csv/database.csv" ]; then
    echo "id,item_name,category,store,date,price,user_id,bank_account_id,type,receipt_image,receipt_json,group_id,receipt_group_id" > csv/database.csv
fi

if [ ! -f "csv/budgets.csv" ]; then
    echo "id,category,amount,period,start_date,user_id" > csv/budgets.csv
fi

if [ ! -f "csv/recurring.csv" ]; then
    echo "id,item_name,category,store,price,user_id,bank_account_id,type,frequency,next_date,active,group_id" > csv/recurring.csv
fi

if [ ! -f "csv/accounts.csv" ]; then
    echo "id,name,type,user_id" > csv/accounts.csv
fi

if [ ! -f "csv/groups.csv" ]; then
    echo "id,name,members" > csv/groups.csv
fi

if [ ! -f "csv/splits.csv" ]; then
    echo "id,receipt_group_id,user_id,amount,percentage" > csv/splits.csv
fi

if [ ! -f "csv/notifications.csv" ]; then
    echo "id,user_id,type,title,message,date,read,data" > csv/notifications.csv
fi

if [ ! -f "csv/users.csv" ]; then
    echo "id,username,password_hash,full_name,email,is_admin,active,must_change_password" > csv/users.csv
fi

if [ ! -f "csv/reset_codes.csv" ]; then
    echo "code,user_id,expires,used" > csv/reset_codes.csv
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# Flask Configuration
SECRET_KEY=change-this-to-a-random-string-in-production
FLASK_ENV=development
FLASK_DEBUG=true

# Database Configuration
USE_CSV=true

# PostgreSQL (only needed when USE_CSV=false)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=receipt_tracker
DB_USER=postgres
DB_PASSWORD=

# Azure Document Intelligence
AZURE_DOC_INTELLIGENCE_ENDPOINT=
AZURE_DOC_INTELLIGENCE_KEY=

# Email Configuration (for notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=

# Notification Settings
ENABLE_EMAIL_NOTIFICATIONS=false
BUDGET_WARNING_THRESHOLD=0.75
BUDGET_CRITICAL_THRESHOLD=0.90
EOF
    echo "Created .env file - Please update with your settings!"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "Creating .gitignore..."
    cat > .gitignore << 'EOF'
venv/
.env
uploads/*
receipts/*
__pycache__/
*.pyc
*.pyo
*.db
*.log
.DS_Store
*.csv
!.gitkeep
EOF
fi

# Create gitkeep files to preserve directories
touch uploads/.gitkeep
touch receipts/.gitkeep

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review and update .env file with your settings"
echo "2. Install Python dependencies: pip install -r requirements.txt"
echo "3. Run the application: python app.py"
echo ""
echo "Default login credentials:"
echo "  Admin: admin / admin123"
echo "  User 1: john / password"
echo "  User 2: jane / password"
echo ""
echo "⚠️  IMPORTANT: Change default passwords after first login!"
echo ""