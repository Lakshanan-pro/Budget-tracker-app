import logging
import os
import sqlite3
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
app.config["DATABASE"] = os.environ.get("DATABASE_PATH", "database.db")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_connection():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT DEFAULT '',
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )"""
    )
    conn.commit()
    conn.close()


def current_user_id():
    return session.get("user_id")


@app.route("/")
def home():
    if not current_user_id():
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/health")
def health():
    """Simple service health endpoint for monitoring and SRE checks."""
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        return jsonify({"status": "healthy", "service": "personal-expense-tracker"}), 200
    except sqlite3.Error:
        logger.exception("Health check failed")
        return jsonify({"status": "unhealthy"}), 503


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    conn = get_db_connection()
    user = conn.execute("SELECT id, password FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        session["user_id"] = user["id"]
        logger.info("User login successful: %s", username)
        return jsonify({"message": "Login successful"}), 200
    return jsonify({"message": "Invalid credentials"}), 401


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if len(username) < 3 or len(password) < 4:
        return jsonify({"message": "Username must be 3+ characters and password 4+ characters"}), 400

    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({"message": "Username already exists"}), 409
    finally:
        conn.close()

    logger.info("New user registered: %s", username)
    return jsonify({"message": "Signup successful"}), 201


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    user_id = current_user_id()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    conn = get_db_connection()
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        try:
            amount = float(data.get("amount", 0))
        except (TypeError, ValueError):
            amount = 0
        category = data.get("category", "").strip()
        description = data.get("description", "").strip()
        date = data.get("date", "").strip()

        if amount <= 0 or not category or not date:
            conn.close()
            return jsonify({"message": "Amount, category and date are required"}), 400

        cursor = conn.execute(
            """INSERT INTO expenses (user_id, amount, category, description, date)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, amount, category, description, date),
        )
        conn.commit()
        expense_id = cursor.lastrowid
        conn.close()
        logger.info("Expense added: id=%s user=%s amount=%.2f", expense_id, user_id, amount)
        return jsonify({"message": "Expense added successfully", "id": expense_id}), 201

    rows = conn.execute(
        "SELECT id, amount, category, description, date FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows]), 200


@app.route("/expenses/<int:expense_id>", methods=["PUT", "DELETE"])
def expense_detail(expense_id):
    user_id = current_user_id()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    conn = get_db_connection()
    existing = conn.execute(
        "SELECT id FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id)
    ).fetchone()
    if not existing:
        conn.close()
        return jsonify({"message": "Expense not found"}), 404

    if request.method == "DELETE":
        conn.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
        conn.commit()
        conn.close()
        logger.info("Expense deleted: id=%s user=%s", expense_id, user_id)
        return jsonify({"message": "Expense deleted"}), 200

    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        amount = 0
    category = data.get("category", "").strip()
    description = data.get("description", "").strip()
    date = data.get("date", "").strip()
    if amount <= 0 or not category or not date:
        conn.close()
        return jsonify({"message": "Amount, category and date are required"}), 400

    conn.execute(
        """UPDATE expenses SET amount = ?, category = ?, description = ?, date = ?
           WHERE id = ? AND user_id = ?""",
        (amount, category, description, date, expense_id, user_id),
    )
    conn.commit()
    conn.close()
    logger.info("Expense updated: id=%s user=%s", expense_id, user_id)
    return jsonify({"message": "Expense updated"}), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({"message": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.exception("Unhandled application error")
    return jsonify({"message": "Internal server error"}), 500


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
