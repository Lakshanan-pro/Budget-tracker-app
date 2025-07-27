from flask import Flask, render_template, request, jsonify
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def init_db():
    with sqlite3.connect("database.db") as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                amount REAL,
                category TEXT,
                description TEXT,
                date TEXT
            )
        ''')

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add", methods=["POST"])
def add_transaction():
    data = request.get_json()
    with sqlite3.connect("database.db") as conn:
        conn.execute(
            "INSERT INTO transactions (type, amount, category, description, date) VALUES (?, ?, ?, ?, ?)",
            (data["type"], data["amount"], data["category"], data["description"], data["date"])
        )
    return jsonify({"message": "Transaction added!"})

@app.route("/transactions", methods=["GET"])
def get_transactions():
    date = request.args.get("date")
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        if date:
            cursor.execute("SELECT * FROM transactions WHERE date = ?", (date,))
        else:
            cursor.execute("SELECT * FROM transactions")
        rows = cursor.fetchall()

    income = sum(row[2] for row in rows if row[1] == "Income")
    expense = sum(row[2] for row in rows if row[1] == "Expense")
    balance = income - expense

    return jsonify({
        "transactions": [
            {"id": row[0], "type": row[1], "amount": row[2], "category": row[3], "description": row[4], "date": row[5]}
            for row in rows
        ],
        "income": income,
        "expense": expense,
        "balance": balance
    })

@app.route("/delete/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    with sqlite3.connect("database.db") as conn:
        conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    return jsonify({"message": "Transaction deleted!"})

if __name__ == "__main__":
    app.run(debug=True)
