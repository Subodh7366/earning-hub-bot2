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

# --- MEMORY TEMPORARY STORAGE FOR WITHDRAWAL STATES ---
withdraw_state = {} # Format: { user_id: { 'upi': None } }

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
        bot.send_message(call.message.chat.id, "ℹ️ Aap niche diye gaye main keyboard menu ka use bhi kar sakte hain.", reply_markup=get_main_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ Aapne abhi tak saare channels join nahi kiye hain!", show_alert=True)

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

# --- CORE LOGIC FUNCTIONS ---
def run_spin_logic(chat_id, user_id):
    spins = users_db[user_id]['spins']
    if spins > 0:
        win_amount = random.choice([4, 5,])
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
    balance = users_db.get(user_id, {}).get('balance', 0)
    spins = users_db.get(user_id, {}).get('spins', 0)
    
    # FIX: Button hamesha show hoga niche text ke, chahe balance kam hi kyu na ho!
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💸 Withdraw Request", callback_data="request_withdraw"))
        
    bot.send_message(
        chat_id, 
        f"💳 **MY LIVE WALLET** 💳\n\n"
        f"💵 Current Balance: **₹{balance}**\n"
        f"🎰 Available Spins: **{spins}**\n\n"
        f"⚠️ *Note: Minimum withdrawal amount ₹20 hai.*", 
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

# --- CALLBACKS & WITHDRAW SYSTEM WITH AMOUNT + UPI ---

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
        balance = users_db.get(user_id, {}).get('balance', 0)
        
        # 1. Check agar minimum balance ₹20 se kam hai
        if balance < 20:
            bot.answer_callback_query(call.id, f"❌ Aapka balance ₹{balance} hai. Minimum withdrawal ₹20 hona chahiye!", show_alert=True)
            return
            
        bot.answer_callback_query(call.id)
        # 2. Agar ₹20 se upar hai, toh UPI ID maango
        msg = bot.send_message(call.message.chat.id, "📩 **⚡ INSTANT WITHDRAWAL (Step 1/2)** ⚡\n\nApni **UPI ID** enter karein:\n_(Jaise: example@upi ya 9876543210@paytm)_", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_upi_step)

    elif call.data.startswith("wd_"):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⚠️ You are not authorized!", show_alert=True)
            return
        action = call.data.split("_")[1]
        target_user_id = int(call.data.split("_")[2])
        amount = int(call.data.split("_")[3])
        
        if action == "approve":
            if target_user_id in users_db and users_db[target_user_id]['balance'] >= amount:
                users_db[target_user_id]['balance'] -= amount
                try: bot.send_message(target_user_id, f"✅ **PAYMENT SUCCESSFUL** ✅\n\nAdmin ne aapka **₹{amount}** ka withdrawal successfully transfer kar diya hai! 🎉", parse_mode="Markdown")
                except: pass
                bot.edit_message_text(f"✅ User `{target_user_id}` ka ₹{amount} ka withdrawal approve aur deduct ho gaya.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            else:
                bot.edit_message_text("❌ Error: User ke paas ab itna balance nahi hai.", call.message.chat.id, call.message.message_id)
        elif action == "reject":
            try: bot.send_message(target_user_id, f"❌ **WITHDRAWAL REJECTED** ❌\n\nAapki ₹{amount} ki withdrawal request admin dwara reject kar di gayi hai.", parse_mode="Markdown")
            except: pass
            bot.edit_message_text(f"❌ User `{target_user_id}` ki ₹{amount} ki request reject kar di gayi.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# Step 1: Handle UPI ID Input
def process_upi_step(message):
    user_id = message.from_user.id
    upi_id = message.text.strip()
    
    if upi_id in ["🎰 Spin and Win", "💰 Wallet", "👥 Invite Friends", "/start"]:
        bot.send_message(message.chat.id, "❌ Withdrawal cancelled.")
        return

    # Temporarily save UPI ID
    withdraw_state[user_id] = {'upi': upi_id}
    
    # Now ask for Amount
    msg = bot.send_message(message.chat.id, "💰 **⚡ INSTANT WITHDRAWAL (Step 2/2)** ⚡\n\nJitna **Amount (Paise)** nikalna hai woh enter karein:\n_(Note: Amount kam se kam ₹20 hona chahiye)_", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_amount_step)

# Step 2: Handle Amount Input & Submit to Admin
def process_amount_step(message):
    user_id = message.from_user.id
    amount_text = message.text.strip()
    balance = users_db.get(user_id, {}).get('balance', 0)
    
    if amount_text in ["🎰 Spin and Win", "💰 Wallet", "👥 Invite Friends", "/start"]:
        bot.send_message(message.chat.id, "❌ Withdrawal cancelled.")
        return

    # Check validity of amount digits
    if not amount_text.isdigit():
        bot.send_message(message.chat.id, "❌ **Galat Amount!** Sirf numbers daalein (Jaise: 25, 50, 100). Please fir se apply karein.")
        return
        
    amount = int(amount_text)
    
    # Validation 1: Check if amount is less than 20
    if amount < 20:
        bot.send_message(message.chat.id, "❌ **Error:** Minimum withdrawal amount ₹20 hona chahiye. Please fir se apply karein.")
        return
        
    # Validation 2: Check if user has enough balance
    if amount > balance:
        bot.send_message(message.chat.id, f"❌ **Insufficient Balance!** Aapka balance sirf ₹{balance} hai aur aap ₹{amount} nikal rahe hain. Please fir se try karein.")
        return

    upi_id = withdraw_state.get(user_id, {}).get('upi', 'Not Found')

    # Send Notification to ADMIN with amount and UPI ID
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(
        types.InlineKeyboardButton("✅ Approve & Deduct", callback_data=f"wd_approve_{user_id}_{amount}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"wd_reject_{user_id}_{amount}")
    )
    
    bot.send_message(
        ADMIN_ID, 
        f"🚨 **NEW WITHDRAWAL REQUEST** 🚨\n\n"
        f"👤 **User Name:** {message.from_user.first_name}\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"💰 **Requested Amount:** *₹{amount}*\n"
        f"📱 **User UPI ID:** `{upi_id}`\n\n"
        f"👉 Manual payment karne ke baad niche decision lein:",
        parse_mode="Markdown",
        reply_markup=admin_markup
    )
    
    bot.send_message(message.chat.id, f"⏳ **Request Submitted Successfully!**\n\n💸 Amount: **₹{amount}**\n📱 UPI: `{upi_id}`\n\nAdmin jaise hi payment verify karega, aapka balance deduct ho jayega! ✨")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
