import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, Application
import os

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
admin_channels = []

logging.basicConfig(level=logging.INFO)


# ---------- UTILS ----------
async def get_channel_id(bot, link: str) -> int:
    if link in channel_cache:
        return channel_cache[link]
    chat = await bot.get_chat(link)
    channel_cache[link] = chat.id
    return chat.id


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
                print(f"✅ Bot is admin in: {channel['name']} ({chat.id})")
        except Exception as e:
            print(f"❌ Error in checking admin for {channel['name']}: {e}")


# ---------- HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id == OWNER_ID:
        await update.message.reply_text("🎉 Welcome, Owner! You have direct access to the bot features.")
        return

    # 1. Banner ہمیشہ دکھانی ہے
    try:
        with open("banner.jpg", "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption="👇 Please join all channels to use the bot 👇"
            )
    except Exception as e:
        logging.warning(f"banner.jpg not found or failed to send: {e}")

    # 2. Channels list with join buttons
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

    await update.message.reply_text("Join all the required channels:", reply_markup=reply_markup)


async def check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    not_joined = []

    for chat_id in admin_channels:
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                ch_name = next((ch['name'] for ch in REQUIRED_CHANNELS if await get_channel_id(context.bot, ch['link']) == chat_id), str(chat_id))
                not_joined.append(ch_name)
        except Exception as e:
            print(f"Error checking membership in channel ID {chat_id}: {e}")
            not_joined.append(str(chat_id))

    if not_joined:
        not_joined_str = "\n".join(f"❌ {name}" for name in not_joined)
        await query.answer(f"You have NOT joined:\n{not_joined_str}", show_alert=True)
    else:
        await query.answer("✅ You are joined in all required channels!", show_alert=True)
        await query.edit_message_text("🎉 You’ve joined all required channels!")


# ---------- MAIN ----------
async def on_startup(app: Application):
    await fetch_admin_channels(app.bot, REQUIRED_CHANNELS)
    print("✅ Admin channels fetched on startup.")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_joined, pattern="^check_joined$"))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()