import sqlite3
import os

DB_FOLDER = "database"
DB_PATH = os.path.join(DB_FOLDER, "app.db")

os.makedirs(DB_FOLDER, exist_ok=True)

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    quantity_sold INTEGER NOT NULL,
    total_price REAL NOT NULL,
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books (id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS purchase_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    quantity_ordered INTEGER NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL
)
""")

# SAFELY ADD supplier_id COLUMN TO EXISTING purchase_orders TABLE IF IT DOES NOT EXIST
cursor.execute("PRAGMA table_info(purchase_orders)")
purchase_order_columns = [column[1] for column in cursor.fetchall()]

if "supplier_id" not in purchase_order_columns:
    cursor.execute("ALTER TABLE purchase_orders ADD COLUMN supplier_id INTEGER")

# SAFELY ADD NEW SALES TAX COLUMNS TO EXISTING sales TABLE IF THEY DO NOT EXIST
cursor.execute("PRAGMA table_info(sales)")
sales_columns = [column[1] for column in cursor.fetchall()]

if "state" not in sales_columns:
    cursor.execute("ALTER TABLE sales ADD COLUMN state TEXT")

if "subtotal" not in sales_columns:
    cursor.execute("ALTER TABLE sales ADD COLUMN subtotal REAL DEFAULT 0")

if "tax_rate" not in sales_columns:
    cursor.execute("ALTER TABLE sales ADD COLUMN tax_rate REAL DEFAULT 0")

if "tax_amount" not in sales_columns:
    cursor.execute("ALTER TABLE sales ADD COLUMN tax_amount REAL DEFAULT 0")

if "final_total" not in sales_columns:
    cursor.execute("ALTER TABLE sales ADD COLUMN final_total REAL DEFAULT 0")

connection.commit()
connection.close()

print("Database initialized successfully.")