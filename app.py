"""
Receipt Tracker - Main Application
Modular Flask application with authentication and notifications
"""

import os
from flask import Flask
from config import get_config, Config
from auth import init_users, get_current_user, is_admin

# Create Flask app
app = Flask(__name__)
config_obj = get_config(os.getenv('FLASK_ENV', 'development'))
app.config.from_object(config_obj)

# Ensure directories exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.RECEIPT_FOLDER, exist_ok=True)

# Initialize authentication
init_users()

# Initialize CSV files (models will create them if they don't exist)
from models import (
    TransactionModel, BudgetModel, RecurringModel, 
    AccountModel, GroupModel, SplitModel, NotificationModel
)

# Initialize all models (creates CSV files if needed)
TransactionModel()
BudgetModel()
RecurringModel()
AccountModel()
GroupModel()
SplitModel()
NotificationModel()

# Register blueprints
from routes import (
    main_bp, api_bp, transactions_bp, budgets_bp,
    recurring_bp, accounts_bp, groups_bp, admin_bp
)

app.register_blueprint(main_bp)
app.register_blueprint(api_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(budgets_bp)
app.register_blueprint(recurring_bp)
app.register_blueprint(accounts_bp)
app.register_blueprint(groups_bp)
app.register_blueprint(admin_bp)

# Context processor to inject current user into all templates
@app.context_processor
def inject_user():
    return dict(
        current_user=get_current_user(),
        is_admin=is_admin()
    )

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return "Page not found", 404

@app.errorhandler(500)
def internal_error(error):
    return "Internal server error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)