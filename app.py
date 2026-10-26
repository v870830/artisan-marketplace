
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, session
)
from werkzeug.security import generate_password_hash, check_password_hash

import sqlite3
import base64
from pathlib import Path
from functools import wraps

app = Flask(__name__)
app.secret_key = "artisan-marketplace-dev-key"
app.config["SESSION_PERMANENT"] = True

app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 30
# Check whether the user is logged in
def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))

        return route_function(*args, **kwargs)

    return wrapper



DATABASE = Path(__file__).with_name("database.db")


# Connect to the SQLite database
def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# Create database tables if they do not exist
def initialize_database():
    connection = get_db_connection()

    # 1. Users table for registration and login
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Products table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            location TEXT NOT NULL,
            artisan TEXT NOT NULL,
            description TEXT NOT NULL,
            image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Check whether products already have a user_id column
    columns = connection.execute(
        "PRAGMA table_info(products)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    # Add user_id without deleting existing products
    if "user_id" not in column_names:
        connection.execute("""
            ALTER TABLE products
            ADD COLUMN user_id INTEGER REFERENCES users(id)
        """)

    # 4. Orders table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            buyer_name TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            total_price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

        # Add buyer_id to existing orders table if it does not exist
    order_columns = connection.execute(
        "PRAGMA table_info(orders)"
    ).fetchall()

    order_column_names = [column["name"] for column in order_columns]

    if "buyer_id" not in order_column_names:
        connection.execute("""
            ALTER TABLE orders
            ADD COLUMN buyer_id INTEGER REFERENCES users(id)
        """)

    # Add cancellation source to existing orders table if missing
    order_columns = connection.execute(
        "PRAGMA table_info(orders)"
    ).fetchall()

    order_column_names = [column["name"] for column in order_columns]

    if "cancelled_by" not in order_column_names:
        connection.execute("""
            ALTER TABLE orders
            ADD COLUMN cancelled_by TEXT
        """)


    
    connection.commit()
    connection.close()



# Register a new artisan
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Validate registration fields
        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
            return redirect(url_for("register"))

        # Save the account with a hashed password
        hashed_password = generate_password_hash(password)

        connection = get_db_connection()

        try:
            connection.execute("""
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
            """, (name, email, hashed_password))

            connection.commit()

        except sqlite3.IntegrityError:
            flash("This email is already registered. Please log in.", "error")
            return redirect(url_for("login"))

        finally:
            connection.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# Log in an existing artisan
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = get_db_connection()

        user = connection.execute("""
            SELECT * FROM users WHERE email = ?
        """, (email,)).fetchone()

        connection.close()

      
        if user and check_password_hash(user["password"], password):
            session.clear()

            # Keep the user logged in across browser restarts
            session.permanent = True

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            flash("Welcome back, " + user["name"] + "!", "success")
            return redirect(url_for("artisan"))

        flash("Invalid email or password.", "error")
        return redirect(url_for("login"))



    return render_template("login.html")


# Log out the current artisan
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


# Marketplace homepage
@app.route("/")
def home():
    connection = get_db_connection()

    products = connection.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()

    # Convert SQLite Row objects into dictionaries for JSON
    products = [dict(product) for product in products]

    connection.close()

    return render_template("index.html", products=products)



# Artisan Studio — each artisan sees only their own products
@app.route("/artisan", methods=["GET", "POST"])
@login_required
def artisan():

    # Handle new product submission
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        location = request.form.get("location", "").strip()
        artisan_name = request.form.get("artisan", "").strip()
        description = request.form.get("description", "").strip()

        try:
            price = float(request.form.get("price", "0"))
        except ValueError:
            price = 0

        # Read the uploaded product image
        image_file = request.files.get("image")
        image_data = None

        if image_file and image_file.filename:
            allowed_types = {"image/jpeg", "image/png", "image/webp"}

            if image_file.mimetype not in allowed_types:
                flash("Please upload a JPG, PNG, or WebP image.", "error")
                return redirect(url_for("artisan"))

            image_bytes = image_file.read()

            if len(image_bytes) > 5 * 1024 * 1024:
                flash("Image must be smaller than 5 MB.", "error")
                return redirect(url_for("artisan"))

            image_data = (
                "data:"
                + image_file.mimetype
                + ";base64,"
                + base64.b64encode(image_bytes).decode("utf-8")
            )

        # Validate product details
        if not all([name, category, location, artisan_name, description]):
            flash("Please fill in all product details.", "error")
            return redirect(url_for("artisan"))

        if price <= 0:
            flash("Please enter a valid price.", "error")
            return redirect(url_for("artisan"))

        if image_data is None:
            flash("Please select a product image.", "error")
            return redirect(url_for("artisan"))

        # Save the product with the logged-in user's ID
        connection = get_db_connection()

        connection.execute("""
            INSERT INTO products
            (name, category, price, location, artisan, description, image, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            category,
            price,
            location,
            artisan_name,
            description,
            image_data,
            session["user_id"]
        ))

        connection.commit()
        connection.close()

        flash("Product published successfully!", "success")
        return redirect(url_for("artisan"))

    # Fetch only products owned by the logged-in artisan
    connection = get_db_connection()

    products = connection.execute("""
        SELECT *
        FROM products
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],)).fetchall()

    connection.close()

    return render_template("artisan.html", products=products)



# Buyer page
@app.route("/buyer")
def buyer():
    connection = get_db_connection()
    products = connection.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()
    connection.close()

    return render_template("buyer.html", products=products)



# Orders dashboard - show only orders for the logged-in artisan
@app.route("/orders")
@login_required
def orders():
    connection = get_db_connection()

    order_list = connection.execute("""
        SELECT
            orders.id,
            orders.buyer_name,
            orders.quantity,
            orders.total_price,
            orders.status,
            orders.cancelled_by,
            orders.created_at,
            products.name AS product_name,
            products.artisan AS artisan_name
        FROM orders
        JOIN products ON orders.product_id = products.id
        WHERE products.user_id = ?
        ORDER BY orders.id DESC
    """, (session["user_id"],)).fetchall()

    connection.close()

    return render_template("orders.html", orders=order_list)


# Create a buyer order

@app.route("/place-order/<int:product_id>", methods=["POST"])
@login_required
def place_order(product_id):
    buyer_name = request.form.get("buyer_name", "").strip()

    try:
        quantity = int(request.form.get("quantity", "1"))
    except ValueError:
        quantity = 0

    if not buyer_name or quantity < 1 or quantity > 100:
        flash("Please enter a valid buyer name and quantity.", "error")
        return redirect(url_for("buyer"))

    connection = get_db_connection()

    product = connection.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if product is None:
        connection.close()
        flash("Product not found.", "error")
        return redirect(url_for("buyer"))

    total_price = product["price"] * quantity

    connection.execute("""
        INSERT INTO orders
        (product_id, buyer_name, quantity, total_price, buyer_id)
        VALUES (?, ?, ?, ?, ?)
    """, (
        product_id,
        buyer_name,
        quantity,
        total_price,
        session["user_id"]
    ))

    connection.commit()
    connection.close()

    flash("Order placed successfully!", "success")
    return redirect(url_for("my_orders"))



# My Orders - show orders belonging to the logged-in buyer
@app.route("/my-orders")
@login_required
def my_orders():
    connection = get_db_connection()

    order_list = connection.execute("""
        SELECT
            orders.id,
            orders.buyer_name,
            orders.quantity,
            orders.total_price,
            orders.status,
            orders.created_at,
            products.name AS product_name,
            products.artisan AS artisan_name
        FROM orders
        JOIN products ON orders.product_id = products.id
        WHERE orders.buyer_id = ?
        ORDER BY orders.id DESC
    """, (session["user_id"],)).fetchall()

    connection.close()

    return render_template("my_orders.html", orders=order_list)


# Allow a buyer to cancel their own Pending or Processing order
@app.route("/cancel-order/<int:order_id>", methods=["POST"])
@login_required
def cancel_order(order_id):
    connection = get_db_connection()

    order = connection.execute("""
        SELECT id, status
        FROM orders
        WHERE id = ? AND buyer_id = ?
    """, (order_id, session["user_id"])).fetchone()

    if order is None:
        connection.close()
        flash("Order not found in your account.", "error")
        return redirect(url_for("my_orders"))

    if order["status"] not in {"Pending", "Processing"}:
        connection.close()
        flash("Only Pending or Processing orders can be cancelled.", "error")
        return redirect(url_for("my_orders"))

    connection.execute("""
UPDATE orders
SET status = 'Cancelled',
cancelled_by = 'customer'
WHERE id = ? AND buyer_id = ?
""", (order_id, session["user_id"]))


    connection.commit()
    connection.close()

    flash("Your order has been cancelled successfully.", "success")
    return redirect(url_for("my_orders"))


# Update order status

@app.route("/update-order/<int:order_id>", methods=["POST"])
@login_required
def update_order(order_id):
    status = request.form.get("status", "")
    allowed_statuses = {"Pending", "Processing", "Delivered", "Cancelled"}

    if status not in allowed_statuses:
        flash("Invalid order status.", "error")
        return redirect(url_for("orders"))

    connection = get_db_connection()

    # Check whether this order belongs to the logged-in artisan
    order = connection.execute("""
        SELECT orders.id
        FROM orders
        JOIN products ON orders.product_id = products.id
        WHERE orders.id = ? AND products.user_id = ?
    """, (order_id, session["user_id"])).fetchone()

    if order is None:
        connection.close()
        flash("You are not allowed to update this order.", "error")
        return redirect(url_for("orders"))

    connection.execute(
        "UPDATE orders SET status = ? WHERE id = ?",
        (status, order_id)
    )

    connection.commit()
    connection.close()

    flash("Order status updated.", "success")
    return redirect(url_for("orders"))


# Initialize database before starting the application
initialize_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
