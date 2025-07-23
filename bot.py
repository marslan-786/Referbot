import os
import json
import uuid
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    MessageHandler,
    filters
)

# Bot configuration
TOKEN = "7902248899:AAHElm3aHJeP3IZiy2SN3jLAgV7ZwRXnvdo"
LOGO_PATH = "logo.png"

# User database file
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

# Update user data
def update_user_data(user_id, data):
    db = load_user_db()
    db[str(user_id)] = data
    save_user_db(db)

# Handle referral
def handle_referral(user_id, referrer_id):
    db = load_user_db()
    
    # Update referrer's data
    if str(referrer_id) in db:
        db[str(referrer_id)]["referrals"] += 1
        db[str(referrer_id)]["points"] += 2
        save_user_db(db)

# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    # Check if this is a referral
    if context.args and context.args[0].startswith('ref'):
        referrer_code = context.args[0][3:]
        db = load_user_db()
        referrer_id = next((uid for uid, data in db.items() if data["referral_code"] == referrer_code), None)
        
        if referrer_id and referrer_id != str(user_id):
            handle_referral(user_id, referrer_id)
    
    # Send welcome message
    with open(LOGO_PATH, 'rb') as logo:
        update.message.reply_photo(
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

# Button callback handler
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    user_data = get_user_data(user_id)
    
    query.answer()

    if query.data == 'my_account':
        account_details = (
            f"📊 Account Details\n\n"
            f"🪙 Points: {user_data['points']}\n"
            f"👥 Referrals: {user_data['referrals']}"
        )
        query.edit_message_text(
            text=account_details,
            reply_markup=back_to_menu_keyboard()
        )
    elif query.data == 'my_referrals':
        referrals_text = (
            f"👥 Your Referrals\n\n"
            f"Total Referrals: {user_data['referrals']}"
        )
        query.edit_message_text(
            text=referrals_text,
            reply_markup=back_to_menu_keyboard()
        )
    elif query.data == 'invite_referrals':
        invite_text = (
            f"📨 Invite Friends\n\n"
            f"Share your referral link and earn 2 points for each successful referral:\n\n"
            f"https://t.me/{context.bot.username}?start=ref{user_data['referral_code']}\n\n"
            f"Each referral earns you 2 points!"
        )
        query.edit_message_text(
            text=invite_text,
            reply_markup=back_to_menu_keyboard()
        )
    elif query.data == 'withdraw':
        query.edit_message_text(
            text=f"💰 Withdraw Points\n\nCurrent Points: {user_data['points']}\nSelect an option:",
            reply_markup=withdraw_keyboard()
        )
    elif query.data == 'withdraw_40':
        if user_data['points'] >= 40:
            user_data['points'] -= 40
            update_user_data(user_id, user_data)
            query.edit_message_text(
                text="🎉 You've redeemed 200 RS Google Play Code!",
                reply_markup=back_to_menu_keyboard()
            )
        else:
            query.edit_message_text(
                text="❌ Error: You need at least 40 points to withdraw",
                reply_markup=withdraw_keyboard()
            )
    elif query.data == 'withdraw_70':
        if user_data['points'] >= 70:
            user_data['points'] -= 70
            update_user_data(user_id, user_data)
            query.edit_message_text(
                text="🎉 You've redeemed 500 RS Google Play Code!",
                reply_markup=back_to_menu_keyboard()
            )
        else:
            query.edit_message_text(
                text="❌ Error: You need at least 70 points to withdraw",
                reply_markup=withdraw_keyboard()
            )
    elif query.data == 'withdraw_100':
        if user_data['points'] >= 100:
            user_data['points'] -= 100
            update_user_data(user_id, user_data)
            query.edit_message_text(
                text="🎉 You've redeemed 1000 RS Google Play Code!",
                reply_markup=back_to_menu_keyboard()
            )
        else:
            query.edit_message_text(
                text="❌ Error: You need at least 100 points to withdraw",
                reply_markup=withdraw_keyboard()
            )
    elif query.data == 'back_to_menu':
        with open(LOGO_PATH, 'rb') as logo:
            query.message.reply_photo(
                photo=logo,
                caption="Welcome to Google Play Redeem Code Bot",
                reply_markup=main_menu_keyboard()
            )
            query.delete_message()

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
    keyboard = [
        [InlineKeyboardButton("Back to Menu", callback_data='back_to_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)



# باقی تمام کوڈ وہی رہے گا، صرف main() فنکشن بدلے گا:

def main() -> None:
    # Initialize user database
    init_user_db()
    
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()