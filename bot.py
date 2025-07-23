import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, Application

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


import json
import os

USER_FILE = "user.json"

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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text  # /start or /start referralcode

    users = load_users()

    # Referral code extract
    referral_code = None
    if text and len(text.split()) > 1:
        referral_code = text.split()[1]

    # Owner gets direct main menu without referral checks
    if user.id == OWNER_ID:
        await send_main_menu(update)
        return

    # Referral processing (if any)
    if referral_code:
        referrer_id = referral_code
        if referrer_id != str(user.id):  # Prevent self-referral
            if referrer_id not in users:
                users[referrer_id] = {"referrals": [], "points": 0}

            if str(user.id) not in users[referrer_id]["referrals"]:
                users[referrer_id]["referrals"].append(str(user.id))
                users[referrer_id]["points"] += 2

                if str(user.id) not in users:
                    users[str(user.id)] = {"referrals": [], "points": 0}

                save_users(users)

                # Notify referrer about new referral
                try:
                    referrer_chat_id = int(referrer_id)
                    referred_username = user.username or "NoUsername"
                    referred_id = user.id
                    msg = (
                        f"🎉 Congratulations! You have a new referral.\n\n"
                        f"User: @{referred_username}\n"
                        f"User ID: {referred_id}\n"
                        f"You earned 2 points."
                    )
                    await context.bot.send_message(chat_id=referrer_chat_id, text=msg)
                except Exception as e:
                    print(f"Error sending referral notification: {e}")

    # Show join channels prompt unconditionally (no admin/channel join check here)
    await show_join_channels(update)
        
admin_channels = []

async def fetch_admin_channels(bot, required_channels):
    global admin_channels
    admin_channels = []
    bot_user_id = (await bot.get_me()).id
    for channel in required_channels:
        try:
            chat = await bot.get_chat(channel['link'])
            admins = await bot.get_chat_administrators(chat.id)
            is_admin = any(admin.user.id == bot_user_id for admin in admins)
            if is_admin:
                admin_channels.append(chat.id)
                print(f"Bot is admin in: {channel['name']} ({chat.id})")
        except Exception as e:
            print(f"Error checking admin for {channel['name']}: {e}")


async def show_join_channels(update: Update):
    keyboard = []
    temp_row = []
    for i, channel in enumerate(REQUIRED_CHANNELS, 1):
        temp_row.append(InlineKeyboardButton(channel["name"], url=channel["link"]))
        if i % 2 == 0:
            keyboard.append(temp_row)
            temp_row = []
    if temp_row:
        keyboard.append(temp_row)

    keyboard.append([InlineKeyboardButton("✅ Joined", callback_data="check_joined")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    with open("banner.jpg", "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption="👇 Please join all channels to use the bot 👇",
            reply_markup=reply_markup
        )


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = context.user_data

    if not data.get("has_seen_error"):
        # First time click — show error only
        data["has_seen_error"] = True
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("❌ Please first join all required channels before proceeding.")
    else:
        # Second time — show main menu
        await send_main_menu(update)
        
        
async def my_referrals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)

    # users.json کو محفوظ طریقے سے لوڈ کریں
    try:
        users = load_users()
    except Exception:
        users = {}

    if user_id not in users:
        referrals = []
        points = 0
    else:
        user_data = users[user_id]
        referrals = user_data.get("referrals", [])
        points = user_data.get("points", 0)

    referrals_count = len(referrals)

    text = f"👥 You have {referrals_count} referral(s).\n"
    if referrals_count > 0:
        # ریفرلز کی IDs یا یوزر نیم دکھائیں (جتنے چاہیں)
        text += "🔗 Your Referrals:\n" + "\n".join(referrals) + "\n\n"
    text += f"💰 Your total points: {points}"

    keyboard = [
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_caption(caption=text, reply_markup=reply_markup)

async def my_account_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)

    # load users.json safely
    try:
        users = load_users()
    except Exception:
        users = {}

    # اگر یوزر موجود نہیں تو ڈیفالٹ ویلیوز دیں
    if user_id not in users:
        user_balance = 0
        user_referrals = 0
        min_withdrawal = 40
    else:
        user_data = users[user_id]
        user_balance = user_data.get("points", 0)
        user_referrals = len(user_data.get("referrals", []))
        min_withdrawal = 40  # ضرورت کے مطابق تبدیل کریں

    text = (
        f"📊 Your Account Info:\n\n"
        f"💰 Balance: {user_balance} points\n"
        f"👥 Referrals: {user_referrals}\n\n"
        f"Minimum Withdrawal: {min_withdrawal} points"
    )

    keyboard = [
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # اب میسج کو ایڈٹ کرتے ہوئے کیپشن اور بٹن بھیجیں
    await query.edit_message_caption(caption=text, reply_markup=reply_markup)
    
async def invite_referral_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    bot_user = await context.bot.get_me()
    bot_username = bot_user.username  # خودکار بوٹ یوزرنیم

    referral_link = f"https://t.me/{bot_username}?start={user_id}"

    text = (
        f"🎯 Your Invite Referral Link:\n\n"
        f"{referral_link}\n\n"
        f"Share this link with your friends to earn points!"
    )

    keyboard = [
        # یہ بٹن یوزر کو لنک پر لے جائے گا، جہاں سے وہ کاپی کر سکتے ہیں
        [InlineKeyboardButton("🔗 Open Link", url=referral_link)],

        # ٹیلیگرام شیئر بٹن (صرف نئے کلائنٹس پر کام کرے گا)
        [InlineKeyboardButton("📤 Share Link", url=f"tg://msg_url?url={referral_link}")],

        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_caption(caption=text, reply_markup=reply_markup)
    
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

def withdrawal_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)

    # Read user.json to get points
    import json
    try:
        with open("user.json", "r") as f:
            users = json.load(f)
        points = users.get(user_id, {}).get("points", 0)
    except:
        points = 0

    # Message
    text = f"💰 Your Current Points: {points}\n\nSelect your withdrawal option:"

    keyboard = [
        [InlineKeyboardButton("💳 40 Points – Rs.200 Code", callback_data="redeem_40")],
        [InlineKeyboardButton("💳 70 Points – Rs.500 Code", callback_data="redeem_70")],
        [InlineKeyboardButton("💳 100 Points – Rs.1000 Code", callback_data="redeem_100")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=text, reply_markup=reply_markup)
    
def redeem_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = query.data

    import json
    try:
        with open("user.json", "r") as f:
            users = json.load(f)
    except:
        users = {}

    points = users.get(user_id, {}).get("points", 0)

    required_points = 0
    reward_text = ""

    if data == "redeem_40":
        required_points = 40
        reward_text = "🎁 You have successfully redeemed Rs.200 Code!"
    elif data == "redeem_70":
        required_points = 70
        reward_text = "🎁 You have successfully redeemed Rs.500 Code!"
    elif data == "redeem_100":
        required_points = 100
        reward_text = "🎁 You have successfully redeemed Rs.1000 Code!"

    if points < required_points:
        query.answer("❌ Insufficient Points", show_alert=True)
        query.edit_message_text("🚫 You don’t have enough points to withdraw this reward.\n\n👉 Please complete referrals to earn more points.")
        return

    # Deduct points
    users[user_id]["points"] -= required_points
    with open("user.json", "w") as f:
        json.dump(users, f, indent=4)

    query.edit_message_text(reward_text + "\n\n✅ Our team will contact you soon with your code.\n\n🔙 You can go back to the menu anytime.")
    
async def send_main_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("👤 My Account", callback_data="my_account")],
        [InlineKeyboardButton("👥 My Referrals", callback_data="my_referrals")],
        [InlineKeyboardButton("📨 Invite Referral Link", callback_data="invite_referral")],
        [InlineKeyboardButton("💵 Withdrawal", callback_data="withdraw")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("🏠 Welcome to the Main Menu:", reply_markup=reply_markup)
    else:
        await update.callback_query.message.edit_text("🏠 Welcome to the Main Menu:", reply_markup=reply_markup)
        
        
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_main_menu(update)
    
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "my_account":
        await my_account_handler(update, context)

    elif data == "my_referrals":
        await my_referrals_handler(update, context)

    elif data == "invite_referral":
        await invite_referral_handler(update, context)

    elif data == "back_to_menu":
        await query.message.delete()
        await send_main_menu(update)

    else:
        await query.answer("Unknown action!")


# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_joined, pattern="^check_joined$"))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(withdrawal_handler, pattern="^withdraw$"))
    app.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(redeem_handler, pattern="^redeem_"))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()