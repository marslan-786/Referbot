import os
import json
import uuid
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
    {"name": "📢 Channel 2", "url": "https://t.me/+_btaEENlL79lMDY1"},
    {"name": "📣 Channel 3", "url": "https://t.me/botsworldtar", "id": -1001826519793},
    {"name": "🔊 Channel 4", "url": "https://t.me/+ddWJ_3i9FKEwYzM9", "id": -1002650001462},
    {"name": "📡 Channel 5", "url": "https://t.me/+ggvGbpCytFU5NzQ1", "id": -1002124581254},
    {"name": "🔗 Channel 6", "url": "https://t.me/+bUxwbe_ZYok2ZWJl"},
    {"name": "📻 Channel 7", "url": "https://t.me/only_possible_world", "id": -1002650289632}
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
        "1. Join all 7 channels below\n"
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
                    # اگر id نہیں ہے تو چیک نہ کرو، بس سکپ کرو
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
            await query.message.delete()
            text = (
                "*📊 Account Details*\n\n"
                f"🪙 Points: `{user_data['points']}`\n"
                f"👥 Referrals: `{user_data['referrals']}`"
            )
            await send_menu_with_banner(query.message.chat_id, context, text, back_to_menu_keyboard())
            
        elif query.data == 'my_referrals':
            await query.message.delete()
            text = f"*👥 Your Referrals*\n\nTotal: `{user_data['referrals']}`"
            await send_menu_with_banner(query.message.chat_id, context, text, back_to_menu_keyboard())

        elif query.data == 'invite_friends':
            await query.message.delete()
            text = (
                "*📨 Invite Friends*\n\n"
                f"Your referral link:\n`https://t.me/{context.bot.username}?start=ref{user_data['referral_code']}`\n\n"
                "Earn 2 points per referral!"
            )
            await send_menu_with_banner(query.message.chat_id, context, text, back_to_menu_keyboard())

        elif query.data == 'withdraw':
            await query.message.delete()
            text = (
                "*💰 Withdraw*\n\n"
                f"Your points: `{user_data['points']}`\n\n"
                "Choose redemption:"
            )
            await send_menu_with_banner(query.message.chat_id, context, text, withdraw_keyboard())

        elif query.data in ['withdraw_40', 'withdraw_70', 'withdraw_100']:
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
            await query.message.delete()
            await show_main_menu(query.message.chat_id, context)

    except Exception as e:
        print(f"Error: {e}")
        await query.message.reply_text("⚠️ Please try again or use /start")
        
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
    
    application.run_polling()

if __name__ == '__main__':
    main()