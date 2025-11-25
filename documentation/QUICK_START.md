# Quick Start Guide

Get Receipt Tracker running in 5 minutes!

## 🚀 Installation (5 Steps)

### Step 1: Download Files (1 min)

Place all files from artifacts in your project directory:

```
receipt-tracker/
├── app.py
├── config.py
├── models.py
├── auth.py (keep your existing file)
├── requirements.txt
├── setup.sh
├── services/
│   ├── __init__.py
│   ├── azure_service.py
│   ├── notification_service.py
│   ├── analytics_service.py
│   └── recurring_processor.py
├── routes/
│   ├── __init__.py
│   ├── main.py
│   ├── api.py
│   ├── transactions.py
│   ├── budgets.py
│   ├── recurring.py
│   ├── accounts.py
│   ├── groups.py
│   └── admin.py
├── utils/
│   ├── __init__.py
│   ├── helpers.py
│   └── decorators.py
└── templates/ (keep your existing templates, add dashboard_enhanced.html)
```

### Step 2: Run Setup (1 min)

```bash
chmod +x setup.sh
./setup.sh
```

This creates all necessary directories and CSV files.

### Step 3: Install Dependencies (1 min)

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Configure (1 min)

Edit `.env` file (created by setup.sh):

```env
SECRET_KEY=my-super-secret-random-key-12345
USE_CSV=true
ENABLE_EMAIL_NOTIFICATIONS=false
```

**Minimum required: Just set `SECRET_KEY` to any random string!**

### Step 5: Run (1 min)

```bash
python app.py
```

Open browser: `http://localhost:5000`

Login: `admin` / `admin123`

**Done! 🎉**

---

## 📝 What You Get

### Immediate Features
✅ Enhanced dashboard with analytics
✅ Notification system
✅ Budget alerts
✅ Recurring reminders
✅ Spending insights
✅ Month-end predictions
✅ Spending patterns

### New UI Elements
- 🔔 Notification bell (top right)
- 📊 Enhanced dashboard with insights
- 📈 Spending trends graphs
- 💡 Actionable recommendations
- 🎯 Month-end projections

---

## 🎯 First Steps After Installation

### 1. Change Passwords (Required)
```
Login → Will prompt to change password
```

### 2. Create Your First Transaction
```
Manual → Fill form → Save
```

### 3. Set a Budget
```
Budgets → Add Budget → Set limit → Save
```

### 4. See Your First Notification
```
Dashboard → Bell icon → View notification
```

---

## 🔧 Optional: Enable Email Notifications

Edit `.env`:
```env
ENABLE_EMAIL_NOTIFICATIONS=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

For Gmail App Password:
1. Google Account → Security
2. 2-Factor Authentication → Enable
3. App Passwords → Generate
4. Copy 16-character password to `.env`

---

## 📱 Access from Other Devices

Find your computer's IP:
```bash
# Linux/Mac
hostname -I

# Windows
ipconfig
```

Access from phone/tablet:
```
http://YOUR-IP:5000
```

Example: `http://192.168.1.100:5000`

---

## 🐛 Common Issues

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Port already in use"
```bash
# Kill process
lsof -i :5000
kill -9 <PID>

# Or change port in app.py
app.run(port=5001)
```

### "No such file or directory"
```bash
# Run setup script
./setup.sh
```

### Templates not found
```bash
# Keep your existing templates folder
# Only add dashboard_enhanced.html
cp dashboard_enhanced.html templates/
```

---

## 📚 Next Steps

1. **Explore Dashboard** - See new analytics features
2. **Set Budgets** - Get automatic alerts
3. **Create Recurring** - Auto-generate transactions
4. **Try Notifications** - Upload receipt or exceed budget
5. **Read Full Docs** - Check README.md for details

---

## 💡 Pro Tips

### Tip 1: Use Groups for Shared Expenses
```
Groups → Create Group → Add members → Use in transactions
```

### Tip 2: Set Budget Thresholds
```env
BUDGET_WARNING_THRESHOLD=0.70  # Alert at 70%
BUDGET_CRITICAL_THRESHOLD=0.85  # Critical at 85%
```

### Tip 3: Daily Check-ins
- Check notification bell daily
- Review dashboard insights weekly
- Adjust budgets monthly

### Tip 4: Export Data
```
Search → Filter transactions → Export CSV
```

---

## 🎓 Learning Path

### Day 1: Basics
- [ ] Login and change password
- [ ] Create manual transaction
- [ ] View dashboard
- [ ] Check notifications

### Day 2: Advanced
- [ ] Set budgets
- [ ] Create recurring transaction
- [ ] Upload receipt (if Azure configured)
- [ ] Create group

### Day 3: Master
- [ ] Analyze spending patterns
- [ ] Review insights
- [ ] Export data
- [ ] Configure email notifications

---

## 📞 Get Help

### Check These First:
1. Browser console (F12)
2. Terminal output
3. `app.log` file
4. README.md troubleshooting section

### Still Stuck?
- GitHub Issues
- Review DEPLOYMENT_CHECKLIST.md
- Check IMPLEMENTATION_GUIDE.md

---

## ✅ Success Checklist

- [ ] Application starts without errors
- [ ] Can login successfully
- [ ] Dashboard displays with charts
- [ ] Notification bell appears
- [ ] Can create transaction
- [ ] Can create budget
- [ ] Notifications appear when budget threshold reached
- [ ] Can view spending insights

**If all checked, you're ready to go! 🚀**

---

## 📖 Full Documentation

For complete features and configuration:
- **README.md** - Full documentation
- **IMPLEMENTATION_GUIDE.md** - Technical details
- **DEPLOYMENT_CHECKLIST.md** - Production deployment

---

**Version**: 2.0.0
**Time to Deploy**: ~5 minutes
**Difficulty**: Easy