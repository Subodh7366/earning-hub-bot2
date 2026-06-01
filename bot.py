import telebot
from telebot import types
import random
import os
import sys

# --- CONFIGURATION (Railway Environment Variables) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID_ENV = os.environ.get("ADMIN_ID")

if not BOT_TOKEN or not ADMIN_ID_ENV:
    print("ERROR: BOT_TOKEN or ADMIN_ID environment variables are missing!")
    sys.exit(1)

try:
    ADMIN_ID = int(ADMIN_ID_ENV)
except ValueError:
    print("ERROR: ADMIN_ID environment variable must be a numeric integer!")
    sys.exit(1)

CHANNELS = [
    "@thepockeprofit01",
    "@buyandsellapp01",
    "@earnbytelegram1"
]

bot = telebot.TeleBot(BOT_TOKEN)
users_db = {} 

# --- HELPER FUNCTIONS ---
def check_membership(user_id):
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            return False
    return True

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_spin = types.KeyboardButton("🎰 Spin and Win")
    btn_wallet = types.KeyboardButton("💰 Wallet")
    btn_invite = types.KeyboardButton("👥 Invite Friends")
    markup.add(btn_spin)
    markup.add(btn_wallet, btn_invite)
    return markup

# --- HANDLERS ---

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])

    if user_id not in users_db:
        users_db[user_id] = {
            'balance': 0,
            'spins': 1,
            'referred_by': referrer_id if referrer_id != user_id else None,
            'verified': False
        }

    if check_membership(user_id):
        users_db[user_id]['verified'] = True
        ref = users_db[user_id]['referred_by']
        if ref and ref in users_db and not users_db[user_id]['verified']:
            users_db[ref]['spins'] += 1
            try: bot.send_message(ref, "🎉 **Notification:** Aapke referral ne join kiya! Aapko **1 Free Spin** mila. 🎰", parse_mode="Markdown")
            except: pass
        bot.send_message(message.chat.id, "👋 **Welcome Back to Earning Hub Bot!** ✨\n\nNiche diye gaye menu se kamana shuru karein. 👇", reply_markup=get_main_keyboard(), parse_mode="Markdown")
    else:
        markup = types.InlineKeyboardMarkup()
        for idx, ch in enumerate(CHANNELS, 1):
            link = f"https://t.me/{ch.replace('@', '')}"
            markup.add(types.InlineKeyboardButton(f"📢 Join Channel {idx}", url=link))
        markup.add(types.InlineKeyboardButton("✅ Joined / Verify", callback_data="verify_channels"))
        
        bot.send_message(
            message.chat.id, 
            "⚠️ **MANDATORY VERIFICATION** ⚠️\n\n"
            "Bot use karne ke liye aapko humare **3 Channels** join karne honge:\n\n"
            f"1️⃣ {CHANNELS[0]}\n2️⃣ {CHANNELS[1]}\n3️⃣ {CHANNELS[2]}\n\n"
            "👉 Join karne ke baad niche **'Verify'** button par click karein.", 
            reply_markup=markup,
            parse_mode="Markdown"
        )

@bot.callback_query_handler(func=lambda call: call.data == "verify_channels")
def verify_callback(call):
    user_id = call.from_user.id
    if check_membership(user_id):
        bot.answer_callback_query(call.id, "✅ Verification Successful!")
        
        if user_id in users_db and users_db[user_id]['referred_by'] and not users_db[user_id]['verified']:
            ref = users_db[user_id]['referred_by']
            if ref in users_db:
                users_db[ref]['spins'] += 1
                try: bot.send_message(ref, "🎉 **Notification:** Aapke referral ne channel join kar liya! Aapko **1 Free Spin** mila. 🎰", parse_mode="Markdown")
                except: pass
                    
        users_db[user_id]['verified'] = True
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
        # --- CHANGES HERE: Direct Spin option after verification ---
        spin_now_markup = types.InlineKeyboardMarkup()
        spin_now_markup.add(types.InlineKeyboardButton("🎰 Spin Now & Earn!", callback_data="spin_trigger"))
        
        bot.send_message(
            call.message.chat.id, 
            "🥳 **CONGRATULATIONS!** 🥳\n\n"
            "Aapka verification safal raha! Aapko mila hai **1 Free Spin** 🎁\n\n"
            "👇 Niche diye gaye button par click karke abhi apna luck try karein!", 
            reply_markup=spin_now_markup,
            parse_mode="Markdown"
        )
        # Niche ke buttons bhi enable kar diye background mein
        bot.send_message(call.message.chat.id, "ℹ️ Aap niche diye gaye main keyboard menu ka use bhi kar sakte hain.", reply_markup=get_main_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ Aapne abhi tak saare channels join nahi kiye hain!", show_alert=True)

# Main script mechanics handler
@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id
    if not check_membership(user_id):
        bot.send_message(message.chat.id, "❌ Please type /start and join required channels first.")
        return

    if message.text == "🎰 Spin and Win":
        run_spin_logic(message.chat.id, user_id)

    elif message.text == "💰 Wallet":
        show_wallet_logic(message.chat.id, user_id)

    elif message.text == "👥 Invite Friends":
        show_invite_logic(message.chat.id, user_id)

# --- REUSABLE CORE LOGIC ---
def run_spin_logic(chat_id, user_id):
    spins = users_db[user_id]['spins']
    if spins > 0:
        win_amount = random.choice([4, 5, 6])
        users_db[user_id]['balance'] += win_amount
        users_db[user_id]['spins'] -= 1
        
        bot.send_message(
            chat_id, 
            f"🎰 **Lucky Wheel Spin Ho Raha Hai...**\n"
            f"⚡ *Checking your luck...*\n\n"
            f"💥 **💥 WINNER! 💥**\n"
            f"🎁 Congratulations! Aapne **₹{win_amount}** jeete hain!\n\n"
            f"🎫 Remaining Spins: **{users_db[user_id]['spins']}**",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(chat_id, "❌ **Oops! Aapke paas spins nahi hain.**\n\n👥 Apne dosto ko invite karein aur har referral par **1 Free Spin** paayein!", parse_mode="Markdown")

def show_wallet_logic(chat_id, user_id):
    balance = users_db[user_id]['balance']
    markup = types.InlineKeyboardMarkup()
    if balance >= 20:
        markup.add(types.InlineKeyboardButton("💸 Withdraw Request", callback_data="request_withdraw"))
        
    bot.send_message(
        chat_id, 
        f"💳 **MY LIVE WALLET** 💳\n\n"
        f"💵 Current Balance: **₹{balance}**\n"
        f"🎰 Available Spins: **{users_db[user_id]['spins']}**\n\n"
        f"⚠️ *Note: Minimum withdrawal amount threshold ₹20 hai.*", 
        parse_mode="Markdown", 
        reply_markup=markup
    )

def show_invite_logic(chat_id, user_id):
    bot_info = bot.get_me()
    invite_link = f"https://t.me/{bot_info.username}?start={user_id}"
    bot.send_message(
        chat_id, 
        f"👥 **REFER & EARN PROGRAM** 👥\n\n"
        f"Apne dosto ko invite karein aur kamaayein unlimited rewards! Har valid referral par aapko milega:\n"
        f"👉 **1 Free Spin**\n\n"
        f"🔗 **Aapka Personal Invite Link:**\n`{invite_link}`", 
        parse_mode="Markdown"
    )

# Callback inline triggers
@bot.callback_query_handler(func=lambda call: call.data in ["spin_trigger", "request_withdraw"] or call.data.startswith("wd_"))
def handle_callbacks(call):
    user_id = call.from_user.id
    
    if call.data == "spin_trigger":
        if not check_membership(user_id):
            bot.answer_callback_query(call.id, "❌ Verification Required!", show_alert=True)
            return
        bot.delete_message(call.message.chat.id, call.message.message_id)
        run_spin_logic(call.message.chat.id, user_id)
        
    elif call.data == "request_withdraw":
        balance = users_db[user_id]['balance']
        if balance >= 20:
            msg = bot.send_message(call.message.chat.id, "📩 **⚡ INSTANT WITHDRAWAL** ⚡\n\nApni **UPI ID** enter karein jisme aapko payment chahiye:\n_(Jaise: name@upi ya mobile@oksbi)_", parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_upi, balance)
            bot.answer_callback_query(call.id)
        else:
            bot.answer_callback_query(call.id, "❌ Minimum balance ₹20 hona chahiye.", show_alert=True)

    elif call.data.startswith("wd_"):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⚠️ You are not authorized!", show_alert=True)
            return
        action = call.data.split("_")[1]
        target_user_id = int(call.data.split("_")[2])
        
        if action == "approve":
            amount = int(call.data.split("_")[3])
            if target_user_id in users_db and users_db[target_user_id]['balance'] >= amount:
                users_db[target_user_id]['balance'] -= amount
                try: bot.send_message(target_user_id, f"✅ **PAYMENT SUCCESSFUL** ✅\n\nAdmin ne aapka **₹{amount}** ka withdrawal successfully transfer kar diya hai! Apna bank account check karein. 🎉", parse_mode="Markdown")
                except: pass
                bot.edit_message_text(f"✅ User `{target_user_id}` ka ₹{amount} ka withdrawal approve aur deduct ho gaya.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            else:
                bot.edit_message_text("❌ Error: User ke paas ab itna balance nahi hai.", call.message.chat.id, call.message.message_id)
        elif action == "reject":
            try: bot.send_message(target_user_id, "❌ **WITHDRAWAL REJECTED** ❌\n\nAapki withdrawal request admin dwara reject kar di gayi hai. Sahi details ke sath fir se try karein.", parse_mode="Markdown")
            except: pass
            bot.edit_message_text(f"❌ User `{target_user_id}` ki request reject kar di gayi.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

def process_upi(message, balance):
    user_id = message.from_user.id
    upi_id = message.text.strip()
    
    if upi_id in ["🎰 Spin and Win", "💰 Wallet", "👥 Invite Friends", "/start"]:
        bot.send_message(message.chat.id, "❌ **Withdrawal Cancelled.** Sahi UPI ID daalein.")
        return

    if users_db.get(user_id, {}).get('balance', 0) < balance:
        bot.send_message(message.chat.id, "❌ **Error:** Balance check karein.")
        return

    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(
        types.InlineKeyboardButton("✅ Approve & Deduct", callback_data=f"wd_approve_{user_id}_{balance}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"wd_reject_{user_id}")
    )
    
    bot.send_message(
        ADMIN_ID, 
        f"🚨 **NEW WITHDRAWAL REQUEST** 🚨\n\n"
        f"👤 **User Name:** {message.from_user.first_name}\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"💰 **Amount:** *₹{balance}*\n"
        f"📱 **UPI ID:** `{upi_id}`\n\n"
        f"👉 Paise manually pay karne ke baad niche click karein:",
        parse_mode="Markdown",
        reply_markup=admin_markup
    )
    
    bot.send_message(message.chat.id, "⏳ **Request Sent!**\n\nAapki withdrawal request successfully Admin ke paas bhej di gayi hai. Sahi verification ke baad paise credit ho jayenge! ✨")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
