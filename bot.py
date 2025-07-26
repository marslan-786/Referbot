import os
import json
import uuid
import random
import asyncio
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
    {"name": "🔊 Channel 2", "url": "https://t.me/botsworldtar", "id": -1001826519793},
    {"name": "📡 Channel 3", "url": "https://t.me/+ddWJ_3i9FKEwYzM9", "id": -1002650001462},
    {"name": "🔗 Channel 4", "url": "https://t.me/+ggvGbpCytFU5NzQ1", "id": -1002124581254},
    {"name": "📻 Channel 5", "url": "https://t.me/only_possible_world", "id": -1002650289632},
    {"name": "📈 Channel 6", "url": "https://t.me/+HCD6LvxtZEg2NDRl"},
    {"name": "🎬 Channel 7", "url": "https://t.me/+2i2Bbv0eaaw4ZDRl"},
    {"name": "🏗️ Channel 8", "url": "https://t.me/+0k61CBIBCQJjNWFl"},
    {"name": "🎤 Channel 9", "url": "https://t.me/+MdCLWsOY3XRmNmY1"},
    {"name": "🦸 Channel 10", "url": "https://t.me/+bxuTB3JZ2SYwNTY1"}
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
        [InlineKeyboardButton("🎯 اپنے پوائنٹس", callback_data='my_account')],
        [InlineKeyboardButton("👥 ریفرلز", callback_data='my_referrals')],
        [InlineKeyboardButton("📩 دوستوں کو انوائٹ کریں", callback_data='invite_friends')],
        [InlineKeyboardButton("💰 ویتھڈرا", callback_data='withdraw')],
        [InlineKeyboardButton("ℹ️ ہیلپ", callback_data='help')]
    ])

def withdraw_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("40 Points - Rs.200 Redeem Code", callback_data='withdraw_40')],
        [InlineKeyboardButton("70 Points - Rs.500 Redeem Code", callback_data='withdraw_70')],
        [InlineKeyboardButton("100 Points - Rs.1000 Redeem Code", callback_data='withdraw_100')],
        [InlineKeyboardButton("⬅️ واپس", callback_data='back_to_menu')]
    ])

def back_to_menu_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ واپس", callback_data='back_to_menu')]])

# Channel join keyboard
def channel_join_keyboard(show_error=False):
    keyboard = []
    for i in range(0, len(CHANNELS), 2):
        row = []
        row.append(InlineKeyboardButton(CHANNELS[i]["name"], url=CHANNELS[i]["url"]))
        if i+1 < len(CHANNELS):
            row.append(InlineKeyboardButton(CHANNELS[i+1]["name"], url=CHANNELS[i+1]["url"]))
        keyboard.append(row)
    
    button_text = "⚠️ براہ کرم تمام چینلز جوائن کریں!" if show_error else "✅ میں نے تمام چینلز جوائن کر لیے ہیں"
    keyboard.append([InlineKeyboardButton(button_text, callback_data='joined_channels')])
    
    return InlineKeyboardMarkup(keyboard)

# Send message with banner
async def send_menu_with_banner(chat_id, context, text, reply_markup):
    if text.strip() == "":
        await context.bot.send_message(
            chat_id=chat_id,
            text=" ",
            reply_markup=reply_markup
        )
    else:
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
    user_clicks[user_id] = 0
    await send_menu_with_banner(
        chat_id,
        context,
        "📢 *براہ کرم ہمارے سرکاری چینلز جوائن کریں:*\n\n"
        "1. نیچے دیے گئے تمام چینلز جوائن کریں\n"
        "2. پھر 'میں نے تمام چینلز جوائن کر لیے ہیں' پر کلک کریں",
        channel_join_keyboard()
    )

# Show main menu
async def show_main_menu(chat_id, context):
    await context.bot.send_message(
        chat_id=chat_id,
        text=" ",
        reply_markup=main_menu_keyboard()
    )

# Start command
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
            user_data = get_user_data(user_id)
    
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
                        not_joined.append(f"❌ آپ {channel['name']} کے ممبر نہیں ہیں")
                except Exception as e:
                    not_joined.append(f"⚠️ {channel['name']} چیک نہیں کیا جا سکا")

            if not_joined:
                text = "⚠️ آپ نے تمام چینلز جوائن نہیں کیے:\n\n" + "\n".join(not_joined)
                await query.edit_message_caption(caption=text, reply_markup=channel_join_keyboard(show_error=True))
            else:
                await query.message.delete()
                await show_main_menu(query.message.chat_id, context)

        elif query.data == 'my_account':
            if not await check_required_channels(user_id, query.message.chat_id, context):
                return
            await query.message.delete()
            text = (
                "*📊 اکاؤنٹ کی تفصیلات*\n\n"
                f"🪙 پوائنٹس: `{user_data['points']}`\n"
                f"👥 ریفرلز: `{user_data['referrals']}`"
            )
            await send_menu_with_banner(query.message.chat_id, context, text, back_to_menu_keyboard())

        elif query.data == 'my_referrals':
            if not await check_required_channels(user_id, query.message.chat_id, context):
                return
            await query.message.delete()
            text = f"*👥 آپ کے ریفرلز*\n\nکل: `{user_data['referrals']}`"
            await send_menu_with_banner(query.message.chat_id, context, text, back_to_menu_keyboard())

        elif query.data == 'invite_friends':
            if not await check_required_channels(user_id, query.message.chat_id, context):
                return
            await query.message.delete()
            text = (
                "*📨 دوستوں کو انوائٹ کریں*\n\n"
                f"آپ کا ریفرل لنک:\n`https://t.me/{context.bot.username}?start=ref{user_data['referral_code']}`\n\n"
                "ہر ریفرل پر 2 پوائنٹس حاصل کریں!"
            )
            await send_menu_with_banner(query.message.chat_id, context, text, back_to_menu_keyboard())

        elif query.data == 'withdraw':
            if not await check_required_channels(user_id, query.message.chat_id, context):
                return
            await query.message.delete()
            text = (
                "*💰 ویتھڈرا*\n\n"
                f"آپ کے پوائنٹس: `{user_data['points']}`\n\n"
                "اختیار منتخب کریں:"
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
                text = f"🎉 کامیابی!\n\nآپ نے Rs.{amounts[points]} کا کوڈ ریڈیم کر لیا ہے!"
                reply_markup = back_to_menu_keyboard()
            else:
                text = f"❌ آپ کو {points} پوائنٹس درکار ہیں!"
                reply_markup = withdraw_keyboard()

            await send_menu_with_banner(query.message.chat_id, context, text, reply_markup)

        elif query.data == 'back_to_menu':
            if not await check_required_channels(user_id, query.message.chat_id, context):
                return
            await query.message.delete()
            await show_main_menu(query.message.chat_id, context)

        elif query.data == 'help':
            if not await check_required_channels(user_id, query.message.chat_id, context):
                return
            await query.message.delete()
            text = (
                "*ℹ️ ہیلپ*\n\n"
                "🤔 کس طرح پوائنٹس حاصل کریں؟\n"
                "- دوستوں کو انوائٹ کر کے: ہر ریفرل پر 2 پوائنٹس\n"
                "- روزانہ چینلز چیک کر کے\n\n"
                "💸 ویتھڈرا کرنے کے لیے کم از کم 40 پوائنٹس درکار ہیں"
            )
            await send_menu_with_banner(query.message.chat_id, context, text, back_to_menu_keyboard())

    except Exception as e:
        print(f"Error: {e}")
        await query.message.reply_text("⚠️ براہ کرم دوبارہ کوشش کریں یا /start استعمال کریں")

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
            "⚠️ *آپ نے درج ذیل چینلز چھوڑ دیے ہیں:*\n\n" +
            "\n".join([f"❌ {ch}" for ch in not_joined]) +
            "\n\nبراہ کرم انہیں دوبارہ جوائن کریں!"
        )
        await send_menu_with_banner(chat_id, context, warning_text, channel_join_keyboard(show_error=True))
        return False

    return True

# [Rest of the code remains the same...]
# [Keep all the other functions (send_broadcast, generate_fake_redeem_message, etc.) unchanged]

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
    application.add_handler(CommandHandler("gen", gen_redeem))
    application.add_handler(CommandHandler("active", start_auto_redeem))
    application.add_handler(CommandHandler("deactive", stop_auto_redeem))
    
    application.run_polling()

if __name__ == '__main__':
    main()