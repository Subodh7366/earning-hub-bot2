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
            bot.send_message(ref, "🎉 Aapke referral ne join kiya! Aapko 1 free spin mila.")
        bot.send_message(message.chat.id, "👋 Welcome back to Earning Hub Bot!", reply_markup=get_main_keyboard())
    else:
        markup = types.InlineKeyboardMarkup()
        for idx, ch in enumerate(CHANNELS, 1):
            link = f"https://t.me/{ch.replace('@', '')}"
            markup.add(types.InlineKeyboardButton(f"Join Channel {idx}", url=link))
        markup.add(types.InlineKeyboardButton("✅ Joined / Verify", callback_data="verify_channels"))
        
        bot.send_message(
            message.chat.id, 
            "⚠️ Bot use karne ke liye aapko humare 3 channels join karne honge:\n\n"
            f"1️⃣ {CHANNELS[0]}\n2️⃣ {CHANNELS[1]}\n3️⃣ {CHANNELS[2]}\n\n"
            "Join karne ke baad niche 'Verify' button par click karein.", 
            reply_markup=markup
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
                try: bot.send_message(ref, "🎉 Aapke referral ne channel join kar liya! Aapko 1 free spin mila.")
                except: pass
                    
        users_db[user_id]['verified'] = True
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "🎉 Aapka verification safal raha! Ab aap kama sakte hain.", reply_markup=get_main_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ Aapne abhi tak saare channels join nahi kiye hain!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id
    if not check_membership(user_id):
        bot.send_message(message.chat.id, "❌ Please type /start and join required channels first.")
        return

    if message.text == "🎰 Spin and Win":
        spins = users_db[user_id]['spins']
        if spins > 0:
            win_amount = random.choice([4, 5, 6])
            users_db[user_id]['balance'] += win_amount
            users_db[user_id]['spins'] -= 1
            bot.send_message(message.chat.id, f"🎰 Spin ghum raha hai...\n\n💰 Congratulations! Aapne ₹{win_amount} jeete!\nRemaining Spins: {users_db[user_id]['spins']}")
        else:
            bot.send_message(message.chat.id, "❌ Aapke paas spins nahi hain! Friends ko invite karein aur spin kamayein.")

    elif message.text == "💰 Wallet":
        balance = users_db[user_id]['balance']
        markup = types.InlineKeyboardMarkup()
        if balance >= 20:
            markup.add(types.InlineKeyboardButton("💸 Withdraw Request", callback_data="request_withdraw"))
        bot.send_message(message.chat.id, f"💳 **Aapka Wallet**\n\n💰 Current Balance: ₹{balance}\n🎰 Available Spins: {users_db[user_id]['spins']}\n\nℹ️ Minimum withdrawal amount ₹20 hai.", parse_mode="Markdown", reply_markup=markup)

    elif message.text == "👥 Invite Friends":
        bot_info = bot.get_me()
        invite_link = f"https://t.me/{bot_info.username}?start={user_id}"
        bot.send_message(message.chat.id, f"👥 **Refer & Earn Program**\n\nApne dosto ko invite karein aur har referral par **1 Free Spin** paayein!\n\n🔗 Aapka Invite Link:\n`{invite_link}`", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "request_withdraw")
def withdraw_request(call):
    user_id = call.from_user.id
    balance = users_db[user_id]['balance']
    if balance >= 20:
        admin_markup = types.InlineKeyboardMarkup()
        admin_markup.add(
            types.InlineKeyboardButton("✅ Approve & Deduct", callback_data=f"wd_approve_{user_id}_{balance}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"wd_reject_{user_id}")
        )
        bot.send_message(ADMIN_ID, f"🚨 **New Withdrawal Request!**\n\n👤 User: {call.from_user.first_name} (ID: `{user_id}`)\n💰 Amount: ₹{balance}\n\nPaise manually pay karne ke baad niche button dabaayein.", parse_mode="Markdown", reply_markup=admin_markup)
        bot.answer_callback_query(call.id, "⏳ Withdrawal request admin ko bhej di gayi hai.", show_alert=True)
        bot.edit_message_text("⏳ Your withdrawal is under review by admin.", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Minimum balance ₹20 hona chahiye.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("wd_"))
def admin_process_withdrawal(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⚠️ You are not authorized!", show_alert=True)
        return
    action = call.data.split("_")[1]
    target_user_id = int(call.data.split("_")[2])
    
    if action == "approve":
        amount = int(call.data.split("_")[3])
        if target_user_id in users_db and users_db[target_user_id]['balance'] >= amount:
            users_db[target_user_id]['balance'] -= amount
            try: bot.send_message(target_user_id, f"✅ Admin ne aapka ₹{amount} ka withdrawal successfully transfer kar diya hai!")
            except: pass
            bot.edit_message_text(f"✅ User `{target_user_id}` ka ₹{amount} ka withdrawal approve aur deduct ho gaya.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text("❌ Error: User ke paas ab itna balance nahi hai.", call.message.chat.id, call.message.message_id)
    elif action == "reject":
        try: bot.send_message(target_user_id, "❌ Aapki withdrawal request admin dwara reject kar di gayi hai.")
        except: pass
        bot.edit_message_text(f"❌ User `{target_user_id}` ki request reject kar di gayi.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
