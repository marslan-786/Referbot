import os
import json
import uuid
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Bot configuration
TOKEN = os.getenv('BOT_TOKEN')  # Environment variable سے ٹوکن لیں
LOGO_PATH = "logo.png"
USER_DB_FILE = "user_db.json"

# Initialize user database
def init_user_db():
    if not os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'w') as f:
            json.dump({}, f)

# Load user database
def load_user_db():
    try:
        with open(USER_DB_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save user database
def save_user_db(db):
    with open(USER_DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

# Get or create user data
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

# Handle referral
def handle_referral(user_id, referrer_id):
    db = load_user_db()
    referrer_id_str = str(referrer_id)
    if referrer_id_str in db:
        db[referrer_id_str]["referrals"] += 1
        db[referrer_id_str]["points"] += 2
        save_user_db(db)

# Main menu keyboard
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("My Account", callback_data='my_account')],
        [InlineKeyboardButton("My Referrals", callback_data='my_referrals')],
        [InlineKeyboardButton("Invite Friends", callback_data='invite_friends')],
        [InlineKeyboardButton("Withdraw", callback_data='withdraw')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Withdraw keyboard
def withdraw_keyboard():
    keyboard = [
        [InlineKeyboardButton("40 Points - 200 RS", callback_data='withdraw_40')],
        [InlineKeyboardButton("70 Points - 500 RS", callback_data='withdraw_70')],
        [InlineKeyboardButton("100 Points - 1000 RS", callback_data='withdraw_100')],
        [InlineKeyboardButton("Back to Menu", callback_data='back_to_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Back to menu keyboard
def back_to_menu_keyboard():
    keyboard = [[InlineKeyboardButton("Back to Menu", callback_data='back_to_menu')]]
    return InlineKeyboardMarkup(keyboard)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
        
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    if context.args and len(context.args) > 0 and context.args[0].startswith('ref'):
        referrer_code = context.args[0][3:]
        db = load_user_db()
        referrer_id = next((uid for uid, data in db.items() if data.get('referral_code') == referrer_code), None)
        if referrer_id and referrer_id != str(user_id):
            handle_referral(user_id, int(referrer_id))
    
    try:
        with open(LOGO_PATH, 'rb') as logo:
            await update.message.reply_photo(
                photo=logo,
                caption="Welcome to Google Play Redeem Code Bot",
                reply_markup=main_menu_keyboard()
            )
    except Exception as e:
        print(f"Start Error: {e}")
        await update.message.reply_text(
            "Welcome to Google Play Redeem Code Bot",
            reply_markup=main_menu_keyboard()
        )

# Button callback handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
        
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user_data(user_id)

    try:
        if query.data == 'my_account':
            text = (
                f"📊 Account Details\n\n"
                f"🪙 Points: {user_data['points']}\n"
                f"👥 Referrals: {user_data['referrals']}"
            )
            await safe_edit_message(query, text, back_to_menu_keyboard())
            
        elif query.data == 'my_referrals':
            text = f"👥 Your Referrals\n\nTotal Referrals: {user_data['referrals']}"
            await safe_edit_message(query, text, back_to_menu_keyboard())
            
        elif query.data == 'invite_friends':
            text = (
                f"📨 Invite Friends\n\nShare your referral link and earn 2 points:\n\n"
                f"https://t.me/{context.bot.username}?start=ref{user_data['referral_code']}\n\n"
                f"Each referral earns you 2 points!"
            )
            await safe_edit_message(query, text, back_to_menu_keyboard())
            
        elif query.data == 'withdraw':
            text = f"💰 Withdraw Points\n\nCurrent Points: {user_data['points']}\nSelect an option:"
            await safe_edit_message(query, text, withdraw_keyboard())
            
        elif query.data == 'withdraw_40':
            if user_data['points'] >= 40:
                user_data['points'] -= 40
                update_user_data(user_id, user_data)
                await safe_edit_message(query, "🎉 You've redeemed 200 RS Google Play Code!", back_to_menu_keyboard())
            else:
                await safe_edit_message(query, "❌ Error: You need at least 40 points", withdraw_keyboard())
                
        elif query.data == 'back_to_menu':
            try:
                with open(LOGO_PATH, 'rb') as logo:
                    await query.message.reply_photo(
                        photo=logo,
                        caption="Welcome to Google Play Redeem Code Bot",
                        reply_markup=main_menu_keyboard()
                    )
                    await query.delete_message()
            except Exception as e:
                print(f"Back to Menu Error: {e}")
                await query.message.reply_text(
                    "Welcome to Google Play Redeem Code Bot",
                    reply_markup=main_menu_keyboard()
                )
                
    except Exception as e:
        print(f"Button Error: {e}")
        await query.message.reply_text("An error occurred. Please try /start again.")

# Safe message edit function
async def safe_edit_message(query, text, reply_markup=None):
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Edit Message Error: {e}")
        await query.message.reply_text(
            text,
            reply_markup=reply_markup
        )
        await query.delete_message()

def main() -> None:
    # Initialize database
    init_user_db()
    
    # Create application with proper configuration
    application = ApplicationBuilder() \
        .token(TOKEN) \
        .concurrent_updates(True) \
        .http_version("1.1") \
        .get_updates_http_version("1.1") \
        .build()
    
    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    
    # Run application with error handling
    try:
        application.run_polling()
    except Exception as e:
        print(f"Application Error: {e}")
    finally:
        print("Bot stopped")

if __name__ == '__main__':
    main()