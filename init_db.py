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

connection.commit()
connection.close()

print("Database initialized successfully.")