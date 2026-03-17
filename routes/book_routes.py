import sqlite3
import os
from flask import Blueprint, render_template, request, redirect, url_for, jsonify

books_bp = Blueprint("books", __name__)

DB_PATH = os.path.join("database", "app.db")


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@books_bp.route("/books")
def list_books():
    connection = get_connection()
    books = connection.execute(
        "SELECT * FROM books ORDER BY id DESC"
    ).fetchall()
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


@books_bp.route("/low-stock")
def low_stock():
    connection = get_connection()
    books = connection.execute(
        "SELECT * FROM books WHERE quantity < 5 ORDER BY quantity ASC"
    ).fetchall()
    connection.close()

    return render_template("low_stock.html", books=books)


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

        if new_quantity < 5:
            reorder_amount = 10
            connection.execute(
                "INSERT INTO purchase_orders (book_id, title, quantity_ordered) VALUES (?, ?, ?)",
                (book["id"], book["title"], reorder_amount)
            )

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

    books = connection.execute(
        "SELECT * FROM books ORDER BY title ASC"
    ).fetchall()
    connection.close()

    return render_template("checkout.html", books=books)


@books_bp.route("/sales")
def sales_history():
    connection = get_connection()
    sales = connection.execute(
        "SELECT * FROM sales ORDER BY sale_date DESC"
    ).fetchall()
    connection.close()

    return render_template("sales.html", sales=sales)


@books_bp.route("/purchase-orders")
def purchase_orders():
    connection = get_connection()
    orders = connection.execute(
        "SELECT * FROM purchase_orders ORDER BY order_date DESC"
    ).fetchall()
    connection.close()

    return render_template("purchase_orders.html", orders=orders)


@books_bp.route("/dashboard")
def dashboard():
    connection = get_connection()

    total_sales = connection.execute(
        "SELECT COUNT(*) AS count FROM sales"
    ).fetchone()["count"]

    total_books_sold = connection.execute(
        "SELECT COALESCE(SUM(quantity_sold), 0) AS total FROM sales"
    ).fetchone()["total"]

    total_revenue = connection.execute(
        "SELECT COALESCE(SUM(total_price), 0) AS revenue FROM sales"
    ).fetchone()["revenue"]

    top_book = connection.execute(
        """
        SELECT title, SUM(quantity_sold) AS total_sold
        FROM sales
        GROUP BY title
        ORDER BY total_sold DESC
        LIMIT 1
        """
    ).fetchone()

    sales_by_title = connection.execute(
        """
        SELECT title, SUM(quantity_sold) AS total_sold
        FROM sales
        GROUP BY title
        ORDER BY total_sold DESC
        """
    ).fetchall()

    connection.close()

    max_sold = 0
    if sales_by_title:
        max_sold = max(row["total_sold"] for row in sales_by_title)

    chart_data = []
    for row in sales_by_title:
        width_percent = 0
        if max_sold > 0:
            width_percent = int((row["total_sold"] / max_sold) * 100)

        chart_data.append({
            "title": row["title"],
            "total_sold": row["total_sold"],
            "width_percent": width_percent
        })

    return render_template(
        "dashboard.html",
        total_sales=total_sales,
        total_books_sold=total_books_sold,
        total_revenue=total_revenue,
        top_book=top_book,
        chart_data=chart_data
    )


@books_bp.route("/api/books")
def api_books():
    connection = get_connection()
    books = connection.execute(
        "SELECT * FROM books ORDER BY id DESC"
    ).fetchall()
    connection.close()

    return jsonify([dict(book) for book in books])


@books_bp.route("/api/sales")
def api_sales():
    connection = get_connection()
    sales = connection.execute(
        "SELECT * FROM sales ORDER BY sale_date DESC"
    ).fetchall()
    connection.close()

    return jsonify([dict(sale) for sale in sales])