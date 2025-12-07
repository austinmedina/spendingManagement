"""
Configuration module for Receipt Tracker
Centralized configuration management
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-in-production')
    
    # File Upload
    UPLOAD_FOLDER = 'uploads'
    RECEIPT_FOLDER = 'receipts'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    
    # Database
    USE_CSV = os.getenv('USE_CSV', 'true').lower() == 'true'
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'receipt_tracker')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # Azure Document Intelligence
    AZURE_ENDPOINT = os.getenv('AZURE_DOC_INTELLIGENCE_ENDPOINT', '')
    AZURE_KEY = os.getenv('AZURE_DOC_INTELLIGENCE_KEY', '')
    
    # Email (SMTP)
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_FROM = os.getenv('SMTP_FROM', SMTP_USERNAME)
    
    # Notifications
    ENABLE_EMAIL_NOTIFICATIONS = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'false').lower() == 'true'
    BUDGET_WARNING_THRESHOLD = float(os.getenv('BUDGET_WARNING_THRESHOLD', '0.75'))  # 75%
    BUDGET_CRITICAL_THRESHOLD = float(os.getenv('BUDGET_CRITICAL_THRESHOLD', '0.90'))  # 90%
    
    # Recurring Transaction Processing
    RECURRING_CHECK_HOUR = int(os.getenv('RECURRING_CHECK_HOUR', '6'))  # 6 AM
    
    # Categories
    EXPENSE_CATEGORIES = [
        'Rent', 'Electric', 'Investment', 'Car', 'Medical', 'Groceries',
        'Entertainment', 'Subscriptions', 'Household', 'Eating Out', 
        'Shopping', 'Other'
    ]
    
    INCOME_CATEGORIES = [
        'Salary', 'Freelance', 'Investment', 'Gift', 'Refund', 'Other'
    ]
    
    # CSV Files
    CSV_FILES = {
        'transactions': 'csv/database.csv',
        'budgets': 'csv/budgets.csv',
        'recurring': 'csv/recurring.csv',
        'accounts': 'csv/accounts.csv',
        'groups': 'csv/groups.csv',
        'splits': 'csv/splits.csv',
        'notifications': 'csv/notifications.csv'
    }
    
    CSV_HEADERS = {
        'transactions': ['id', 'item_name', 'category', 'store', 'date', 'price', 
                        'user_id', 'bank_account_id', 'type', 'receipt_image', 
                        'group_id', 'receipt_group_id'],
        'budgets': ['id', 'category', 'amount', 'period', 'start_date', 'user_id'],
        'recurring': ['id', 'item_name', 'category', 'store', 'price', 'user_id', 
                     'bank_account_id', 'type', 'frequency', 'next_date', 'active', 'group_id'],
        'accounts': ['id', 'name', 'type', 'user_id'],
        'groups': ['id', 'name', 'members'],
        'splits': ['id', 'receipt_group_id', 'user_id', 'amount', 'percentage'],
        'notifications': ['id', 'user_id', 'type', 'title', 'message', 'date', 'read', 'data'],
        'reset_code': ['code', 'user_id', 'expires', 'used']
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env='default'):
    """Get configuration by environment"""
    return config.get(env, config['default'])