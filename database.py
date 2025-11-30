"""
Database module for PostgreSQL integration
Replace CSV functions in app.py with these for production
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('DB_NAME', 'receipt_tracker'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

@contextmanager
def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    """Initialize all database tables"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Transactions table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    item_name VARCHAR(255) NOT NULL,
                    category VARCHAR(100) DEFAULT 'Other',
                    store VARCHAR(255),
                    date DATE NOT NULL,
                    price DECIMAL(10, 2) NOT NULL,
                    person VARCHAR(100),
                    bank_account_id VARCHAR(100),
                    type VARCHAR(20) DEFAULT 'expense',
                    receipt_image VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(date);
                CREATE INDEX IF NOT EXISTS idx_trans_category ON transactions(category);
                CREATE INDEX IF NOT EXISTS idx_trans_type ON transactions(type);
            ''')
            
            # Budgets table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id SERIAL PRIMARY KEY,
                    category VARCHAR(100) NOT NULL,
                    amount DECIMAL(10, 2) NOT NULL,
                    period VARCHAR(20) DEFAULT 'monthly',
                    start_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Recurring transactions table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS recurring (
                    id SERIAL PRIMARY KEY,
                    item_name VARCHAR(255) NOT NULL,
                    category VARCHAR(100) DEFAULT 'Other',
                    store VARCHAR(255),
                    price DECIMAL(10, 2) NOT NULL,
                    person VARCHAR(100),
                    bank_account_id VARCHAR(100),
                    type VARCHAR(20) DEFAULT 'expense',
                    frequency VARCHAR(20) DEFAULT 'monthly',
                    next_date DATE NOT NULL,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')

# Transaction functions
def read_all_transactions():
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT id, item_name, category, store, 
                       TO_CHAR(date, 'YYYY-MM-DD') as date,
                       price::text, person, bank_account_id, type, receipt_image
                FROM transactions ORDER BY date DESC
            ''')
            return cur.fetchall()

def write_transaction(t):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO transactions (item_name, category, store, date, price, person, bank_account_id, type, receipt_image)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (t['item_name'], t.get('category', 'Other'), t.get('store', ''), t['date'],
                  t['price'], t.get('person', ''), t.get('bank_account_id', ''), t.get('type', 'expense'), t.get('receipt_image', '')))
            return cur.fetchone()[0]

def get_transactions_filtered(filters):
    query = '''SELECT id, item_name, category, store, TO_CHAR(date, 'YYYY-MM-DD') as date,
               price::text, person, bank_account_id, type, receipt_image FROM transactions WHERE 1=1'''
    params = []
    
    if filters.get('category'):
        query += ' AND LOWER(category) = LOWER(%s)'; params.append(filters['category'])
    if filters.get('store'):
        query += ' AND LOWER(store) LIKE LOWER(%s)'; params.append(f"%{filters['store']}%")
    if filters.get('person'):
        query += ' AND LOWER(person) = LOWER(%s)'; params.append(filters['person'])
    if filters.get('bank_account_id'):
        query += ' AND LOWER(bank_account_id) = LOWER(%s)'; params.append(filters['bank_account_id'])
    if filters.get('start_date'):
        query += ' AND date >= %s'; params.append(filters['start_date'])
    if filters.get('end_date'):
        query += ' AND date <= %s'; params.append(filters['end_date'])
    if filters.get('q'):
        query += ' AND (LOWER(item_name) LIKE LOWER(%s) OR LOWER(store) LIKE LOWER(%s))'
        params.extend([f"%{filters['q']}%", f"%{filters['q']}%"])
    if filters.get('type'):
        query += ' AND type = %s'; params.append(filters['type'])
    
    query += ' ORDER BY date DESC'
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()

# Budget functions
def read_all_budgets():
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT id, category, amount::text, period, TO_CHAR(start_date, \'YYYY-MM-DD\') as start_date FROM budgets')
            return cur.fetchall()

def write_budget(b):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO budgets (category, amount, period, start_date) VALUES (%s, %s, %s, %s) RETURNING id',
                       (b['category'], b['amount'], b.get('period', 'monthly'), b.get('start_date')))
            return cur.fetchone()[0]

def update_budget(bid, b):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE budgets SET category=%s, amount=%s, period=%s WHERE id=%s',
                       (b['category'], b['amount'], b.get('period', 'monthly'), bid))

def delete_budget(bid):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM budgets WHERE id=%s', (bid,))

# Recurring functions
def read_all_recurring():
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''SELECT id, item_name, category, store, price::text, person, bank_account_id,
                          type, frequency, TO_CHAR(next_date, 'YYYY-MM-DD') as next_date,
                          CASE WHEN active THEN 'true' ELSE 'false' END as active FROM recurring''')
            return cur.fetchall()

def write_recurring(r):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute('''INSERT INTO recurring (item_name, category, store, price, person, bank_account_id, type, frequency, next_date, active)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE) RETURNING id''',
                       (r['item_name'], r.get('category', 'Other'), r.get('store', ''), r['price'],
                        r.get('person', ''), r.get('bank_account_id', ''), r.get('type', 'expense'), r.get('frequency', 'monthly'), r['next_date']))
            return cur.fetchone()[0]

def update_recurring_next_date(rid, next_date):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE recurring SET next_date=%s WHERE id=%s', (next_date, rid))

def toggle_recurring(rid):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE recurring SET active = NOT active WHERE id=%s', (rid,))

def delete_recurring(rid):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM recurring WHERE id=%s', (rid,))

def get_unique_values(column):
    valid = ['category', 'bank_account_id', 'person', 'store']
    if column not in valid:
        raise ValueError(f"Invalid column: {column}")
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f'SELECT DISTINCT {column} FROM transactions WHERE {column} IS NOT NULL AND {column} != \'\' ORDER BY {column}')
            return [row[0] for row in cur.fetchall()]
