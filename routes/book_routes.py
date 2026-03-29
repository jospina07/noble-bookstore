import sqlite3
import os
import csv
import io
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, Response, session

books_bp = Blueprint("books", __name__)

DB_PATH = os.path.join("database", "app.db")

STATE_TAX_RATES = {
    "AL": 0.04,
    "AK": 0.00,
    "AZ": 0.056,
    "AR": 0.065,
    "CA": 0.0725,
    "CO": 0.029,
    "CT": 0.0635,
    "DE": 0.00,
    "FL": 0.06,
    "GA": 0.04,
    "HI": 0.04,
    "ID": 0.06,
    "IL": 0.0625,
    "IN": 0.07,
    "IA": 0.06,
    "KS": 0.065,
    "KY": 0.06,
    "LA": 0.0445,
    "ME": 0.055,
    "MD": 0.06,
    "MA": 0.0625,
    "MI": 0.06,
    "MN": 0.06875,
    "MS": 0.07,
    "MO": 0.04225,
    "MT": 0.00,
    "NE": 0.055,
    "NV": 0.0685,
    "NH": 0.00,
    "NJ": 0.06625,
    "NM": 0.05125,
    "NY": 0.04,
    "NC": 0.0475,
    "ND": 0.05,
    "OH": 0.0575,
    "OK": 0.045,
    "OR": 0.00,
    "PA": 0.06,
    "RI": 0.07,
    "SC": 0.06,
    "SD": 0.042,
    "TN": 0.07,
    "TX": 0.0625,
    "UT": 0.061,
    "VT": 0.06,
    "VA": 0.053,
    "WA": 0.065,
    "WV": 0.06,
    "WI": 0.05,
    "WY": 0.04
}

USERS = {
    "admin": {"password": "password123", "role": "all_access"},
    "JOspina": {"password": "Jeff01", "role": "all_access"},
    "KPeek": {"password": "Kadysha01", "role": "all_access"},
    "CPowers": {"password": "Craig01", "role": "all_access"},
    "ROwens": {"password": "Ryan01", "role": "all_access"},
    "EBarrenos": {"password": "Enrique01", "role": "all_access"},
    "FAlmasri": {"password": "Fadi01", "role": "all_access"},

    "manager1": {"password": "Manager01", "role": "manager"},
    "employee1": {"password": "Employee01", "role": "employee"},
}


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def login_required(route_function):
    @wraps(route_function)
    def wrapped_route(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("books.login"))
        return route_function(*args, **kwargs)
    return wrapped_route


def role_required(allowed_roles):
    def decorator(route_function):
        @wraps(route_function)
        def wrapped_route(*args, **kwargs):
            if not session.get("logged_in"):
                return redirect(url_for("books.login"))

            user_role = session.get("role")
            if user_role not in allowed_roles:
                return "Access denied.", 403

            return route_function(*args, **kwargs)
        return wrapped_route
    return decorator


def generate_barcode_pattern(isbn):
    cleaned = "".join(ch for ch in str(isbn) if ch.isdigit())

    if not cleaned:
        cleaned = "000000000000"

    pattern = ""
    for digit in cleaned:
        number = int(digit)
        pattern += "|" * (number + 1) + " "

    return pattern.strip()


@books_bp.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        user = USERS.get(username)

        if user and user["password"] == password:
            session["logged_in"] = True
            session["username"] = username
            session["role"] = user["role"]
            return redirect(url_for("books.home_page"))
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)


@books_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("books.login"))


@books_bp.route("/home")
@login_required
def home_page():
    return render_template(
        "index.html",
        username=session.get("username"),
        role=session.get("role")
    )


@books_bp.route("/books")
@login_required
def list_books():
    search_query = request.args.get("search", "")

    connection = get_connection()

    if search_query:
        books = connection.execute(
            """
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?
            ORDER BY id DESC
            """,
            (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%")
        ).fetchall()
    else:
        books = connection.execute(
            "SELECT * FROM books ORDER BY id DESC"
        ).fetchall()

    connection.close()

    return render_template(
        "inventory.html",
        books=books,
        search_query=search_query,
        username=session.get("username"),
        role=session.get("role")
    )


@books_bp.route("/books/add", methods=["GET", "POST"])
@role_required(["all_access", "manager"])
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

    return render_template("add_book.html", username=session.get("username"), role=session.get("role"))


@books_bp.route("/books/edit/<int:book_id>", methods=["GET", "POST"])
@role_required(["all_access", "manager"])
def edit_book(book_id):
    connection = get_connection()

    if request.method == "POST":
        isbn = request.form["isbn"]
        title = request.form["title"]
        author = request.form["author"]
        price = request.form["price"]
        quantity = request.form["quantity"]

        connection.execute(
            """
            UPDATE books
            SET isbn = ?, title = ?, author = ?, price = ?, quantity = ?
            WHERE id = ?
            """,
            (isbn, title, author, price, quantity, book_id)
        )
        connection.commit()
        connection.close()

        return redirect(url_for("books.list_books"))

    book = connection.execute(
        "SELECT * FROM books WHERE id = ?",
        (book_id,)
    ).fetchone()

    connection.close()

    if book is None:
        return "Book not found."

    return render_template("edit_book.html", book=book, username=session.get("username"), role=session.get("role"))


@books_bp.route("/books/delete/<int:book_id>", methods=["POST"])
@role_required(["all_access", "manager"])
def delete_book(book_id):
    connection = get_connection()

    connection.execute(
        "DELETE FROM books WHERE id = ?",
        (book_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("books.list_books"))


@books_bp.route("/books/update/<int:book_id>", methods=["POST"])
@role_required(["all_access", "manager"])
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


@books_bp.route("/books/label/<int:book_id>")
@role_required(["all_access", "manager"])
def book_label(book_id):
    connection = get_connection()

    book = connection.execute(
        "SELECT * FROM books WHERE id = ?",
        (book_id,)
    ).fetchone()

    connection.close()

    if book is None:
        return "Book not found."

    barcode_pattern = generate_barcode_pattern(book["isbn"])

    return render_template(
        "book_label.html",
        book=book,
        barcode_pattern=barcode_pattern,
        username=session.get("username"),
        role=session.get("role")
    )


@books_bp.route("/export/inventory")
@role_required(["all_access", "manager"])
def export_inventory():
    connection = get_connection()
    books = connection.execute(
        "SELECT * FROM books ORDER BY id DESC"
    ).fetchall()
    connection.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Book ID",
        "ISBN",
        "Title",
        "Author",
        "Price",
        "Quantity"
    ])

    for book in books:
        writer.writerow([
            book["id"],
            book["isbn"],
            book["title"],
            book["author"],
            book["price"],
            book["quantity"]
        ])

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory_report.csv"}
    )


@books_bp.route("/low-stock")
@role_required(["all_access", "manager"])
def low_stock():
    connection = get_connection()
    books = connection.execute(
        "SELECT * FROM books WHERE quantity < 5 ORDER BY quantity ASC"
    ).fetchall()
    connection.close()

    return render_template(
        "low_stock.html",
        books=books,
        username=session.get("username"),
        role=session.get("role")
    )


@books_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    connection = get_connection()

    if request.method == "POST":
        book_id = request.form["book_id"]
        quantity_sold = int(request.form["quantity_sold"])
        state = request.form["state"]

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

        subtotal = float(book["price"]) * quantity_sold
        tax_rate = STATE_TAX_RATES.get(state, 0)
        tax_amount = round(subtotal * tax_rate, 2)
        final_total = round(subtotal + tax_amount, 2)

        if new_quantity < 5:
            reorder_amount = 10

            first_supplier = connection.execute(
                "SELECT id FROM suppliers ORDER BY id ASC LIMIT 1"
            ).fetchone()

            supplier_id = first_supplier["id"] if first_supplier else None

            connection.execute(
                """
                INSERT INTO purchase_orders (book_id, title, quantity_ordered, supplier_id)
                VALUES (?, ?, ?, ?)
                """,
                (book["id"], book["title"], reorder_amount, supplier_id)
            )

        connection.execute(
            "UPDATE books SET quantity = ? WHERE id = ?",
            (new_quantity, book_id)
        )

        connection.execute(
            """
            INSERT INTO sales (
                book_id, title, quantity_sold, total_price, state, subtotal, tax_rate, tax_amount, final_total
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                book["id"],
                book["title"],
                quantity_sold,
                final_total,
                state,
                subtotal,
                tax_rate,
                tax_amount,
                final_total
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("books.sales_history"))

    books = connection.execute(
        "SELECT * FROM books ORDER BY title ASC"
    ).fetchall()
    connection.close()

    return render_template(
        "checkout.html",
        books=books,
        state_tax_rates=STATE_TAX_RATES,
        username=session.get("username"),
        role=session.get("role")
    )


@books_bp.route("/sales")
@login_required
def sales_history():
    connection = get_connection()
    sales = connection.execute(
        "SELECT * FROM sales ORDER BY sale_date DESC"
    ).fetchall()
    connection.close()

    return render_template(
        "sales.html",
        sales=sales,
        username=session.get("username"),
        role=session.get("role")
    )


@books_bp.route("/export/sales")
@role_required(["all_access", "manager"])
def export_sales():
    connection = get_connection()
    sales = connection.execute(
        "SELECT * FROM sales ORDER BY sale_date DESC"
    ).fetchall()
    connection.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Sale ID",
        "Book ID",
        "Title",
        "Quantity Sold",
        "State",
        "Subtotal",
        "Tax Rate",
        "Tax Amount",
        "Final Total",
        "Sale Date"
    ])

    for sale in sales:
        writer.writerow([
            sale["id"],
            sale["book_id"],
            sale["title"],
            sale["quantity_sold"],
            sale["state"] if "state" in sale.keys() else "",
            sale["subtotal"] if "subtotal" in sale.keys() else "",
            sale["tax_rate"] if "tax_rate" in sale.keys() else "",
            sale["tax_amount"] if "tax_amount" in sale.keys() else "",
            sale["final_total"] if "final_total" in sale.keys() else sale["total_price"],
            sale["sale_date"]
        ])

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=sales_report.csv"}
    )


@books_bp.route("/purchase-orders")
@role_required(["all_access", "manager"])
def purchase_orders():
    connection = get_connection()

    orders = connection.execute(
        """
        SELECT
            purchase_orders.id,
            purchase_orders.book_id,
            purchase_orders.title,
            purchase_orders.quantity_ordered,
            purchase_orders.order_date,
            purchase_orders.supplier_id,
            suppliers.name AS supplier_name
        FROM purchase_orders
        LEFT JOIN suppliers ON purchase_orders.supplier_id = suppliers.id
        ORDER BY purchase_orders.order_date DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "purchase_orders.html",
        orders=orders,
        username=session.get("username"),
        role=session.get("role")
    )


@books_bp.route("/export/purchase-orders")
@role_required(["all_access", "manager"])
def export_purchase_orders():
    connection = get_connection()

    orders = connection.execute(
        """
        SELECT
            purchase_orders.id,
            purchase_orders.book_id,
            purchase_orders.title,
            purchase_orders.quantity_ordered,
            purchase_orders.order_date,
            suppliers.name AS supplier_name
        FROM purchase_orders
        LEFT JOIN suppliers ON purchase_orders.supplier_id = suppliers.id
        ORDER BY purchase_orders.order_date DESC
        """
    ).fetchall()

    connection.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Order ID",
        "Book ID",
        "Title",
        "Quantity Ordered",
        "Supplier",
        "Order Date"
    ])

    for order in orders:
        writer.writerow([
            order["id"],
            order["book_id"],
            order["title"],
            order["quantity_ordered"],
            order["supplier_name"] if order["supplier_name"] else "Unassigned",
            order["order_date"]
        ])

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=purchase_orders_report.csv"}
    )


@books_bp.route("/dashboard")
@role_required(["all_access", "manager"])
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
        chart_data=chart_data,
        username=session.get("username"),
        role=session.get("role")
    )


@books_bp.route("/suppliers")
@role_required(["all_access", "manager"])
def suppliers():
    connection = get_connection()
    suppliers_list = connection.execute(
        "SELECT * FROM suppliers ORDER BY id DESC"
    ).fetchall()
    connection.close()

    return render_template(
        "suppliers.html",
        suppliers=suppliers_list,
        username=session.get("username"),
        role=session.get("role")
    )


@books_bp.route("/suppliers/add", methods=["GET", "POST"])
@role_required(["all_access", "manager"])
def add_supplier():
    if request.method == "POST":
        name = request.form["name"]
        contact_name = request.form["contact_name"]
        email = request.form["email"]
        phone = request.form["phone"]

        connection = get_connection()
        connection.execute(
            "INSERT INTO suppliers (name, contact_name, email, phone) VALUES (?, ?, ?, ?)",
            (name, contact_name, email, phone)
        )
        connection.commit()
        connection.close()

        return redirect(url_for("books.suppliers"))

    return render_template(
        "add_supplier.html",
        username=session.get("username"),
        role=session.get("role")
    )


@books_bp.route("/api/books")
@role_required(["all_access"])
def api_books():
    connection = get_connection()
    books = connection.execute("SELECT * FROM books").fetchall()
    connection.close()

    return jsonify([dict(book) for book in books])


@books_bp.route("/api/sales")
@role_required(["all_access"])
def api_sales():
    connection = get_connection()
    sales = connection.execute("SELECT * FROM sales").fetchall()
    connection.close()

    return jsonify([dict(sale) for sale in sales])