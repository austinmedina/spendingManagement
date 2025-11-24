# Authentication & User Management Guide

## Overview

Receipt Tracker now includes a complete authentication system with:
- Secure login/logout
- User and admin roles
- Password hashing (SHA-256)
- Session management
- Admin dashboard for user management

## Default Accounts

### On First Run
Three accounts are automatically created:

| Username | Password | Role | Full Name |
|----------|----------|------|-----------|
| `admin` | `admin123` | Administrator | Administrator |
| `john` | `password` | Regular User | John |
| `jane` | `password` | Regular User | Jane |

**⚠️ SECURITY: Change default passwords immediately after first login!**

## User Roles

### Regular User Permissions
✅ View personal dashboard
✅ Upload receipts
✅ Create transactions, budgets, accounts
✅ Join groups (admin assigns)
✅ View group shared expenses
✅ Set up recurring transactions
✅ Export transaction data

❌ Create other users
❌ View other users' personal data
❌ Access admin panel
❌ Manage groups they're not in

### Administrator Permissions
✅ **Everything regular users can do**, PLUS:
✅ Create new user accounts
✅ Reset any user's password
✅ Activate/deactivate accounts
✅ Grant/revoke admin privileges
✅ View all system users
✅ Manage all groups
✅ Access admin dashboard (`/admin`)

## Login Process

1. Navigate to `http://localhost:5000` or your Raspberry Pi's IP
2. You'll be redirected to `/login`
3. Enter username and password
4. Click "Sign In"
5. Upon success, redirected to dashboard

## For Administrators

### Accessing Admin Panel

1. Log in with admin account
2. Click **Settings** (gear icon) in navbar
3. Select **Admin Panel** (red text at bottom)
4. Admin dashboard opens at `/admin`

### Creating New Users

**Via Admin Panel:**
1. Go to `/admin`
2. Click "Create User"
3. Fill in:
   - Username (for login)
   - Full Name (display name)
   - Password
   - Check "Administrator privileges" if admin
4. Click "Save User"

**Important:**
- Usernames must be unique
- Full Name is what appears throughout the app
- New users are active by default

### Resetting Passwords

1. Go to `/admin`
2. Find user in table
3. Click pencil (edit) icon
4. Enter new password
5. Leave blank to keep existing
6. Click "Save User"

### Deactivating Users

1. Go to `/admin`
2. Find user in table
3. Click trash (delete) icon
4. Confirm deactivation
5. User can no longer log in
6. Their data remains in system

**Note:** You cannot delete your own account

### Granting Admin Rights

1. Go to `/admin`
2. Edit user
3. Check "Administrator privileges"
4. Save
5. User now has admin access

## For Regular Users

### First Login

1. Use credentials provided by admin
2. Log in at `/login`
3. Change your password:
   - No built-in profile page yet
   - Ask admin to reset your password
   - OR admin can give you temp password to change

### Setting Up Your Account

After login:
1. **Create Accounts** (`/accounts`)
   - Add your bank accounts
   - Add credit cards
   - Add payment methods

2. **Join Groups** (ask admin)
   - Admin adds you to expense groups
   - You'll see group transactions

3. **Set Budgets** (`/budgets`)
   - Create personal budget limits
   - Track your spending

4. **Add Recurring** (`/recurring`)
   - Set up automatic transactions
   - Like rent, subscriptions, salary

### Logging Out

Click your name (top right) → "Logout"

## Security Features

### Password Hashing
- Passwords stored as SHA-256 hashes
- Never stored in plain text
- Cannot be recovered (only reset)

### Session Management
- Flask sessions with secure cookies
- Auto-logout on browser close
- Server-side session storage

### Route Protection
All app pages require login except:
- `/login` - Login page
- Static files (CSS, JS, receipts)

Admin pages additionally require admin role:
- `/admin` - Admin dashboard
- `/api/admin/*` - Admin API endpoints

## Data Privacy

### What Each User Sees

**Personal Data (only you):**
- Your own transactions
- Your budgets
- Your bank accounts
- Your recurring transactions

**Shared Data (you + group):**
- Group transactions
- Split amounts
- Group members
- Shared expenses

**Hidden from You:**
- Other users' personal transactions
- Other users' budgets
- Other users' accounts
- Groups you're not in

### What Admins See

Admins see:
- All user accounts
- All groups and members
- System statistics
- User active/inactive status

Admins do NOT automatically see:
- Users' transaction data
- Users' budget details
- Users' actual spending

*Admins only see spending data if they're in the same group*

## Common Scenarios

### Scenario 1: New Household Member

**Admin actions:**
1. Create account: username `mike`, password `temp123`
2. Add Mike to "Household" group
3. Tell Mike his credentials

**Mike's actions:**
1. Login with `mike` / `temp123`
2. Ask admin to reset password (change from temp)
3. Add personal bank accounts
4. Start uploading receipts

### Scenario 2: Roommate Moves Out

**Admin actions:**
1. Go to `/admin`
2. Edit "Apartment" group
3. Remove departing roommate from members
4. Optionally deactivate their account
5. Past shared expenses remain

### Scenario 3: Multiple Families

**Setup:**
- Family 1: Group "Smith Family" (John, Jane, Kids)
- Family 2: Group "Jones Family" (Alice, Bob)
- Admin manages both

**Result:**
- Smith family only sees their data
- Jones family only sees their data
- No cross-visibility
- Admin can manage both groups

### Scenario 4: Forgot Password

**Solution:**
1. Contact admin
2. Admin goes to `/admin`
3. Admin edits user
4. Admin sets temporary password
5. Admin tells user new temp password
6. User logs in and should change it

## Best Practices

### For Admins

1. **Change default admin password immediately**
2. Use strong, unique passwords for admin account
3. Only grant admin rights when necessary
4. Regularly review active users
5. Deactivate accounts for departed members
6. Keep a backup admin account
7. Document who has access to what

### For Users

1. **Don't share passwords**
2. Log out on shared devices
3. Use unique password (not reused elsewhere)
4. Report suspicious activity to admin
5. Keep account info current

### For System

1. **Keep SECRET_KEY secure in .env**
2. Use HTTPS in production
3. Regular backups of user data
4. Monitor login attempts (future feature)
5. Consider 2FA for production (future)

## File Structure

### Authentication Files

```
auth.py          # Authentication module
users.csv        # User accounts (CSV mode)
app.py           # Includes login/logout routes
```

### CSV Schema

**users.csv:**
```
id,username,password_hash,full_name,is_admin,active
1,admin,<hash>,Administrator,true,true
2,john,<hash>,John,false,true
```

## Troubleshooting

### Can't Login

**Problem:** "Invalid username or password"

**Solutions:**
- Check username spelling
- Check password (case-sensitive)
- Ask admin if account is active
- Request password reset

### Redirected to Login

**Problem:** Accessing page redirects to login

**Cause:** Not logged in or session expired

**Solution:** Log in again

### No Admin Panel Link

**Problem:** Can't find Admin Panel in Settings

**Cause:** Not logged in as admin

**Solution:**
- Log out
- Log in with admin account
- Link appears in Settings dropdown

### Changes Don't Persist

**Problem:** Login but can't access features

**Possible causes:**
- Account is inactive (contact admin)
- Session issue (try logout/login)
- Browser cache (clear cookies)

## API Endpoints

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET/POST | `/login` | None | Login page |
| GET | `/logout` | User | Logout |

### Admin API

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/admin/users` | Admin | List all users |
| POST | `/api/admin/users` | Admin | Create user |
| PUT | `/api/admin/users/<id>` | Admin | Update user |
| DELETE | `/api/admin/users/<id>` | Admin | Deactivate user |
| POST | `/api/admin/groups/assign` | Admin | Assign group members |

## Future Enhancements

Potential additions:
- Password complexity requirements
- Password reset via email
- Two-factor authentication (2FA)
- Login attempt limiting
- Account lockout after failed attempts
- Password change page for users
- User profile page
- Activity logs
- Email notifications
- OAuth integration (Google, Microsoft)

## Security Checklist

Before deploying to production:

- [ ] Change default admin password
- [ ] Update SECRET_KEY in .env
- [ ] Enable HTTPS
- [ ] Set secure session cookies
- [ ] Implement rate limiting
- [ ] Add password complexity rules
- [ ] Regular backup schedule
- [ ] Monitor logs
- [ ] Document admin procedures
- [ ] Train users on security
