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
BANNER_PATH = "logo.png"  # Using logo.png as banner for all menus
USER_DB_FILE = "user_db.json"

# Initialize user database
def init_user_db():
    if not os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'w') as f:
            json.dump({}, f)

# [Previous database functions remain the same...]

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
        [InlineKeyboardButton("Back to Menu", callback_data='back_to_menu')]
    ])

def back_to_menu_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data='back_to_menu')]])

# Send message with banner/logo
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
    
    await send_menu_with_banner(
        update.message.chat_id,
        context,
        "*🏠 Main Menu*\n\nWelcome to Google Play Redeem Code Bot",
        main_menu_keyboard()
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
                "*📊 Account Details*\n\n"
                f"🪙 *Points:* `{user_data['points']}`\n"
                f"👥 *Referrals:* `{user_data['referrals']}`"
            )
            await send_menu_with_banner(
                query.message.chat_id,
                context,
                text,
                back_to_menu_keyboard()
            )
            
        elif query.data == 'my_referrals':
            text = f"*👥 Your Referrals*\n\n📊 *Total Referrals:* `{user_data['referrals']}`"
            await send_menu_with_banner(
                query.message.chat_id,
                context,
                text,
                back_to_menu_keyboard()
            )
            
        elif query.data == 'invite_friends':
            text = (
                "*📨 Invite Friends*\n\n"
                "Share your referral link and earn 2 points for each friend who joins!\n\n"
                f"🔗 Your referral link:\n`https://t.me/{context.bot.username}?start=ref{user_data['referral_code']}`\n\n"
                "💰 *Earn 2 points per referral!*"
            )
            await send_menu_with_banner(
                query.message.chat_id,
                context,
                text,
                back_to_menu_keyboard()
            )
            
        elif query.data == 'withdraw':
            text = (
                "*💰 Withdraw Points*\n\n"
                f"🪙 *Current Points:* `{user_data['points']}`\n\n"
                "Select a redemption option:"
            )
            await send_menu_with_banner(
                query.message.chat_id,
                context,
                text,
                withdraw_keyboard()
            )
            
        elif query.data == 'withdraw_40':
            if user_data['points'] >= 40:
                user_data['points'] -= 40
                update_user_data(user_id, user_data)
                text = "🎉 *Success!*\n\nYou've redeemed Rs.200 Google Play Code!"
                await send_menu_with_banner(
                    query.message.chat_id,
                    context,
                    text,
                    back_to_menu_keyboard()
                )
            else:
                text = "❌ *Error*\n\nYou need at least 40 points to withdraw!"
                await send_menu_with_banner(
                    query.message.chat_id,
                    context,
                    text,
                    withdraw_keyboard()
                )
                
        elif query.data == 'withdraw_70':
            if user_data['points'] >= 70:
                user_data['points'] -= 70
                update_user_data(user_id, user_data)
                text = "🎉 *Success!*\n\nYou've redeemed Rs.500 Google Play Code!"
                await send_menu_with_banner(
                    query.message.chat_id,
                    context,
                    text,
                    back_to_menu_keyboard()
                )
            else:
                text = "❌ *Error*\n\nYou need at least 70 points to withdraw!"
                await send_menu_with_banner(
                    query.message.chat_id,
                    context,
                    text,
                    withdraw_keyboard()
                )
                
        elif query.data == 'withdraw_100':
            if user_data['points'] >= 100:
                user_data['points'] -= 100
                update_user_data(user_id, user_data)
                text = "🎉 *Success!*\n\nYou've redeemed Rs.1000 Google Play Code!"
                await send_menu_with_banner(
                    query.message.chat_id,
                    context,
                    text,
                    back_to_menu_keyboard()
                )
            else:
                text = "❌ *Error*\n\nYou need at least 100 points to withdraw!"
                await send_menu_with_banner(
                    query.message.chat_id,
                    context,
                    text,
                    withdraw_keyboard()
                )
                
        elif query.data == 'back_to_menu':
            await send_menu_with_banner(
                query.message.chat_id,
                context,
                "*🏠 Main Menu*\n\nWelcome to Google Play Redeem Code Bot",
                main_menu_keyboard()
            )
            
    except Exception as e:
        print(f"Button Error: {e}")
        await query.message.reply_text("⚠️ An error occurred. Please try again or use /start")

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