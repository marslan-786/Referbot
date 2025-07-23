import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

# ----------- CONFIG -----------
BOT_TOKEN = "7902248899:AAHElm3aHJeP3IZiy2SN3jLAgV7ZwRXnvdo"

REQUIRED_CHANNELS = [
    {"name": "Channel 1", "link": "https://t.me/+92ZkRWBBExhmNzY1"},
    {"name": "Channel 2", "link": "https://t.me/+dsm5id0xjLQyZjcx"},
    {"name": "Channel 3", "link": "https://t.me/+ggvGbpCytFU5NzQ1"},
    {"name": "Channel 4", "link": "https://t.me/+ddWJ_3i9FKEwYzM9"},
    {"name": "Channel 5", "link": "https://t.me/+VCRRpYGKMz8xY2U0"},
    {"name": "Channel 6", "link": "https://t.me/+ggvGbpCytFU5NzQ1"},
]

OWNER_ID = 8003357608  # اپنی ID یہاں ڈالیں

channel_cache = {}

async def get_channel_id(bot, link: str) -> int:
    if link in channel_cache:
        return channel_cache[link]
    chat = await bot.get_chat(link)
    channel_cache[link] = chat.id
    return chat.id

async def check_user_joined_all(bot, user_id: int) -> bool:
    for channel in REQUIRED_CHANNELS:
        try:
            chat_id = await get_channel_id(bot, channel['link'])
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            logging.warning(f"Check failed for {channel['link']}: {e}")
            return False
    return True

  # گلوبل لسٹ جس میں چینل IDs محفوظ ہوں گی

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # اگر admin_channels خالی ہے تو اپڈیٹ کر لیں
    if not admin_channels:
        await fetch_admin_channels(context.bot, REQUIRED_CHANNELS)

    if user.id == OWNER_ID:
        await update.message.reply_text(
            "🎉 Welcome, Owner! You have direct access to the bot features."
        )
        return

    # دو دو بٹن ایک لائن میں بنانے کا طریقہ
    keyboard = []
    temp_row = []
    for i, channel in enumerate(REQUIRED_CHANNELS, 1):
        temp_row.append(InlineKeyboardButton(channel["name"], url=channel["link"]))
        if i % 2 == 0:
            keyboard.append(temp_row)
            temp_row = []
    if temp_row:
        keyboard.append(temp_row)

    # joined چیک بٹن نیچے ایڈ کریں
    keyboard.append([InlineKeyboardButton("✅ Joined", callback_data="check_joined")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    with open("banner.jpg", "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption="👇 Please join all channels to use the bot 👇",
            reply_markup=reply_markup
        )
admin_channels = []  # یہاں IDs آ جائیں گے جو بوت کے ہیں

async def fetch_admin_channels(bot, required_channels):
    global admin_channels
    admin_channels = []  # پہلے خالی کریں

    bot_user_id = (await bot.get_me()).id

    for channel in required_channels:
        try:
            chat = await bot.get_chat(channel['link'])
            admins = await bot.get_chat_administrators(chat.id)

            # چیک کریں کہ بوت ایڈمن ہے یا نہیں
            is_admin = any(admin.user.id == bot_user_id for admin in admins)
            if is_admin:
                admin_channels.append(chat.id)
                print(f"Bot is admin in channel '{channel['name']}' (ID: {chat.id})")
        except Exception as e:
            print(f"Failed to check admin status for channel '{channel['name']}': {e}")


# پھر join چیک میں admin_channels استعمال کریں:
async def check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    not_joined = []

    for chat_id in admin_channels:
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                # چینل کا نام چاہیے، تو ریورس میپ بنائیں یا ID کو نام سے map کریں
                ch_name = next((ch['name'] for ch in REQUIRED_CHANNELS if await get_channel_id(context.bot, ch['link']) == chat_id), str(chat_id))
                not_joined.append(ch_name)
        except Exception as e:
            print(f"Error checking membership in channel ID {chat_id}: {e}")
            not_joined.append(str(chat_id))

    if not_joined:
        not_joined_str = "\n".join(f"❌ {name}" for name in not_joined)
        await query.answer(f"You have NOT joined these channels:\n{not_joined_str}", show_alert=True)
    else:
        await query.answer("✅ You are joined in all required channels!", show_alert=True)
        await query.edit_message_caption("🎉 You’ve joined all required channels!")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # async function call to fetch admin channels before starting polling
    import asyncio
    asyncio.run(fetch_admin_channels(application.bot))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_joined, pattern="^check_joined$"))
    application.run_polling()
    

if __name__ == "__main__":
    main()