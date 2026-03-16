import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import os

books_bp = Blueprint("books", __name__)

DB_PATH = os.path.join("database", "app.db")


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@books_bp.route("/books")
def list_books():
    connection = get_connection()
    books = connection.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
    connection.close()
    return render_template("inventory.html", books=books)


@books_bp.route("/books/add", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        isbn = request.form["isbn"]
        title = request.form["title"]
        author = request.form["author"]
        price = request.form["price"]
        quantity = request.form["quantity"]

        connection = get_connection()
        connection.execute(
            "INSERT INTO books (isbn, title, author, price, quantity) VALUES (?, ?, ?, ?, ?)",
            (isbn, title, author, price, quantity)
        )
        connection.commit()
        connection.close()

        return redirect(url_for("books.list_books"))

    return render_template("add_book.html")


@books_bp.route("/books/update/<int:book_id>", methods=["POST"])
def update_book_quantity(book_id):
    new_quantity = request.form["quantity"]

    connection = get_connection()
    connection.execute(
        "UPDATE books SET quantity = ? WHERE id = ?",
        (new_quantity, book_id)
    )
    connection.commit()
    connection.close()

    return redirect(url_for("books.list_books"))


@books_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    connection = get_connection()

    if request.method == "POST":
        book_id = request.form["book_id"]
        quantity_sold = int(request.form["quantity_sold"])

        book = connection.execute(
            "SELECT * FROM books WHERE id = ?",
            (book_id,)
        ).fetchone()

        if book is None:
            connection.close()
            return "Book not found."

        if quantity_sold <= 0:
            connection.close()
            return "Quantity must be greater than 0."

        if book["quantity"] < quantity_sold:
            connection.close()
            return "Not enough stock available."

        new_quantity = book["quantity"] - quantity_sold
        total_price = float(book["price"]) * quantity_sold

        connection.execute(
            "UPDATE books SET quantity = ? WHERE id = ?",
            (new_quantity, book_id)
        )

        connection.execute(
            "INSERT INTO sales (book_id, title, quantity_sold, total_price) VALUES (?, ?, ?, ?)",
            (book["id"], book["title"], quantity_sold, total_price)
        )

        connection.commit()
        connection.close()

        return redirect(url_for("books.sales_history"))

    books = connection.execute("SELECT * FROM books ORDER BY title ASC").fetchall()
    connection.close()
    return render_template("checkout.html", books=books)


@books_bp.route("/sales")
def sales_history():
    connection = get_connection()
    sales = connection.execute(
        "SELECT * FROM sales ORDER BY sale_date DESC, id DESC"
    ).fetchall()
    connection.close()
    return render_template("sales.html", sales=sales)


@books_bp.route("/api/books")
def api_books():
    connection = get_connection()
    books = connection.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
    connection.close()

    return jsonify([
        {
            "id": book["id"],
            "isbn": book["isbn"],
            "title": book["title"],
            "author": book["author"],
            "price": book["price"],
            "quantity": book["quantity"],
            "low_stock": book["quantity"] < 5
        }
        for book in books
    ])


@books_bp.route("/api/sales")
def api_sales():
    connection = get_connection()
    sales = connection.execute(
        "SELECT * FROM sales ORDER BY sale_date DESC, id DESC"
    ).fetchall()
    connection.close()

    return jsonify([
        {
            "id": sale["id"],
            "book_id": sale["book_id"],
            "title": sale["title"],
            "quantity_sold": sale["quantity_sold"],
            "total_price": sale["total_price"],
            "sale_date": sale["sale_date"]
        }
        for sale in sales
    ])