import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

# ----------- CONFIG -----------
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

REQUIRED_CHANNELS = [
    {"name": "Channel 1", "link": "https://t.me/+92ZkRWBBExhmNzY1"},
    {"name": "Channel 2", "link": "https://t.me/+dsm5id0xjLQyZjcx"},
    {"name": "Channel 3", "link": "https://t.me/+ggvGbpCytFU5NzQ1"},
    {"name": "Channel 4", "link": "https://t.me/+ddWJ_3i9FKEwYzM9"},
    {"name": "Channel 5", "link": "https://t.me/+VCRRpYGKMz8xY2U0"},
    {"name": "Channel 6", "link": "https://t.me/+ggvGbpCytFU5NzQ1"},
]

# ----------- UTILS (Channel ID cache and membership check) -----------

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

# ----------- HANDLERS -----------

OWNER_ID = 8003357608  # اپنی ID یہاں ڈالیں

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id == OWNER_ID:
        # Owner کو جوائننگ پیغام نہ دکھائیں، سیدھا Welcome میسج یا مینیو
        await update.message.reply_text(
            "🎉 Welcome, Owner! You have direct access to the bot features."
        )
        return

    # باقی یوزرز کو چینلز جوائننگ والا پیغام بھیجیں
    keyboard = []
    for channel in REQUIRED_CHANNELS:
        keyboard.append([InlineKeyboardButton(channel["name"], url=channel["link"])])
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
    not_joined = []

    for channel in REQUIRED_CHANNELS:
        try:
            chat_id = await get_channel_id(context.bot, channel["link"])
            member = await context.bot.get_chat_member(chat_id, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_joined.append(channel["name"])
        except Exception as e:
            logging.warning(f"Error checking membership for {channel['name']}: {e}")
            not_joined.append(channel["name"])

    if not_joined:
        await query.answer(f"❌ You have not joined: {', '.join(not_joined)}", show_alert=True)
    else:
        await query.answer("✅ You are joined in all required channels!", show_alert=True)
        await query.edit_message_caption("🎉 You’ve joined all required channels!")

# ----------- MAIN -----------

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_joined, pattern="^check_joined$"))
    application.run_polling()

if __name__ == "__main__":
    main()