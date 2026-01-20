import telebot
from telebot import types
import db
from flask import Flask
from threading import Thread
import sender 

# --- CONFIGURATION ---
API_TOKEN = '8510819274:AAHSTv4XIizaR_0b_iu18eKR-T-VDBHT8_w'  # আপনার বোট টোকেন
ADMIN_ID = 5762886443               # আপনার টেলিগ্রাম ইউজার আইডি (সংখ্যায় লিখবেন)
ADMIN_USERNAME = "@md_bro2k"       # ডিসপ্লে ইউজারনেম

bot = telebot.TeleBot(API_TOKEN)

# --- WEB SERVER FOR RENDER (Keep Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive! Bot is running 24/7."

def run_http():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# --- KEYBOARDS ---

def get_main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Main Menu 🏠"))
    return markup

def get_start_inline_markup(user_id):
    markup = types.InlineKeyboardMarkup()
    btn_sms = types.InlineKeyboardButton("📨 Send SMS", callback_data="start_sms")
    markup.add(btn_sms)
    
    # Check if user is admin (Converted to int just in case)
    if int(user_id) == int(ADMIN_ID):
        btn_admin = types.InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel")
        markup.add(btn_admin)
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
        types.InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
    )
    return markup

# --- START & MENU ---

@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda message: message.text == "Main Menu 🏠")
def send_welcome(message):
    # Fix: Clear any pending step handlers to prevent bugs
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
    remaining = daily_limit - used

    if is_banned:
        role_display = "🚫 BANNED"
    elif role == 'premium':
        role_display = "💎 Premium"
    else:
        role_display = "👤 Basic"

    welcome_text = (
        f"👋 Welcome <b>{username}</b>\n\n"
        f"🆔 User ID: <code>{user_id}</code>\n"
        f"👤 Role: <b>{role_display}</b>\n"
        f"📨 Daily Limit: {daily_limit}\n"
        f"📊 Today Used: {used}\n"
        f"📉 Remaining: {remaining}\n"
    )

    if role == 'premium' and expiry:
        welcome_text += f"📅 Premium Till: {expiry}\n"
    
    welcome_text += f"\n💎 Premium নিতে admin কে ID দিন:\n{ADMIN_USERNAME}"

    bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode='HTML', 
        reply_markup=get_start_inline_markup(user_id)
    )
    # Ensure keyboard is always there
    bot.send_message(message.chat.id, "Use the keyboard below:", reply_markup=get_main_menu_keyboard())

# --- SEND SMS FLOW ---
user_data = {} 

@bot.callback_query_handler(func=lambda call: call.data == "start_sms")
def start_sms_flow(call):
    # Fix: Clear previous handlers
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    
    user_id = call.from_user.id
    user_info = db.get_user_info(user_id)
    
    if user_info[7] == 1: # Banned check
        bot.answer_callback_query(call.id, "🚫 You are BANNED!", show_alert=True)
        return

    msg = bot.edit_message_text(
        "📱 Enter Bangladeshi Number (e.g., 017xxxxxxxx):", 
        call.message.chat.id, 
        call.message.message_id, 
        reply_markup=get_back_cancel_markup("main_menu")
    )
    bot.register_next_step_handler(msg, process_number)

def process_number(message):
    try:
        if message.text == "Main Menu 🏠":
            send_welcome(message)
            return

        phone = message.text
        if not phone.isdigit() or len(phone) != 11 or not phone.startswith("01"):
            msg = bot.reply_to(message, "❌ Invalid Number. Try again (01xxxxxxxxx):", reply_markup=get_back_cancel_markup("main_menu"))
            bot.register_next_step_handler(msg, process_number)
            return
        
        user_data[message.chat.id] = {'phone': phone}
        
        user_info = db.get_user_info(message.chat.id)
        role = user_info[2]
        session_limit = 50 if role == 'premium' else 20
        
        msg = bot.send_message(
            message.chat.id, 
            f"🔢 How many OTPs? (Max per session: {session_limit})", 
            reply_markup=get_back_cancel_markup("start_sms")
        )
        bot.register_next_step_handler(msg, process_amount, session_limit, user_info)
    except Exception:
        bot.send_message(message.chat.id, "❌ Error. /start again.")

def process_amount(message, session_limit, user_info):
    try:
        if message.text == "Main Menu 🏠":
            send_welcome(message)
            return

        if not message.text.isdigit():
             msg = bot.send_message(message.chat.id, "❌ Please enter a number.", reply_markup=get_back_cancel_markup("start_sms"))
             bot.register_next_step_handler(msg, process_amount, session_limit, user_info)
             return

        amount = int(message.text)
        daily_limit = user_info[4]
        used = user_info[5]
        remaining = daily_limit - used
        
        if amount > session_limit:
            msg = bot.send_message(message.chat.id, f"❌ Max session limit is {session_limit}. Try again.", reply_markup=get_back_cancel_markup("start_sms"))
            bot.register_next_step_handler(msg, process_amount, session_limit, user_info)
            return
        
        if amount > remaining:
            msg = bot.send_message(message.chat.id, f"❌ You only have {remaining} OTPs left today.", reply_markup=get_back_cancel_markup("start_sms"))
            bot.register_next_step_handler(msg, process_amount, session_limit, user_info)
            return

        user_data[message.chat.id]['amount'] = amount
        
        msg = bot.send_message(
            message.chat.id, 
            "⏱ Enter Delay (in seconds):", 
            reply_markup=get_back_cancel_markup("start_sms")
        )
        bot.register_next_step_handler(msg, process_delay)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid input.")

def process_delay(message):
    try:
        if message.text == "Main Menu 🏠":
            send_welcome(message)
            return

        delay = float(message.text)
        data = user_data.get(message.chat.id)
        
        start_msg = bot.send_message(message.chat.id, f"🚀 Sending {data['amount']} OTPs to {data['phone']}...")
        
        # --- SENDING ---
        sent = sender.send_serial_otp(data['phone'], data['amount'], delay)
        
        db.update_usage(message.chat.id, sent)
        
        bot.send_message(
            message.chat.id, 
            f"✅ Result: Total OTP sent to {data['phone']}: {sent}",
            reply_markup=get_back_cancel_markup("main_menu")
        )
    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid delay. Enter number only.")

# --- ADMIN PANEL ---

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel_home(call):
    # Admin Check Logic
    if int(call.from_user.id) != int(ADMIN_ID):
        bot.answer_callback_query(call.id, "❌ Admin access only!")
        return
    
    total_users, total_sent = db.get_global_stats()
    text = (
        "🛠 <b>Welcome Admin Panel</b>\n\n"
        f"👥 Total Users: {total_users}\n"
        f"📨 Total OTP Sent Today: {total_sent if total_sent else 0}\n"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=get_admin_panel_markup())

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if int(call.from_user.id) != int(ADMIN_ID): return

    users = db.get_all_users()
    report = "📊 <b>User Statistics</b>\n\n"
    
    for u in users:
        status = "🚫 Banned" if u[7] else u[2]
        report += (
            f"👦\nUser ID: <code>{u[0]}</code>\n"
            f"Username: @{u[1]}\n"
            f"Role: {status}\n"
            f"Total OTP send: {u[5]}/{u[4]}\n"
        )
        if u[2] == 'premium':
            report += f"Premium Validity: {u[3]}\n"
        report += "---------\n"
        
    if len(report) > 4000:
        report = report[:4000] + "...\n(List truncated)"
        
    bot.edit_message_text(report, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=get_back_cancel_markup("admin_panel"))

# Admin Actions
@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def handle_admin_actions(call):
    if int(call.from_user.id) != int(ADMIN_ID): return

    action = call.data
    bot.clear_step_handler_by_chat_id(call.message.chat.id) # Safety clear

    if action == "admin_set_prem":
        msg = bot.send_message(call.message.chat.id, "💎 Enter User ID:", reply_markup=get_back_cancel_markup("admin_panel"))
        bot.register_next_step_handler(msg, ask_premium_duration)
        
    elif action == "admin_set_basic":
        msg = bot.send_message(call.message.chat.id, "👤 Enter User ID to set Basic:", reply_markup=get_back_cancel_markup("admin_panel"))
        bot.register_next_step_handler(msg, perform_set_basic)
        
    elif action == "admin_ban":
        msg = bot.send_message(call.message.chat.id, "🚫 Enter User ID to BAN:", reply_markup=get_back_cancel_markup("admin_panel"))
        bot.register_next_step_handler(msg, lambda m: perform_ban_unban(m, 1))
        
    elif action == "admin_unban":
        msg = bot.send_message(call.message.chat.id, "✅ Enter User ID to UNBAN:", reply_markup=get_back_cancel_markup("admin_panel"))
        bot.register_next_step_handler(msg, lambda m: perform_ban_unban(m, 0))

    elif action == "admin_reset":
        msg = bot.send_message(call.message.chat.id, "🔄 Enter User ID to Reset Usage:", reply_markup=get_back_cancel_markup("admin_panel"))
        bot.register_next_step_handler(msg, perform_reset)

# Helper Functions for Admin
def ask_premium_duration(message):
    try:
        uid = int(message.text)
        user_data['admin_target_uid'] = uid
        msg = bot.send_message(message.chat.id, "📅 Enter Duration (Days):", reply_markup=get_back_cancel_markup("admin_panel"))
        bot.register_next_step_handler(msg, perform_set_premium)
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID.", reply_markup=get_main_menu_keyboard())

def perform_set_premium(message):
    try:
        days = int(message.text)
        uid = user_data.get('admin_target_uid')
        db.set_premium(uid, days)
        bot.send_message(message.chat.id, f"✅ User {uid} set to Premium for {days} days.", reply_markup=get_main_menu_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ Error.", reply_markup=get_main_menu_keyboard())

def perform_set_basic(message):
    try:
        uid = int(message.text)
        db.set_basic(uid)
        bot.send_message(message.chat.id, f"✅ User {uid} set to Basic.", reply_markup=get_main_menu_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ Error.", reply_markup=get_main_menu_keyboard())

def perform_ban_unban(message, status):
    try:
        uid = int(message.text)
        db.set_ban_status(uid, status)
        action = "Banned" if status == 1 else "Unbanned"
        bot.send_message(message.chat.id, f"User {uid} {action}.", reply_markup=get_main_menu_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ Error.", reply_markup=get_main_menu_keyboard())

def perform_reset(message):
    try:
        uid = int(message.text)
        db.reset_user_stats(uid)
        bot.send_message(message.chat.id, f"✅ User {uid} Usage Reset.", reply_markup=get_main_menu_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ Error.", reply_markup=get_main_menu_keyboard())

# Navigation
@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def back_to_main(call):
    # Fix: Clear handlers here too
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_welcome(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_action(call):
    # Fix: This is the MAIN fix for the input bug
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "❌ Cancelled.")
    send_welcome(call.message)

if __name__ == "__main__":
    keep_alive()
    # পোলিং শুরু করার আগে কিছুক্ষণ গ্যাপ রাখা
    import time
    time.sleep(2) 
    bot.infinity_polling(skip_pending=True, timeout=10, long_polling_timeout=5)
