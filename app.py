from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize the database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT,
        amount REAL,
        category TEXT,
        description TEXT,
        date TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    conn.commit()
    conn.close()

init_db()

# Routes
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    data = request.get_json()
    username = data['username']
    password = data['password']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT id, password FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()

    if user and check_password_hash(user[1], password):
        session['user_id'] = user[0]
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    data = request.get_json()
    username = data['username']
    password = generate_password_hash(data['password'])

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Username already exists'}), 409
    finally:
        conn.close()

    return jsonify({'message': 'Signup successful'}), 200

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/transactions', methods=['GET', 'POST', 'DELETE'])
def transactions():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        data = request.get_json()
        c.execute('''INSERT INTO transactions (user_id, type, amount, category, description, date)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (user_id, data['type'], data['amount'], data['category'], data['description'], data['date']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Transaction added successfully'}), 201

    elif request.method == 'GET':
        c.execute('SELECT * FROM transactions WHERE user_id = ?', (user_id,))
        transactions = c.fetchall()
        conn.close()

        result = [{
            'id': row[0],
            'type': row[2],
            'amount': row[3],
            'category': row[4],
            'description': row[5],
            'date': row[6]
        } for row in transactions]

        return jsonify(result), 200

    elif request.method == 'DELETE':
        data = request.get_json()
        c.execute('DELETE FROM transactions WHERE id = ? AND user_id = ?', (data['id'], user_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Transaction deleted'}), 200

if __name__ == '__main__':
    app.run(debug=True)
