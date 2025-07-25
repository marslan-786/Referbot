import os
import json
import uuid
import random
import asyncio
from auto_redeem import start_auto_redeem, stop_auto_redeem  # اگر الگ فائل میں ہے
from telegram.constants import ChatAction
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# Bot configuration
TOKEN = os.getenv('BOT_TOKEN')
BANNER_PATH = "logo.png"
USER_DB_FILE = "user_db.json"

# Channel configuration (replace with your actual channels)
CHANNELS = [
    {"name": "🔔 Channel 1", "url": "https://t.me/+92ZkRWBBExhmNzY1", "id": -1002215184698},
    {"name": "📣 Channel 2", "url": "https://t.me/+dsm5id0xjLQyZjcx", "id": -1002107245494},
    {"name": "🔊 Channel 3", "url": "https://t.me/botsworldtar", "id": -1001826519793},
    {"name": "📡 Channel 4", "url": "https://t.me/+ddWJ_3i9FKEwYzM9", "id": -1002650001462},
    {"name": "🔗 Channel 5", "url": "https://t.me/+ggvGbpCytFU5NzQ1", "id": -1002124581254},
    {"name": "📻 Channel 6", "url": "https://t.me/only_possible_world", "id": -1002650289632},
    {"name": "📈 Channel 7", "url": "https://t.me/+HCD6LvxtZEg2NDRl"},
    {"name": "🎬 Channel 8", "url": "https://t.me/+2i2Bbv0eaaw4ZDRl"},
    {"name": "🏗️ Channel 9", "url": "https://t.me/+0k61CBIBCQJjNWFl"},
    {"name": "🎤 Channel 10", "url": "https://t.me/+MdCLWsOY3XRmNmY1"}
]

# Track user clicks for channel joining
user_clicks = {}

# Initialize database
def init_user_db():
    if not os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'w') as f:
            json.dump({}, f)

# Load user data
def load_user_db():
    try:
        with open(USER_DB_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save user data
def save_user_db(db):
    with open(USER_DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

# Get or create user
def get_user_data(user_id):
    db = load_user_db()
    user_id_str = str(user_id)
    if user_id_str not in db:
        db[user_id_str] = {
            "points": 0,
            "referrals": 0,
            "referral_code": str(uuid.uuid4())[:8].upper()
        }
        save_user_db(db)
    return db[user_id_str]

# Update user data
def update_user_data(user_id, data):
    db = load_user_db()
    db[str(user_id)] = data
    save_user_db(db)

# Handle referrals
def handle_referral(user_id, referrer_id):
    db = load_user_db()
    referrer_id_str = str(referrer_id)
    if referrer_id_str in db:
        db[referrer_id_str]["referrals"] += 1
        db[referrer_id_str]["points"] += 2
        save_user_db(db)

# Menu keyboards
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("My Account", callback_data='my_account')],
        [InlineKeyboardButton("My Referrals", callback_data='my_referrals')],
        [InlineKeyboardButton("Invite Friends", callback_data='invite_friends')],
        [InlineKeyboardButton("Withdraw", callback_data='withdraw')]
    ])

def withdraw_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("40 Points - Rs.200 Redeem Code", callback_data='withdraw_40')],
        [InlineKeyboardButton("70 Points - Rs.500 Redeem Code", callback_data='withdraw_70')],
        [InlineKeyboardButton("100 Points - Rs.1000 Redeem Code", callback_data='withdraw_100')],
        [InlineKeyboardButton("Back", callback_data='back_to_menu')]
    ])

def back_to_menu_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back_to_menu')]])

# Channel join keyboard
def channel_join_keyboard(show_error=False):
    keyboard = []
    # Add channel buttons (2 per row)
    for i in range(0, len(CHANNELS), 2):
        row = []
        row.append(InlineKeyboardButton(CHANNELS[i]["name"], url=CHANNELS[i]["url"]))
        if i+1 < len(CHANNELS):
            row.append(InlineKeyboardButton(CHANNELS[i+1]["name"], url=CHANNELS[i+1]["url"]))
        keyboard.append(row)
    
    # Add Join button with error message if needed
    button_text = "⚠️ Please Join All Channels First!" if show_error else "✅ I've Joined All Channels"
    keyboard.append([InlineKeyboardButton(button_text, callback_data='joined_channels')])
    
    return InlineKeyboardMarkup(keyboard)

# Send message with banner
async def send_menu_with_banner(chat_id, context, text, reply_markup):
    try:
        with open(BANNER_PATH, 'rb') as banner:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=banner,
                caption=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    except Exception as e:
        print(f"Banner Error: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# Show channel join menu
async def show_channel_join_menu(chat_id, context, user_id):
    # Initialize click count for this user
    user_clicks[user_id] = 0
    await send_menu_with_banner(
        chat_id,
        context,
        "📢 *Please join our official channels:*\n\n"
        "1. Join all 8 channels below\n"
        "2. Then click 'I've Joined All Channels'",
        channel_join_keyboard()
    )

# Show main menu
async def show_main_menu(chat_id, context):
    await send_menu_with_banner(
        chat_id,
        context,
        "*🏠 Main Menu*\n\nWelcome to Google Play Redeem Code Bot",
        main_menu_keyboard()
    )

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
        
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    # Handle referrals
    if context.args and len(context.args) > 0 and context.args[0].startswith('ref'):
        referrer_code = context.args[0][3:]
        db = load_user_db()
        referrer_id = next((uid for uid, data in db.items() if data.get('referral_code') == referrer_code), None)
        if referrer_id and referrer_id != str(user_id):
            handle_referral(user_id, int(referrer_id))
            user_data = get_user_data(user_id)  # Refresh data
    
    # Show channel join menu first
    await show_channel_join_menu(update.message.chat_id, context, user_id)

# Button handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
        
    await query.answer()
    user_id = query.from_user.id
    user_data = get_user_data(user_id)

    try:
        if query.data == 'joined_channels':
            not_joined = []

            for channel in CHANNELS:
                if "id" not in channel:
                    continue

                try:
                    member = await context.bot.get_chat_member(channel["id"], user_id)
                    if member.status not in ['member', 'administrator', 'creator']:
                        not_joined.append(f"❌ You are not a member of {channel['name']}")
                except Exception as e:
                    not_joined.append(f"⚠️ Could not check {channel['name']}")

            if not_joined:
                text = "⚠️ You have not joined all channels:\n\n" + "\n".join(not_joined)
                await query.edit_message_caption(caption=text, reply_markup=channel_join_keyboard(show_error=True))
            else:
                await query.message.delete()
                await show_main_menu(query.message.chat_id, context)

        elif query.data == 'my_account':
            if not await check_required_channels(user_id, query.message.chat_id, context):
                return
            await query.message.delete()
            text = (
                "*📊 Account Details*\n\n"
                f"🪙 Points: `{user_data['points']}`\n"
                f"👥 Referrals: `{user_data['referrals']}`"
            )
            await send_menu_with_banner(query.message.chat_id, context, text, back_to_menu_keyboard())

        elif query.data == 'my_referrals':
            if not await check_required_channels(user_id, query.message.chat_id, context):
                return
            await query.message.delete()
            text = f"*👥 Your Referrals*\n\nTotal: `{user_data['referrals']}`"
            await send_menu_with_banner(query.message.chat_id, context, text, back_to_menu_keyboard())

        elif query.data == 'invite_friends':
            if not await check_required_channels(user_id, query.message.chat_id, context):
                return
            await query.message.delete()
            text = (
                "*📨 Invite Friends*\n\n"
                f"Your referral link:\n`https://t.me/{context.bot.username}?start=ref{user_data['referral_code']}`\n\n"
                "Earn 2 points per referral!"
            )
            await send_menu_with_banner(query.message.chat_id, context, text, back_to_menu_keyboard())

        elif query.data == 'withdraw':
            if not await check_required_channels(user_id, query.message.chat_id, context):
                return
            await query.message.delete()
            text = (
                "*💰 Withdraw*\n\n"
                f"Your points: `{user_data['points']}`\n\n"
                "Choose redemption:"
            )
            await send_menu_with_banner(query.message.chat_id, context, text, withdraw_keyboard())

        elif query.data in ['withdraw_40', 'withdraw_70', 'withdraw_100']:
            if not await check_required_channels(user_id, query.message.chat_id, context):
                return
            await query.message.delete()
            points = int(query.data.split('_')[1])
            amounts = {40: 200, 70: 500, 100: 1000}
            
            if user_data['points'] >= points:
                user_data['points'] -= points
                update_user_data(user_id, user_data)
                text = f"🎉 Success!\n\nYou redeemed Rs.{amounts[points]} code!"
                reply_markup = back_to_menu_keyboard()
            else:
                text = f"❌ You need {points} points!"
                reply_markup = withdraw_keyboard()

            await send_menu_with_banner(query.message.chat_id, context, text, reply_markup)

        elif query.data == 'back_to_menu':
            if not await check_required_channels(user_id, query.message.chat_id, context):
                return
            await query.message.delete()
            await show_main_menu(query.message.chat_id, context)

    except Exception as e:
        print(f"Error: {e}")
        await query.message.reply_text("⚠️ Please try again or use /start")
        
# Check if user is still in all required channels
async def check_required_channels(user_id, chat_id, context):
    not_joined = []

    for channel in CHANNELS:
        if "id" not in channel:
            continue

        try:
            member = await context.bot.get_chat_member(channel["id"], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined.append(channel['name'])
        except Exception:
            not_joined.append(channel['name'])

    if not_joined:
        warning_text = (
            "⚠️ *You have left required channels:*\n\n" +
            "\n".join([f"❌ {ch}" for ch in not_joined]) +
            "\n\nPlease re-join them to continue!"
        )
        await send_menu_with_banner(chat_id, context, warning_text, channel_join_keyboard(show_error=True))
        return False

    return True
        

# --- Send Broadcast Command ---
async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /send Your message here")
        return

    message = ' '.join(context.args)
    db = load_user_db()
    total = 0
    failed = 0

    await update.message.reply_text("📤 Sending message to all users...")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    for user_id in db.keys():
        try:
            await context.bot.send_message(chat_id=int(user_id), text=message)
            total += 1
        except Exception:
            failed += 1
            continue

    await update.message.reply_text(f"✅ Sent to {total} users.\n❌ Failed: {failed}")
    

# 🔴 اصل چینل کی ID یہاں دیں


import asyncio
import random
from telegram import Update
from telegram.ext import ContextTypes

auto_redeem_active = False
auto_redeem_task = None
TARGET_CHANNEL_ID = -1001897280766


async def generate_fake_redeem_message(context):
    fake_user_id = random.randint(100000000, 999999999)

    english_first = ["Ali", "Ayesha", "Umer", "Fatima", "Bilal", "Zara", "John", "Emily", "David", "Sophia", "Liam", "Emma"]
    english_last = ["Khan", "Smith", "Brown", "Johnson", "Lee", "Walker", "Davis", "Allen", "Clark", "Hill", "Butt", "Malik"]

    urdu_first = ["علی", "فاطمہ", "سعد", "ماہین", "ریحان"]
    urdu_last = ["شیخ", "چوہدری", "مغل", "عباسی", "حسینی"]

    hindi_first = ["अमन", "प्रिया", "राहुल", "सोनम", "विवेक", "नेहा", "संगीता", "आर्यन", "कविता", "अंजलि", "निशा", "अभय"]
    hindi_last = ["शर्मा", "गुप्ता", "जैन", "अंसारी", "कुमार", "वर्मा", "दुबे", "चौधरी", "सिद्दीकी", "खान", "मिश्रा", "त्रिपाठी"]

    lang_choice = random.choice(["english", "urdu", "hindi"])
    if lang_choice == "english":
        first = random.choice(english_first)
        last = random.choice(english_last)
    elif lang_choice == "urdu":
        first = random.choice(urdu_first)
        last = random.choice(urdu_last)
    else:
        first = random.choice(hindi_first)
        last = random.choice(hindi_last)

    fake_name = f"{first} {last}"

    message = (
        "𝙁𝙍𝙀𝙀 𝙍𝙀𝘿𝙀𝙀𝙈 𝘾𝙊𝘿𝙀\n\n"
        f"👤 *User ID:* `{fake_user_id}`\n"
        f"👤 *Name:* `{fake_name}`\n"
        f"💳 *Redeem Code:* `Rs.200 successfully redeemed`"
    )

    sent_msg = await context.bot.send_message(chat_id=context.job.chat_id, text=message, parse_mode="Markdown")

    # Forward to channel
    await context.bot.forward_message(
        chat_id=TARGET_CHANNEL_ID,
        from_chat_id=sent_msg.chat_id,
        message_id=sent_msg.message_id
    )


# /gen → one-time fake message
async def gen_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generate_fake_redeem_message(context=type("obj", (object,), {"bot": context.bot, "job": update}))
    await update.message.reply_text("✅ Fake redeem message generated.")


# /active → start auto redeem
async def start_auto_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_redeem_active, auto_redeem_task

    if auto_redeem_active:
        await update.message.reply_text("✅ Already active.")
        return

    auto_redeem_active = True
    await update.message.reply_text("🔄 Auto fake redeem started.")

    async def loop_redeem():
        while auto_redeem_active:
            await generate_fake_redeem_message(context=type("obj", (object,), {"bot": context.bot, "job": update}))
            wait_minutes = random.choice([3, 5, 7, 10])
            await asyncio.sleep(wait_minutes * 60)

    auto_redeem_task = asyncio.create_task(loop_redeem())


# /deactive → stop auto redeem
async def stop_auto_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_redeem_active, auto_redeem_task

    if not auto_redeem_active:
        await update.message.reply_text("⛔ Auto fake redeem is not active.")
        return

    auto_redeem_active = False
    if auto_redeem_task:
        auto_redeem_task.cancel()
        auto_redeem_task = None

    await update.message.reply_text("✅ Auto fake redeem stopped.")
    
# --- Backup Command ---
async def send_backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text("📦 Sending backup files...")

        if os.path.exists("bot.py"):
            await context.bot.send_document(update.effective_chat.id, document=open("bot.py", "rb"))
        else:
            await update.message.reply_text("❌ bot.py file not found.")

        if os.path.exists("user_db.json"):
            await context.bot.send_document(update.effective_chat.id, document=open("user_db.json", "rb"))
        else:
            await update.message.reply_text("❌ user_db.json file not found.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error while sending files: {e}")
        
# --- Reset Command ---
async def reset_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = load_user_db()
    for user_id in db:
        db[user_id]["points"] = 0
        db[user_id]["referrals"] = 0
    save_user_db(db)
    await update.message.reply_text("✅ All users' points and referrals have been reset to 0.")
        
# Status command
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = load_user_db()
    total_users = len(db)
    total_points = sum(user.get("points", 0) for user in db.values())
    total_referrals = sum(user.get("referrals", 0) for user in db.values())

    text = (
        "*📊 Bot Status*\n\n"
        f"👥 Total Users: `{total_users}`\n"
        f"🎯 Total Points Earned: `{total_points}`\n"
        f"🤝 Total Referrals Made: `{total_referrals}`"
    )

    await update.message.reply_text(text, parse_mode='Markdown')

def main() -> None:
    init_user_db()
    application = ApplicationBuilder() \
        .token(TOKEN) \
        .concurrent_updates(True) \
        .build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler('send', send_broadcast))
    application.add_handler(CommandHandler('reset', reset_users))
    application.add_handler(CommandHandler('backup', send_backup))
    application.add_handler(CommandHandler('gen', generate_fake_redeem))
    application.add_handler(CommandHandler("active", start_auto_redeem))
    application.add_handler(CommandHandler("deactive", stop_auto_redeem))
    
    application.run_polling()

if __name__ == '__main__':
    main()