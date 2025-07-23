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
    {"name": "🔔 Channel 1", "url": "https://t.me/only_possible_world"},
    {"name": "📢 Channel 2", "url": "https://t.me/channel2"},
    {"name": "📣 Channel 3", "url": "https://t.me/channel3"},
    {"name": "🔊 Channel 4", "url": "https://t.me/channel4"},
    {"name": "📡 Channel 5", "url": "https://t.me/channel5"},
    {"name": "📻 Channel 6", "url": "https://t.me/channel6"}
]

# Initialize database
def init_user_db():
    if not os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'w') as f:
            json.dump({}, f)

# [Previous database functions remain the same...]

# Start menu keyboard with 6 channels (2 per row)
def start_menu_keyboard():
    keyboard = []
    # Add channel buttons (2 per row)
    for i in range(0, len(CHANNELS), 2):
        row = []
        row.append(InlineKeyboardButton(CHANNELS[i]["name"], url=CHANNELS[i]["url"]))
        if i+1 < len(CHANNELS):
            row.append(InlineKeyboardButton(CHANNELS[i+1]["name"], url=CHANNELS[i+1]["url"]))
        keyboard.append(row)
    # Add Join button
    keyboard.append([InlineKeyboardButton("✅ I've Joined All Channels", callback_data='joined_channels')])
    return InlineKeyboardMarkup(keyboard)

# Main menu keyboard
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("My Account", callback_data='my_account')],
        [InlineKeyboardButton("My Referrals", callback_data='my_referrals')],
        [InlineKeyboardButton("Invite Friends", callback_data='invite_friends')],
        [InlineKeyboardButton("Withdraw", callback_data='withdraw')]
    ])

# [Other keyboard functions remain the same...]

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

# Track users who clicked join button
user_join_clicks = {}

# Start command handler
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
    
    # Show start menu with channels
    await send_menu_with_banner(
        update.message.chat_id,
        context,
        "📢 Please join our official channels:\n\n"
        "1. Join all 6 channels below\n"
        "2. Then click 'I've Joined All Channels'",
        start_menu_keyboard()
    )

# Button callback handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
        
    await query.answer()
    user_id = query.from_user.id

    try:
        if query.data == 'joined_channels':
            if user_id not in user_join_clicks:
                # First click - show message
                user_join_clicks[user_id] = 1
                await query.message.reply_text(
                    "⚠️ Please join all channels first!",
                    reply_markup=start_menu_keyboard()
                )
            else:
                # Second click - proceed to main menu
                await show_main_menu(query.message.chat_id, context)
                
        elif query.data == 'my_account':
            user_data = get_user_data(user_id)
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
            
        # [Rest of the button handlers remain the same...]
            
    except Exception as e:
        print(f"Error: {e}")
        await query.message.reply_text("⚠️ Please try again or use /start")

# [Rest of the functions remain the same...]

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