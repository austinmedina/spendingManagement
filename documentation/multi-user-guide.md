# Multi-User & Group Features Guide

## Overview

The Receipt Tracker now supports multiple people and expense sharing groups, allowing you to:
- Track expenses for multiple people in your household
- Create groups for shared expenses (family, roommates, etc.)
- Automatically split transaction costs among group members
- Filter the dashboard by person to see individual spending
- Manage separate bank accounts for each person

## Core Concepts

### 1. People
- Each transaction is associated with a person
- Dashboard can be filtered to show any person's view
- Current person is shown in the navbar (top right)
- Each person only sees transactions they own or are part of through groups

### 2. Accounts
- Bank accounts, credit cards, and payment methods
- Each account belongs to a specific person
- Types: Checking, Savings, Credit Card, Cash, Other
- Manage at: `/accounts`

### 3. Groups
- Collections of people who share expenses
- Examples: "Household" (John + Jane), "Roommates" (Alice + Bob + Carol)
- Each transaction can optionally be assigned to a group
- When assigned to a group, costs can be split among members
- Manage at: `/groups`

### 4. Splits
- Automatic cost splitting among group members
- Define percentage each person owes
- Default is equal split (e.g., 50/50 for 2 people)
- Each person sees only their share in their dashboard

## How It Works

### Creating a Group

1. Go to `/groups`
2. Click "Create Group"
3. Enter group name (e.g., "Household")
4. Add members (you're automatically included)
5. Save

Example: Create "Household" group with members John and Jane

### Adding a Shared Expense

#### Via Receipt Upload (`/upload`)
1. Upload receipt image
2. Review extracted items
3. Select **Group** (e.g., "Household")
4. Choose who **Paid By** (who actually paid)
5. System auto-calculates 50/50 split for John and Jane
6. Adjust percentages if needed
7. Save

#### Via Manual Entry (`/manual`)
1. Select "Expense" tab
2. Fill in details
3. Select **Group** (e.g., "Household")
4. Choose who **Paid By**
5. Adjust split percentages if needed
6. Save

### How Splits Affect Dashboards

**Example:** $100 grocery bill, Household group (John + Jane), 50/50 split, paid by John

**John's Dashboard View:**
- Shows $50 expense (his share)
- Total expenses include $50

**Jane's Dashboard View:**
- Shows $50 expense (her share)
- Total expenses include $50

**Actual Transaction:**
- Full $100 is recorded
- John paid $100 from his account
- Split records show John owes $50, Jane owes $50

### Personal vs. Shared Expenses

**Personal Expense** (no group):
- Only appears in that person's dashboard
- Full amount counted for that person only

**Shared Expense** (with group):
- Appears in all group members' dashboards
- Each person sees only their split amount
- "Paid By" person's account shows the full transaction

## Use Cases

### Use Case 1: Household Partners
**Setup:**
- Group: "Household" (John, Jane)
- John's accounts: Chase Checking, Visa Credit
- Jane's accounts: Wells Fargo Checking, Amex

**Workflow:**
1. John buys $150 groceries → Group: Household, Paid By: John, 50/50 split
2. Jane pays $120 electric bill → Group: Household, Paid By: Jane, 50/50 split
3. John's personal $50 car wash → No group (personal expense)

**Result:**
- John's dashboard: $75 (groceries) + $60 (electric) + $50 (car wash) = $185
- Jane's dashboard: $75 (groceries) + $60 (electric) = $135

### Use Case 2: Roommates
**Setup:**
- Group: "Apartment" (Alice, Bob, Carol)
- Equal 33.33% split by default

**Workflow:**
1. Rent: $1800, Paid By: Alice, 33.33% each = $600/person
2. Internet: $90, Paid By: Bob, 33.33% each = $30/person
3. Alice's personal groceries: $80, No group = Alice only

**Result:**
- Each roommate sees $630 in shared expenses
- Alice additionally sees $80 personal expense

### Use Case 3: Mixed Arrangements
**Setup:**
- Group 1: "Household" (John, Jane)
- Group 2: "Roommates" (Alice, Bob)

**Benefits:**
- John only sees Household group expenses
- Alice only sees Roommates group expenses
- No cross-visibility between groups

## Dashboard Person Filter

**Top-right dropdown** allows filtering:
- Shows all people in your groups
- Select any person to view their spending
- Charts update to show selected person's data
- Useful for:
  - Parents tracking children's spending
  - Partners reviewing each other's budgets
  - Roommates checking individual contributions

## Budgets & Groups

- Budgets are **per person**, not per group
- Each person sets their own budget limits
- Dashboard shows budget progress for the filtered person
- Example: John sets $400 grocery budget, Jane sets $350 grocery budget

## Recurring Transactions & Groups

- Recurring transactions can be assigned to groups
- Auto-generates with splits on each occurrence
- Example: Monthly rent auto-splits 50/50 on the 1st

## Best Practices

### 1. Account Setup
- Create accounts for each person first
- Use descriptive names (e.g., "John - Chase Checking")

### 2. Group Naming
- Use clear names: "Household", "Apartment", "Family"
- Avoid generic names like "Group 1"

### 3. Split Percentages
- Adjust from default equal split if needed
- Income differences: 60/40 based on earnings
- Usage differences: 70/30 if one person uses more

### 4. Regular Reviews
- Check splits monthly
- Adjust percentages if circumstances change
- Use dashboard person filter to verify fairness

### 5. Communication
- Discuss large purchases before making them
- Review shared expenses together
- Use the search function to find specific transactions

## Data Privacy

- Each person sees:
  - ✅ Their personal transactions
  - ✅ Group transactions they're part of
  - ❌ Other people's personal transactions
  - ❌ Groups they're not a member of

## Technical Details

### CSV Files (Testing Mode)
```
accounts.csv    - Bank accounts with person ownership
groups.csv      - Groups and their members
splits.csv      - Transaction splits (amount per person)
```

### Session Management
- Current person stored in Flask session
- Switch person: Top-right navbar (future feature)
- Currently defaults to first person or "John"

### Database Schema (PostgreSQL)
When switching to PostgreSQL:
- `transactions` table includes `group_id`, `paid_by`
- `accounts` table includes `person` foreign key
- `groups` table stores member list
- `splits` table records per-person amounts
