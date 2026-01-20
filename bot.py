import telebot
from telebot import types
import db
from flask import Flask
from threading import Thread
from datetime import datetime
import sender 

# --- CONFIGURATION ---
API_TOKEN = '8510819274:AAHSTv4XIizaR_0b_iu18eKR-T-VDBHT8_w'  # Bot token
ADMIN_ID = 5762886443               # Admin User ID (Numeric)
ADMIN_USERNAME = "@md_bro2k"       # Admin Username

bot = telebot.TeleBot(API_TOKEN)

# --- WEB SERVER FOR RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive"
def run_http(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_http).start()

# --- HELPER FUNCTIONS ---
def get_remaining_days(expiry_str):
    if not expiry_str: return 0
    try:
        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        today = datetime.now(db.DHAKA_TZ).date()
        remaining = (expiry_date - today).days
        return max(0, remaining)
    except: return 0

# --- KEYBOARDS ---

def get_main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Main Menu 🏠"))
    return markup

def get_start_inline_markup(user_id):
    markup = types.InlineKeyboardMarkup()
    btn_sms = types.InlineKeyboardButton("📨 Send SMS", callback_data="start_sms")
    markup.add(btn_sms)
    
    if int(user_id) == int(ADMIN_ID):
        btn_admin = types.InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel")
        markup.add(btn_admin)
    return markup

def get_back_btn(callback_data):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data=callback_data))
    return markup

def get_back_cancel_markup(back_callback):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data=back_callback))
    markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
    return markup

def get_admin_panel_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📊 User Statistics", callback_data="admin_stats"),
        types.InlineKeyboardButton("💎 Set Premium", callback_data="admin_set_prem"),
        types.InlineKeyboardButton("👤 Set Basic", callback_data="admin_set_basic"),
        types.InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ Unban User", callback_data="admin_unban"),
        types.InlineKeyboardButton("🔄 Reset User Usage", callback_data="admin_reset"),
        types.InlineKeyboardButton("🔙 Back to Start Menu", callback_data="main_menu")
    )
    return markup

# --- START & MENU ---

@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda message: message.text == "Main Menu 🏠")
def send_welcome(message):
    bot.clear_step_handler_by_chat_id(message.chat.id)
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
    db.add_user(user_id, username)
    user_info = db.get_user_info(user_id) 
    
    role = user_info[2]
    expiry = user_info[3]
    daily_limit = user_info[4]
    used = user_info[5]
    is_banned = user_info[7]
    
    # Admin & Role Logic
    if int(user_id) == int(ADMIN_ID):
        role_display = "👨‍✈️ Admin"
        limit_display = "♾ Unlimited"
        remaining_display = "♾"
    elif is_banned:
        role_display = "🚫 Banned"
        limit_display = "0"
        remaining_display = "0"
    elif role == 'premium':
        role_display = "💎 Premium"
        limit_display = str(daily_limit)
        remaining_display = str(daily_limit - used)
    else:
        role_display = "👤 Basic"
        limit_display = str(daily_limit)
        remaining_display = str(daily_limit - used)

    welcome_text = (
        f"👋 Welcome <b>{username}</b>\n\n"
        f"🆔 User ID: <code>{user_id}</code>\n"
        f"👤 Role: <b>{role_display}</b>\n"
        f"📨 Daily Limit: {limit_display}\n"
        f"📊 Today Used: {used}\n"
        f"📉 Remaining: {remaining_display}\n"
    )

    if role == 'premium' and expiry and int(user_id) != int(ADMIN_ID):
        rem_days = get_remaining_days(expiry)
        welcome_text += f"📅 Premium Till: {expiry}\n"
        welcome_text += f"⏳ Premium Remaining: {rem_days} Days\n"
    
    welcome_text += f"\n💎 Premium নিতে admin কে ID দিন:\n{ADMIN_USERNAME}"

    # Back function and others will now call this, so admin button will always show
    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', 
                     reply_markup=get_start_inline_markup(user_id))
    bot.send_message(message.chat.id, "Keyboard Menu Opened:", reply_markup=get_main_menu_keyboard())

# --- SEND SMS FLOW ---
user_data = {} 

@bot.callback_query_handler(func=lambda call: call.data == "start_sms")
def start_sms_flow(call):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    user_info = db.get_user_info(call.from_user.id)
    
    if user_info[7] == 1:
        bot.answer_callback_query(call.id, "🚫 You are BANNED!", show_alert=True)
        return

    msg = bot.edit_message_text("📱 Enter Bangladeshi Number (e.g., 017xxxxxxxx):", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=get_back_cancel_markup("main_menu"))
    bot.register_next_step_handler(msg, process_number)

def process_number(message):
    if message.text == "Main Menu 🏠": return send_welcome(message)
    phone = message.text
    if not phone or not phone.isdigit() or len(phone) != 11 or not phone.startswith("01"):
        msg = bot.reply_to(message, "❌ Invalid Number. Try again:", reply_markup=get_back_cancel_markup("main_menu"))
        bot.register_next_step_handler(msg, process_number)
        return
    
    user_data[message.chat.id] = {'phone': phone}
    user_info = db.get_user_info(message.chat.id)
    
    # Admin has 100 per session, Premium 50, Basic 20
    if int(message.chat.id) == int(ADMIN_ID): s_limit = 100
    elif user_info[2] == 'premium': s_limit = 50
    else: s_limit = 20
    
    msg = bot.send_message(message.chat.id, f"🔢 How many OTPs? (Max: {s_limit})", reply_markup=get_back_cancel_markup("start_sms"))
    bot.register_next_step_handler(msg, process_amount, s_limit, user_info)

def process_amount(message, s_limit, user_info):
    if message.text == "Main Menu 🏠": return send_welcome(message)
    if not message.text.isdigit():
        msg = bot.send_message(message.chat.id, "❌ Enter number only:", reply_markup=get_back_cancel_markup("start_sms"))
        bot.register_next_step_handler(msg, process_amount, s_limit, user_info)
        return

    amount = int(message.text)
    used = user_info[5]
    daily_limit = user_info[4]
    
    # Admin bypass limit
    if int(message.chat.id) != int(ADMIN_ID):
        if amount > s_limit:
            msg = bot.send_message(message.chat.id, f"❌ Max session {s_limit}. Try again:", reply_markup=get_back_cancel_markup("start_sms"))
            bot.register_next_step_handler(msg, process_amount, s_limit, user_info)
            return
        if amount > (daily_limit - used):
            bot.send_message(message.chat.id, "❌ Daily limit exceeded!", reply_markup=get_main_menu_keyboard())
            return

    user_data[message.chat.id]['amount'] = amount
    msg = bot.send_message(message.chat.id, "⏱ Enter Delay (seconds):", reply_markup=get_back_cancel_markup("start_sms"))
    bot.register_next_step_handler(msg, process_delay)

def process_delay(message):
    if message.text == "Main Menu 🏠": return send_welcome(message)
    try:
        delay = float(message.text)
        data = user_data.get(message.chat.id)
        bot.send_message(message.chat.id, f"🚀 Sending {data['amount']} OTPs to {data['phone']}...")
        sent = sender.send_serial_otp(data['phone'], data['amount'], delay)
        db.update_usage(message.chat.id, sent)
        bot.send_message(message.chat.id, f"✅ Done! Sent {sent} to {data['phone']}", reply_markup=get_back_btn("main_menu"))
    except:
        bot.send_message(message.chat.id, "❌ Invalid delay.")

# --- ADMIN PANEL ---

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel_home(call):
    if int(call.from_user.id) != int(ADMIN_ID): return
    total_users, total_sent = db.get_global_stats()
    text = f"🛠 <b>Welcome Admin Panel</b>\n\n👥 Total Users: {total_users}\n📨 Total OTP Today: {total_sent or 0}"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=get_admin_panel_markup())

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    users = db.get_all_users()
    report = "📊 <b>User Statistics</b>\n\n"
    for u in users:
        role = "Admin" if int(u[0]) == int(ADMIN_ID) else ("Banned" if u[7] else u[2])
        report += f"👤 <code>{u[0]}</code> | @{u[1]}\nRole: {role} | Used: {u[5]}/{u[4]}\n"
        if u[2] == 'premium' and u[3]: report += f"Exp: {u[3]} ({get_remaining_days(u[3])} days)\n"
        report += "----------\n"
    bot.edit_message_text(report[:4000], call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=get_back_btn("admin_panel"))

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def handle_admin_actions(call):
    action = call.data
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    if action == "admin_set_prem":
        msg = bot.send_message(call.message.chat.id, "💎 Enter User ID:", reply_markup=get_back_btn("admin_panel"))
        bot.register_next_step_handler(msg, admin_ask_days)
    elif action == "admin_set_basic":
        msg = bot.send_message(call.message.chat.id, "👤 Enter User ID:", reply_markup=get_back_btn("admin_panel"))
        bot.register_next_step_handler(msg, lambda m: admin_final_action(m, "basic"))
    elif action == "admin_ban":
        msg = bot.send_message(call.message.chat.id, "🚫 Enter User ID:", reply_markup=get_back_btn("admin_panel"))
        bot.register_next_step_handler(msg, lambda m: admin_final_action(m, "ban"))
    elif action == "admin_unban":
        msg = bot.send_message(call.message.chat.id, "✅ Enter User ID:", reply_markup=get_back_btn("admin_panel"))
        bot.register_next_step_handler(msg, lambda m: admin_final_action(m, "unban"))
    elif action == "admin_reset":
        msg = bot.send_message(call.message.chat.id, "🔄 Enter User ID:", reply_markup=get_back_btn("admin_panel"))
        bot.register_next_step_handler(msg, lambda m: admin_final_action(m, "reset"))

def admin_ask_days(message):
    try:
        user_data[message.chat.id] = {'target': int(message.text)}
        msg = bot.send_message(message.chat.id, "📅 Enter Duration (Days):", reply_markup=get_back_btn("admin_panel"))
        bot.register_next_step_handler(msg, lambda m: admin_final_action(m, "premium"))
    except: bot.send_message(message.chat.id, "❌ Invalid ID")

def admin_final_action(message, task):
    try:
        target_id = user_data.get(message.chat.id, {}).get('target') or int(message.text)
        if task == "premium":
            db.set_premium(target_id, int(message.text))
            res = "Premium Set ✅"
        elif task == "basic":
            db.set_basic(target_id)
            res = "Basic Set ✅"
        elif task == "ban":
            db.set_ban_status(target_id, 1)
            res = "User Banned 🚫"
        elif task == "unban":
            db.set_ban_status(target_id, 0)
            res = "User Unbanned ✅"
        elif task == "reset":
            db.reset_user_stats(target_id)
            res = "Usage Reset 🔄"
        
        # Result showing with BACK TO ADMIN PANEL button
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel"))
        markup.add(types.InlineKeyboardButton("🏠 Back to Start Menu", callback_data="main_menu"))
        bot.send_message(message.chat.id, res, reply_markup=markup)
    except: bot.send_message(message.chat.id, "❌ Operation Failed.")

# Navigation
@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def back_to_main(call):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_welcome(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_action(call):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    bot.send_message(call.message.chat.id, "❌ Action Cancelled.")
    send_welcome(call.message)

if __name__ == "__main__":
    keep_alive()
    # পোলিং শুরু করার আগে কিছুক্ষণ গ্যাপ রাখা
    import time
    time.sleep(2) 
    bot.infinity_polling(skip_pending=True, timeout=10, long_polling_timeout=5)
