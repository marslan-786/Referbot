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
    {"name": "Channel 6", "link": "https://t.me/+ggvGbpCytFU5NzQ1"},
]

OWNER_ID = 8003357608
channel_cache = {}
user_join_status = {}
admin_channels = []  # global variable

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

    if not admin_channels:
        await fetch_admin_channels(context.bot, REQUIRED_CHANNELS)

    if user.id == OWNER_ID:
        # Owner کو سیدھا مین مینیو بھیج دو
        await send_main_menu(update)
        return

    joined_all = await check_user_joined_all(context.bot, user.id)

    if not joined_all:
        # چینلز جوائن کروانے والا میسج + بٹن + بینر
        await show_join_channels(update)
    else:
        # مین مینیو شو کرو
        await send_main_menu(update)


async def send_main_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("My Account", callback_data="my_account")],
        [InlineKeyboardButton("My Referrals", callback_data="my_referrals")],
        [InlineKeyboardButton("Invite Referral Code", callback_data="invite_referral")],
        [InlineKeyboardButton("Withdrawal", callback_data="withdrawal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    with open("banner.jpg", "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption="A Free Radio Code - Welcome to Redeem Code",
            reply_markup=reply_markup
        )


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


async def check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    joined_all, not_joined = await has_joined_all_channels(context.bot, user_id)

    if not joined_all:
        not_joined_str = "\n".join(f"❌ {name}" for name in not_joined)
        await query.answer(f"You have NOT joined:\n{not_joined_str}", show_alert=True)
    else:
        user_join_status[user_id] = True
        await query.answer("✅ You have joined all required channels!", show_alert=True)
        await query.edit_message_caption("🎉 You have joined all required channels!")
        
        

# فرض کرتے ہیں کہ یوزر کا بیلنس اور ریفرلز کہیں سے فچ کرنے کا فنکشن ہے
# یہاں مثال کے طور پر ہارڈ کوڈ ویلیوز دے رہا ہوں، آپ ڈیٹا بیس یا دوسرے ذریعے سے لے سکتے ہیں

async def my_account_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    # Example user data (replace with real data fetching)
    user_balance = 150  # example points
    user_referrals = 5  # example referral count
    min_withdrawal = 40

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

    await query.edit_message_caption(caption=text, reply_markup=reply_markup)
    
    
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "my_account":
        # Handle My Account button
        user_balance = 150
        user_referrals = 5
        min_withdrawal = 40
        text = (
            f"📊 Your Account Info:\n\n"
            f"💰 Balance: {user_balance} points\n"
            f"👥 Referrals: {user_referrals}\n\n"
            f"Minimum Withdrawal: {min_withdrawal} points"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_caption(caption=text, reply_markup=reply_markup)

    elif data == "back_to_menu":
        # Show main menu again (banner + 4 buttons)
        await send_main_menu(update)  # آپ کا main menu function جو بنائیں گے

    # مزید بٹن یہاں add کریں جیسے:
    # elif data == "my_referrals":
    #     # Handle my referrals button

    else:
        await query.answer("Unknown action!")

# پھر اس handler کو add کریں



# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_joined, pattern="^check_joined$"))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()