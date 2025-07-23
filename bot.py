import os
import json
import uuid
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
TOKEN = "7902248899:AAHElm3aHJeP3IZiy2SN3jLAgV7ZwRXnvdo"
LOGO_PATH = "logo.png"
USER_DB_FILE = "user_db.json"

# Initialize user database
def init_user_db():
    if not os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'w') as f:
            json.dump({}, f)

# Load user database
def load_user_db():
    with open(USER_DB_FILE, 'r') as f:
        return json.load(f)

# Save user database
def save_user_db(db):
    with open(USER_DB_FILE, 'w') as f:
        json.dump(db, f)

# Get or create user data
def get_user_data(user_id):
    db = load_user_db()
    if str(user_id) not in db:
        db[str(user_id)] = {
            "points": 0,
            "referrals": 0,
            "referral_code": str(uuid.uuid4())[:8].upper()
        }
        save_user_db(db)
    return db[str(user_id)]

# Handle referral
def handle_referral(user_id, referrer_id):
    db = load_user_db()
    if str(referrer_id) in db:
        db[str(referrer_id)]["referrals"] += 1
        db[str(referrer_id)]["points"] += 2
        save_user_db(db)

# Async start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    if context.args and context.args[0].startswith('ref'):
        referrer_code = context.args[0][3:]
        db = load_user_db()
        referrer_id = next((uid for uid, data in db.items() if data["referral_code"] == referrer_code), None)
        if referrer_id and referrer_id != str(user_id):
            handle_referral(user_id, referrer_id)
    
    with open(LOGO_PATH, 'rb') as logo:
        await update.message.reply_photo(
            photo=logo,
            caption="Welcome to Google Play Redeem Code Bot",
            reply_markup=main_menu_keyboard()
        )

# Main menu keyboard
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("My Account", callback_data='my_account')],
        [InlineKeyboardButton("My Referrals", callback_data='my_referrals')],
        [InlineKeyboardButton("Invite Referrals", callback_data='invite_referrals')],
        [InlineKeyboardButton("Withdraw", callback_data='withdraw')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Async button callback handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user_data(user_id)

    if query.data == 'my_account':
        account_details = (
            f"📊 Account Details\n\n"
            f"🪙 Points: {user_data['points']}\n"
            f"👥 Referrals: {user_data['referrals']}"
        )
        await query.edit_message_text(
            text=account_details,
            reply_markup=back_to_menu_keyboard()
        )
    elif query.data == 'my_referrals':
        referrals_text = f"👥 Your Referrals\n\nTotal Referrals: {user_data['referrals']}"
        await query.edit_message_text(
            text=referrals_text,
            reply_markup=back_to_menu_keyboard()
        )
    elif query.data == 'invite_referrals':
        invite_text = (
            f"📨 Invite Friends\n\nShare your referral link and earn 2 points:\n\n"
            f"https://t.me/{context.bot.username}?start=ref{user_data['referral_code']}"
        )
        await query.edit_message_text(
            text=invite_text,
            reply_markup=back_to_menu_keyboard()
        )
    elif query.data == 'withdraw':
        await query.edit_message_text(
            text=f"💰 Withdraw Points\n\nCurrent Points: {user_data['points']}\nSelect an option:",
            reply_markup=withdraw_keyboard()
        )
    elif query.data == 'withdraw_40':
        if user_data['points'] >= 40:
            user_data['points'] -= 40
            update_user_data(user_id, user_data)
            await query.edit_message_text(
                text="🎉 You've redeemed 200 RS Google Play Code!",
                reply_markup=back_to_menu_keyboard()
            )
        else:
            await query.edit_message_text(
                text="❌ Error: You need at least 40 points",
                reply_markup=withdraw_keyboard()
            )
    elif query.data == 'back_to_menu':
        with open(LOGO_PATH, 'rb') as logo:
            await query.message.reply_photo(
                photo=logo,
                caption="Welcome to Google Play Redeem Code Bot",
                reply_markup=main_menu_keyboard()
            )
            await query.delete_message()

def withdraw_keyboard():
    keyboard = [
        [InlineKeyboardButton("40 Points - 200 RS", callback_data='withdraw_40')],
        [InlineKeyboardButton("70 Points - 500 RS", callback_data='withdraw_70')],
        [InlineKeyboardButton("100 Points - 1000 RS", callback_data='withdraw_100')],
        [InlineKeyboardButton("Back to Menu", callback_data='back_to_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_to_menu_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data='back_to_menu')]])

def main() -> None:
    init_user_db()
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    
    application.run_polling()

if __name__ == '__main__':
    main()