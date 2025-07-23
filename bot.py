import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, Application

logging.basicConfig(level=logging.INFO)

# ---------- CONFIG ----------
BOT_TOKEN = "7902248899:AAHElm3aHJeP3IZiy2SN3jLAgV7ZwRXnvdo"

REQUIRED_CHANNELS = [
    {"name": "Channel 1", "link": "https://t.me/+92ZkRWBBExhmNzY1"},
    {"name": "Channel 2", "link": "https://t.me/+dsm5id0xjLQyZjcx"},
    {"name": "Channel 3", "link": "https://t.me/+ggvGbpCytFU5NzQ1"},
    {"name": "Channel 4", "link": "https://t.me/+ddWJ_3i9FKEwYzM9"},
    {"name": "Channel 5", "link": "https://t.me/+VCRRpYGKMz8xY2U0"},
    {"name": "Channel 6", "link": "https://t.me/botsworldtar"},
]

OWNER_ID = 8003357608
channel_cache = {}
user_join_status = {}
admin_channels = []  # global variable


import json
import os

USER_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f, indent=4)
# ---------- UTILS ----------
async def get_channel_id(bot, link: str) -> int:
    if link in channel_cache:
        return channel_cache[link]
    chat = await bot.get_chat(link)
    channel_cache[link] = chat.id
    return chat.id


async def has_joined_all_channels(bot, user_id: int) -> (bool, list):
    not_joined_channels = []

    for channel in REQUIRED_CHANNELS:
        try:
            chat_id = await get_channel_id(bot, channel['link'])
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined_channels.append(channel['name'])
        except Exception as e:
            logging.warning(f"Error checking membership for {channel['name']}: {e}")
            not_joined_channels.append(channel['name'])

    return (len(not_joined_channels) == 0, not_joined_channels)


# ---------- HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text  # /start or /start referralcode

    users = load_users()

    # Referral code extract
    referral_code = None
    if text and len(text.split()) > 1:
        referral_code = text.split()[1]

    # ✅ Make sure user exists in users.json even without referral
    if str(user.id) not in users:
        users[str(user.id)] = {"referrals": [], "points": 0}
        save_users(users)

    # 🛡 Owner bypasses all checks
    if user.id == OWNER_ID:
        await send_main_menu(update)
        return

    # 💡 Referral processing (if provided)
    if referral_code:
        referrer_id = referral_code
        if referrer_id != str(user.id):  # Prevent self-referral
            if referrer_id not in users:
                users[referrer_id] = {"referrals": [], "points": 0}

            if str(user.id) not in users[referrer_id]["referrals"]:
                users[referrer_id]["referrals"].append(str(user.id))
                users[referrer_id]["points"] += 2

                save_users(users)

                # Notify referrer
                try:
                    referrer_chat_id = int(referrer_id)
                    referred_username = user.username or "NoUsername"
                    referred_id = user.id
                    msg = (
                        f"🎉 Congratulations! You have a new referral.\n\n"
                        f"User: @{referred_username}\n"
                        f"User ID: {referred_id}\n"
                        f"You earned 2 points."
                    )
                    await context.bot.send_message(chat_id=referrer_chat_id, text=msg)
                except Exception as e:
                    print(f"Error sending referral notification: {e}")

    # ✅ Show join channels prompt unconditionally
    await show_join_channels(update)


async def show_join_channels(update: Update):
    keyboard = []
    temp_row = []
    for i, channel in enumerate(REQUIRED_CHANNELS, 1):
        temp_row.append(InlineKeyboardButton(channel["name"], url=channel["link"]))
        if i % 2 == 0:
            keyboard.append(temp_row)
            temp_row = []
    if temp_row:
        keyboard.append(temp_row)

    keyboard.append([InlineKeyboardButton("✅ Joined", callback_data="check_joined")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    with open("banner.jpg", "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption="👇 Please join all channels to use the bot 👇",
            reply_markup=reply_markup
        )


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    query = update.callback_query
    await query.answer()

    if not data.get("has_seen_error"):
        data["has_seen_error"] = True
        await query.message.reply_text("❌ Please first join all required channels before proceeding.")
    else:
        # صرف میسج ڈیلیٹ کرنے کی کوشش کریں، اگر ہو سکے
        try:
            await query.message.delete()
        except Exception as e:
            print(f"Message delete error in check_joined: {e}")

        await send_main_menu(update)


async def send_main_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("👤 My Account", callback_data="my_account_handler")],
        [InlineKeyboardButton("👥 My Referrals", callback_data="my_referrals_handler")],
        [InlineKeyboardButton("📨 Invite Referral Link", callback_data="invite_referral_handler")],
        [InlineKeyboardButton("💵 Withdrawal", callback_data="withdraw_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    photo_path = "banner.jpg"

    if update.message:
        await update.message.reply_photo(photo=open(photo_path, "rb"), caption="🏠 Welcome to the Main Menu:", reply_markup=reply_markup)
    elif update.callback_query:
        # پہلے میسج ڈیلیٹ کرنے کی کوشش کریں لیکن error کو ignore کریں اگر ہو جائے تو
        try:
            await update.callback_query.message.delete()
        except Exception as e:
            print(f"Message delete error in send_main_menu: {e}")

        await update.callback_query.message.chat.send_photo(photo=open(photo_path, "rb"), caption="🏠 Welcome to the Main Menu:", reply_markup=reply_markup)
    else:
        print("Neither message nor callback_query found in update.")


# یہ بھی چیک کریں کہ آپ کا handler 'check_joined' کے لیے صحیح طریقے سے لگا ہوا ہے:
# app.add_handler(CallbackQueryHandler(check_joined, pattern="^check_joined$"))
        
        
async def my_account_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)

    with open("users.json", "r") as f:
        users = json.load(f)

    if user_id not in users:
        await query.answer("User not registered.")
        return

    user_data = users[user_id]
    username = user_data.get("username", "N/A")
    balance = user_data.get("balance", 0)
    referral_code = user_data.get("referral_code", "N/A")
    referrals = len(user_data.get("referrals", []))

    text = f"""👤 <b>My Account</b>

🆔 <b>User ID:</b> <code>{user_id}</code>
👤 <b>Username:</b> @{username}
💰 <b>Balance:</b> {balance} PKR
🔗 <b>Referral Code:</b> <code>{referral_code}</code>
👥 <b>Total Referrals:</b> {referrals}
"""

    keyboard = [
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.delete()
    await query.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
# مائی ریفرل مینو
async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # users.json سے ڈیٹا لوڈ کریں
    with open("users.json", "r") as f:
        users = json.load(f)

    if user_id not in users:
        await update.message.reply_text("⛔ You are not registered yet.")
        return

    user = users[user_id]
    referral_code = user.get("referral_code", "N/A")
    referrals = user.get("referrals", [])
    referral_earning = user.get("referral_earning", 0)

    # میسج تیار کریں
    text = (
        f"📢 *Your Referral Info:*\n\n"
        f"🔗 *Referral Code:* `{referral_code}`\n"
        f"👥 *Total Referrals:* {len(referrals)}\n"
        f"💰 *Referral Earnings:* {referral_earning} PKR\n"
    )

    # بیک بٹن کے ساتھ مینو
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(
        photo=open("banner.jpg", "rb"),
        caption=text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
# انوائٹ ریفرل لنک مینو
async def invite_referral_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # users.json سے ڈیٹا لوڈ کریں
    with open("users.json", "r") as f:
        users = json.load(f)

    if user_id not in users:
        await update.message.reply_text("⛔ You are not registered yet.")
        return

    user = users[user_id]
    referral_code = user.get("referral_code", "N/A")

    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"

    text = (
        f"📩 *Invite Your Friends!*\n\n"
        f"🔗 *Your Referral Link:*\n`{referral_link}`\n\n"
        f"👥 When someone joins using your link, you'll earn bonus rewards.\n"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(
        photo=open("banner.jpg", "rb"),
        caption=text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
async def withdraw_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    with open("users.json", "r") as f:
        users = json.load(f)

    if user_id not in users:
        await update.message.reply_text("⛔ You are not registered yet.")
        return

    points = users[user_id].get("points", 0)

    text = (
        f"💸 *Withdraw Menu*\n\n"
        f"💰 Your Current Points: *{points}*\n\n"
        f"Choose one of the options below to redeem your points:"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎁 40 Points = Rs. 200", callback_data="withdraw_40"),
            InlineKeyboardButton("🎁 70 Points = Rs. 500", callback_data="withdraw_70"),
            InlineKeyboardButton("🎁 100 Points = Rs. 1000", callback_data="withdraw_100"),
        ],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ]

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
async def process_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    data = query.data  # withdraw_40, withdraw_70, withdraw_100

    with open("users.json", "r") as f:
        users = json.load(f)

    if user_id not in users:
        await query.edit_message_text("⛔ You are not registered yet.")
        return

    user = users[user_id]
    points = user.get("points", 0)

    # پوائنٹس ریڈیم ویلیوز
    withdraw_map = {
        "withdraw_40": (40, 200),
        "withdraw_70": (70, 500),
        "withdraw_100": (100, 1000),
    }

    required_points, amount = withdraw_map.get(data, (None, None))

    if required_points is None:
        await query.edit_message_text("❌ Invalid option selected.")
        return

    if points < required_points:
        await query.edit_message_text(f"🚫 You need *{required_points} points* to redeem Rs. {amount}.\nYou only have *{points} points*.",
                                      parse_mode=ParseMode.MARKDOWN)
        return

    # پوائنٹس کم کرو
    users[user_id]["points"] -= required_points

    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

    await query.edit_message_text(
        f"✅ Your request to redeem Rs. {amount} has been received.\n"
        f"📤 Remaining Points: *{users[user_id]['points']}*\n\n"
        f"👨‍💼 Our team will contact you soon for the payment.",
        parse_mode=ParseMode.MARKDOWN
    )
        
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_main_menu(update)
    
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "my_account_handler":
        await my_account_menu(update, context)

    elif data == "my_referrals_handler":
        await my_referrals(update, context)

    elif data == "invite_referral_handler":
        await invite_referral_link(update, context)

    elif data == "back_to_menu":
        await query.message.delete()
        await send_main_menu(update)

    else:
        await query.answer("Unknown action!")


# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_joined, pattern="^check_joined$"))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(my_account_menu, pattern="^my_account$"))
    app.add_handler(CallbackQueryHandler(my_referrals, pattern="^my_referrals$"))
    app.add_handler(CallbackQueryHandler(invite_referral_link, pattern="^invite_referral$"))
    app.add_handler(CallbackQueryHandler(withdraw_menu, pattern="^withdraw_menu$"))
    app.add_handler(CallbackQueryHandler(process_withdrawal, pattern="^withdraw_"))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()