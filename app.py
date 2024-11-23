from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('ration_shop.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    contact TEXT NOT NULL,
                    token_number INTEGER NOT NULL,
                    status TEXT DEFAULT 'Reserved')''')
    conn.commit()
    conn.close()

# Home page
@app.route('/')
def index():
    conn = sqlite3.connect('ration_shop.db')
    c = conn.cursor()
    c.execute("SELECT * FROM tokens")
    tokens = c.fetchall()
    conn.close()
    return render_template('index.html', tokens=tokens)

# Reserve a token
@app.route('/reserve', methods=['POST'])
def reserve_token():
    name = request.form['name']
    contact = request.form['contact']
    conn = sqlite3.connect('ration_shop.db')
    c = conn.cursor()
    c.execute("SELECT COALESCE(MAX(token_number), 0) + 1 FROM tokens")
    token_number = c.fetchone()[0]
    c.execute("INSERT INTO tokens (name, contact, token_number) VALUES (?, ?, ?)",
              (name, contact, token_number))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Mark token as completed
@app.route('/complete/<int:token_id>')
def complete_token(token_id):
    conn = sqlite3.connect('ration_shop.db')
    c = conn.cursor()
    c.execute("UPDATE tokens SET status='Completed' WHERE id=?", (token_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Alert message simulation
@app.route('/alert/<int:token_id>')
def alert_token(token_id):
    conn = sqlite3.connect('ration_shop.db')
    c = conn.cursor()
    c.execute("SELECT contact FROM tokens WHERE id=?", (token_id,))
    contact = c.fetchone()
    conn.close()
    # In a real app, send an SMS or notification
    print(f"Alert sent to: {contact}")
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
