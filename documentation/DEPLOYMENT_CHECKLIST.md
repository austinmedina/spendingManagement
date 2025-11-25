# Deployment Checklist

## Pre-Deployment

### ✅ File Structure
- [ ] All files from artifacts created
- [ ] Directory structure matches layout
- [ ] `__init__.py` files in services/, routes/, utils/
- [ ] Templates directory with all HTML files
- [ ] CSV files initialized

### ✅ Configuration
- [ ] `.env` file created and configured
- [ ] `SECRET_KEY` changed from default
- [ ] SMTP settings configured (if using email)
- [ ] Azure credentials added (if using receipt scanning)
- [ ] Notification thresholds set

### ✅ Dependencies
- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] `requirements.txt` installed
- [ ] All imports successful

### ✅ Security
- [ ] Default passwords documented to change
- [ ] Admin password plan in place
- [ ] `.gitignore` includes sensitive files
- [ ] File permissions correct (644 for .csv, 600 for .env)

## Deployment Steps

### 1. Initial Setup
```bash
# Run setup script
chmod +x setup.sh
./setup.sh

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Edit .env
nano .env

# Set at minimum:
# - SECRET_KEY (generate new random key)
# - Change USE_CSV to false if using PostgreSQL

# Test configuration
python -c "from config import Config; print('Config OK')"
```

### 3. Test Run
```bash
# Start application
python app.py

# Should see:
# * Running on http://0.0.0.0:5000
# * Debug mode: on

# Open browser to http://localhost:5000
# Login with: admin / admin123
```

### 4. Verify Features
- [ ] Login works
- [ ] Dashboard loads
- [ ] Notifications bell appears
- [ ] Can create manual transaction
- [ ] Can create budget
- [ ] Can create recurring transaction
- [ ] Can create group
- [ ] Admin panel accessible
- [ ] Search works

### 5. Change Default Passwords
```bash
# Login as each user and change password:
# 1. Login as admin
# 2. Will be prompted to change password
# 3. Change to strong password
# 4. Repeat for john and jane
```

### 6. Production Deployment (Raspberry Pi)
```bash
# Create systemd service
sudo nano /etc/systemd/system/receipt-tracker.service

# Add service configuration (see README)

# Enable and start
sudo systemctl enable receipt-tracker
sudo systemctl start receipt-tracker

# Check status
sudo systemctl status receipt-tracker

# View logs
sudo journalctl -u receipt-tracker -f
```

## Post-Deployment

### ✅ Verification
- [ ] Service starts on boot
- [ ] Accessible from network
- [ ] SSL/HTTPS configured (if applicable)
- [ ] Backups scheduled
- [ ] Monitoring configured

### ✅ User Setup
- [ ] Admin accounts created
- [ ] Regular user accounts created
- [ ] Groups configured
- [ ] Accounts (bank accounts) created
- [ ] Initial budgets set

### ✅ Documentation
- [ ] Users trained on system
- [ ] Admin procedures documented
- [ ] Backup procedures documented
- [ ] Support contacts listed

## File Checklist

### Core Application Files
- [ ] `app.py` - Main application
- [ ] `config.py` - Configuration
- [ ] `models.py` - Data models
- [ ] `auth.py` - Authentication (from original)
- [ ] `requirements.txt` - Dependencies
- [ ] `setup.sh` - Setup script
- [ ] `.env` - Configuration (create from template)
- [ ] `.gitignore` - Git exclusions

### Services Directory
- [ ] `services/__init__.py`
- [ ] `services/azure_service.py`
- [ ] `services/notification_service.py`
- [ ] `services/analytics_service.py`
- [ ] `services/recurring_processor.py`

### Routes Directory
- [ ] `routes/__init__.py`
- [ ] `routes/main.py`
- [ ] `routes/api.py`
- [ ] `routes/transactions.py`
- [ ] `routes/budgets.py`
- [ ] `routes/recurring.py`
- [ ] `routes/accounts.py`
- [ ] `routes/groups.py`
- [ ] `routes/admin.py`

### Utils Directory
- [ ] `utils/__init__.py`
- [ ] `utils/helpers.py`
- [ ] `utils/decorators.py`

### Templates Directory (from original)
- [ ] `templates/base.html`
- [ ] `templates/dashboard_enhanced.html` (NEW)
- [ ] `templates/login.html`
- [ ] `templates/change_password.html`
- [ ] `templates/forgot_password.html`
- [ ] `templates/reset_password.html`
- [ ] `templates/upload.html`
- [ ] `templates/manual.html`
- [ ] `templates/search.html`
- [ ] `templates/budgets.html`
- [ ] `templates/recurring.html`
- [ ] `templates/accounts.html`
- [ ] `templates/groups.html`
- [ ] `templates/admin.html`

### Data Files (auto-created)
- [ ] `database.csv`
- [ ] `budgets.csv`
- [ ] `recurring.csv`
- [ ] `accounts.csv`
- [ ] `groups.csv`
- [ ] `splits.csv`
- [ ] `notifications.csv` (NEW)
- [ ] `users.csv`
- [ ] `reset_codes.csv`

## Quick Commands

### Development
```bash
# Activate venv
source venv/bin/activate

# Run application
python app.py

# Check logs
tail -f app.log
```

### Production
```bash
# Start service
sudo systemctl start receipt-tracker

# Stop service
sudo systemctl stop receipt-tracker

# Restart service
sudo systemctl restart receipt-tracker

# View logs
sudo journalctl -u receipt-tracker -f

# Check status
sudo systemctl status receipt-tracker
```

### Maintenance
```bash
# Backup data
tar -czf backup-$(date +%Y%m%d).tar.gz *.csv .env

# Update code
git pull
sudo systemctl restart receipt-tracker

# Update dependencies
pip install --upgrade -r requirements.txt
sudo systemctl restart receipt-tracker
```

## Troubleshooting

### Application Won't Start
```bash
# Check Python version
python --version  # Should be 3.8+

# Check virtual environment
which python  # Should show venv path

# Check dependencies
pip list | grep -i flask

# Check for errors
python app.py  # Look for import errors
```

### ImportError
```bash
# Ensure __init__.py files exist
find . -name "__init__.py"

# Should show:
# ./services/__init__.py
# ./routes/__init__.py
# ./utils/__init__.py

# If missing, create them
touch services/__init__.py routes/__init__.py utils/__init__.py
```

### ModuleNotFoundError
```bash
# Install missing module
pip install module-name

# Or reinstall all
pip install -r requirements.txt
```

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>

# Or use different port in app.py
# app.run(host='0.0.0.0', port=5001)
```

## Success Criteria

### ✅ Application Running
- Application starts without errors
- Accessible at configured URL
- No error messages in logs

### ✅ Core Features Working
- User login successful
- Dashboard displays
- Notifications appear
- Can create transactions
- Can upload receipts
- Can manage budgets

### ✅ Notifications Working
- Budget alerts trigger correctly
- Recurring reminders appear
- Bell icon shows unread count
- Email notifications sent (if enabled)

### ✅ Performance
- Dashboard loads in < 3 seconds
- API responses in < 1 second
- No memory leaks
- Stable for 24+ hours

## Support Resources

### Documentation
- README.md - Full documentation
- IMPLEMENTATION_GUIDE.md - Technical guide
- Code comments - Inline documentation

### Logs
- `app.log` - Application logs
- `journalctl` - System logs (production)
- Browser console - Frontend errors

### Contacts
- GitHub Issues - Bug reports
- Email - Direct support
- Documentation - First reference

---

**Last Updated**: 2025
**Version**: 2.0.0