import os
import json
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, Application
from datetime import datetime
import json

REQUIRED_CHANNELS = [
    {"name": "Channel 1", "link": "https://t.me/+92ZkRWBBExhmNzY1"},
    {"name": "Channel 2", "link": "https://t.me/+dsm5id0xjLQyZjcx"},
    {"name": "Channel 3", "link": "https://t.me/+ggvGbpCytFU5NzQ1"},
    {"name": "Channel 4", "link": "https://t.me/+ddWJ_3i9FKEwYzM9"},
    {"name": "Channel 5", "link": "https://t.me/+VCRRpYGKMz8xY2U0"},
    {"name": "Channel 6", "link": "https://t.me/botsworldtar"},
]

users_data = {}
user_check_data = {}

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    # Save user data if new
    if user_id not in users_data:
        users_data[user_id] = {
            "joined_at": datetime.utcnow().isoformat()
        }
        save_json("users.json", users_data)

    # Build keyboard with channel buttons (2 per row)
    keyboard = []
    temp_row = []
    for i, channel in enumerate(REQUIRED_CHANNELS, 1):
        temp_row.append(InlineKeyboardButton(channel["name"], url=channel["link"]))
        if i % 2 == 0:
            keyboard.append(temp_row)
            temp_row = []
    if temp_row:
        keyboard.append(temp_row)

    # Add "I've Joined" button
    keyboard.append([InlineKeyboardButton("✅ I've Joined", callback_data="check_joined")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send banner + buttons
    with open("banner.jpg", "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption="👇 Please join all required channels below to continue:",
            reply_markup=reply_markup
        )

async def check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()

    # Track how many times user clicked "I've Joined"
    count = user_check_data.get(user_id, 0) + 1
    user_check_data[user_id] = count
    save_json("user_check_count.json", user_check_data)

    if count == 1:
        # First time: Send error message to join channels
        await query.message.reply_text("❌ You have not joined all channels. Please join them and try again.")
    else:
        # Second time: Show main menu
        await query.message.delete()  # delete join message
        await send_main_menu(query.message, context)

async def send_main_menu(update_or_message, context: ContextTypes.DEFAULT_TYPE = None):
    keyboard = [
        [InlineKeyboardButton("👤 My Account", callback_data="my_account")],
        [InlineKeyboardButton("👥 My Referrals", callback_data="my_referrals")],
        [InlineKeyboardButton("📨 Invite Referral Link", callback_data="invite_referral")],
        [InlineKeyboardButton("💵 Withdrawal", callback_data="withdrawal")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    photo_path = "banner.jpg"

    # update_or_message can be Update or Message object
    if hasattr(update_or_message, "callback_query"):  # Update object
        try:
            await update_or_message.callback_query.message.delete()
        except:
            pass
        await update_or_message.callback_query.message.chat.send_photo(
            photo=open(photo_path, "rb"),
            caption="🏠 Welcome to the Main Menu:",
            reply_markup=reply_markup
        )
    else:  # Message object
        await update_or_message.reply_photo(
            photo=open(photo_path, "rb"),
            caption="🏠 Welcome to the Main Menu:",
            reply_markup=reply_markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = str(query.from_user.id)

    with open("users.json", "r") as f:
        users = json.load(f)

    if data == "my_account":
        if user_id not in users:
            await query.answer("You are not registered.", show_alert=True)
            return
        user_data = users[user_id]
        text = f"""👤 <b>My Account</b>

🆔 <b>User ID:</b> <code>{user_id}</code>
👤 <b>Username:</b> @{user_data.get("username", "N/A")}
💰 <b>Balance:</b> {user_data.get("balance", 0)} PKR
🔗 <b>Referral Code:</b> <code>{user_data.get("referral_code", "N/A")}</code>
👥 <b>Total Referrals:</b> {len(user_data.get("referrals", []))}
"""
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.message.delete()
        except Exception as e:
            print(f"Error deleting message in my_account: {e}")
        await query.message.chat.send_message(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

    elif data == "my_referrals":
        if user_id not in users:
            await query.answer("You are not registered.", show_alert=True)
            return
        user = users[user_id]
        text = (
            f"📢 *Your Referral Info:*\n\n"
            f"🔗 *Referral Code:* `{user.get('referral_code', 'N/A')}`\n"
            f"👥 *Total Referrals:* {len(user.get('referrals', []))}\n"
            f"💰 *Referral Earnings:* {user.get('referral_earning', 0)} PKR\n"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.message.delete()
        except Exception as e:
            print(f"Error deleting message in my_referrals: {e}")
        await query.message.chat.send_photo(photo=open("banner.jpg", "rb"),
                                          caption=text,
                                          parse_mode=ParseMode.MARKDOWN,
                                          reply_markup=reply_markup)

    elif data == "invite_referral":
        if user_id not in users:
            await query.answer("You are not registered.", show_alert=True)
            return
        user = users[user_id]
        bot_username = (await context.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={user.get('referral_code', 'N/A')}"
        text = (
            f"📩 *Invite Your Friends!*\n\n"
            f"🔗 *Your Referral Link:*\n`{referral_link}`\n\n"
            f"👥 When someone joins using your link, you'll earn bonus rewards.\n"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.message.delete()
        except Exception as e:
            print(f"Error deleting message in invite_referral: {e}")
        await query.message.chat.send_photo(photo=open("banner.jpg", "rb"),
                                          caption=text,
                                          parse_mode=ParseMode.MARKDOWN,
                                          reply_markup=reply_markup)

    elif data == "withdrawal":
        if user_id not in users:
            await query.answer("You are not registered.", show_alert=True)
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
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.message.delete()
        except Exception as e:
            print(f"Error deleting message in withdrawal: {e}")
        await query.message.chat.send_message(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    elif data.startswith("withdraw_"):
        if user_id not in users:
            await query.edit_message_text("⛔ You are not registered yet.")
            return
        user = users[user_id]
        points = user.get("points", 0)
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
        users[user_id]["points"] -= required_points
        with open("users.json", "w") as f:
            json.dump(users, f, indent=4)
        await query.edit_message_text(
            f"✅ Your request to redeem Rs. {amount} has been received.\n"
            f"📤 Remaining Points: *{users[user_id]['points']}*\n\n"
            f"👨‍💼 Our team will contact you soon for the payment.",
            parse_mode=ParseMode.MARKDOWN
        )

    elif data == "back_to_menu":
        await send_main_menu(update)

    else:
        await query.answer("Unknown action!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_main_menu(update)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_joined, pattern="check_joined"))
    app.add_handler(CallbackQueryHandler(button_handler))  # سب بٹن کلکس کو ایک ہی ہینڈل کرے گا

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()