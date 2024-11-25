from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from twilio.rest import Client

app = Flask(__name__)
app.secret_key = 'your_secret_key'
  # Secret key for session management




client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Landing Page for Role Selection
@app.route('/home')
def landing_page():
    return render_template('landing_page.html')
@app.route('/admin/clear_queue')

def clear_queue():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    # Clear the tokens table
    conn = sqlite3.connect('ration_shop.db')
    c = conn.cursor()
    c.execute("DELETE FROM tokens")
    conn.commit()
    conn.close()

    return redirect(url_for('admin_page'))


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

# Admin credentials (hardcoded for simplicity)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

# Home (Customer Page)
@app.route('/')
def customer_page():
    conn = sqlite3.connect('ration_shop.db')
    c = conn.cursor()
    c.execute("SELECT * FROM tokens")
    tokens = c.fetchall()
    conn.close()
    return render_template('customer.html', tokens=tokens)

# Reserve Token (Customer)
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
    return redirect(url_for('customer_page'))

# Admin Login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_page'))
        else:
            return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')

# Admin Logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# Admin Page
@app.route('/admin')
def admin_page():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect('ration_shop.db')
    c = conn.cursor()
    c.execute("SELECT * FROM tokens")
    tokens = c.fetchall()
    conn.close()
    return render_template('admin.html', tokens=tokens)

# Send Alert (Admin)
@app.route('/alert/<int:token_id>')
def send_alert(token_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect('ration_shop.db')
    c = conn.cursor()
    c.execute("SELECT contact, token_number FROM tokens WHERE id=?", (token_id,))
    token = c.fetchone()
    conn.close()

    if token:
        contact, token_number = token
        message = f"Reminder: Your token number {token_number} is about to be served. Please proceed to the ration shop."
        try:
            client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=contact
            )
            print(f"Alert sent to {contact}")
        except Exception as e:
            print(f"Failed to send SMS: {e}")
    return redirect(url_for('admin_page'))

# Mark Token as Completed (Admin)
@app.route('/complete/<int:token_id>')
def complete_token(token_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect('ration_shop.db')
    c = conn.cursor()
    c.execute("UPDATE tokens SET status='Completed' WHERE id=?", (token_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_page'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
