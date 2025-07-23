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

    if user.id == OWNER_ID:
        await update.message.reply_text("🎉 Welcome, Owner! You have direct access to the bot features.")
        return

    # Check user join status and cache it
    if user.id in user_join_status and user_join_status[user.id]:
        await update.message.reply_text("🎉 You have already joined all channels! You can now use the bot features.")
        return

    joined_all, not_joined = await has_joined_all_channels(context.bot, user.id)
    user_join_status[user.id] = joined_all

    if joined_all:
        await update.message.reply_text("🎉 You have joined all required channels! You can now use the bot features.")
        return

    # Create buttons for required channels
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

    try:
        with open("banner.jpg", "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption="👇 Please join all channels to use the bot 👇",
                reply_markup=reply_markup
            )
    except Exception as e:
        logging.warning(f"banner.jpg not found or failed to send: {e}")
        await update.message.reply_text(
            "👇 Please join all channels to use the bot 👇",
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


# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_joined, pattern="^check_joined$"))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()