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
    {"name": "🔔 Channel 1", "url": "https://t.me/channel1"},
    {"name": "📢 Channel 2", "url": "https://t.me/channel2"},
    {"name": "📣 Channel 3", "url": "https://t.me/channel3"},
    {"name": "🔊 Channel 4", "url": "https://t.me/channel4"},
    {"name": "📡 Channel 5", "url": "https://t.me/channel5"},
    {"name": "📻 Channel 6", "url": "https://t.me/channel6"}
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
        [InlineKeyboardButton("40 Points - Rs.200", callback_data='withdraw_40')],
        [InlineKeyboardButton("70 Points - Rs.500", callback_data='withdraw_70')],
        [InlineKeyboardButton("100 Points - Rs.1000", callback_data='withdraw_100')],
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
        "1. Join all 6 channels below\n"
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
            # Track clicks
            user_clicks[user_id] = user_clicks.get(user_id, 0) + 1
            
            if user_clicks[user_id] == 1:
                # First click - show error message
                await query.edit_message_reply_markup(
                    reply_markup=channel_join_keyboard(show_error=True)
                )
            else:
                # Second click - proceed to main menu
                await show_main_menu(query.message.chat_id, context)
                
        elif query.data == 'my_account':
            text = (
                "*📊 Account Details*\n\n"
                f"🪙 Points: `{user_data['points']}`\n"
                f"👥 Referrals: `{user_data['referrals']}`"
            )
            await send_menu_with_banner(
                query.message.chat_id,
                context,
                text,
                back_to_menu_keyboard()
            )
            
        elif query.data == 'my_referrals':
            text = f"*👥 Your Referrals*\n\nTotal: `{user_data['referrals']}`"
            await send_menu_with_banner(
                query.message.chat_id,
                context,
                text,
                back_to_menu_keyboard()
            )
            
        elif query.data == 'invite_friends':
            text = (
                "*📨 Invite Friends*\n\n"
                f"Your referral link:\n`https://t.me/{context.bot.username}?start=ref{user_data['referral_code']}`\n\n"
                "Earn 2 points per referral!"
            )
            await send_menu_with_banner(
                query.message.chat_id,
                context,
                text,
                back_to_menu_keyboard()
            )
            
        elif query.data == 'withdraw':
            text = (
                "*💰 Withdraw*\n\n"
                f"Your points: `{user_data['points']}`\n\n"
                "Choose redemption:"
            )
            await send_menu_with_banner(
                query.message.chat_id,
                context,
                text,
                withdraw_keyboard()
            )
            
        elif query.data in ['withdraw_40', 'withdraw_70', 'withdraw_100']:
            points = int(query.data.split('_')[1])
            amounts = {40: 200, 70: 500, 100: 1000}
            
            if user_data['points'] >= points:
                user_data['points'] -= points
                update_user_data(user_id, user_data)
                text = f"🎉 Success!\n\nYou redeemed Rs.{amounts[points]} code!"
            else:
                text = f"❌ You need {points} points!"
                
            await send_menu_with_banner(
                query.message.chat_id,
                context,
                text,
                back_to_menu_keyboard() if user_data['points'] >= points else withdraw_keyboard()
            )
            
        elif query.data == 'back_to_menu':
            await show_main_menu(query.message.chat_id, context)
            
    except Exception as e:
        print(f"Error: {e}")
        await query.message.reply_text("⚠️ Please try again or use /start")

def main() -> None:
    init_user_db()
    application = ApplicationBuilder() \
        .token(TOKEN) \
        .concurrent_updates(True) \
        .build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    
    application.run_polling()

if __name__ == '__main__':
    main()