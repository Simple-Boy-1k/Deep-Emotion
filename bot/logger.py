# ==========================================================
# DEEP EMOTIONS — FANCY DYNAMIC LOGGER SYSTEM
# ==========================================================

import os
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import START_IMAGE_URL

# Heroku Environment Variable se Log Channel ID uthayega
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))


# ==========================================================
# 1. BOT START LOGGER
# ==========================================================
async def log_user_start(bot, user):
    """
    Jab koi private chat me /start dabaye
    """
    if not LOG_CHANNEL_ID:
        return

    # Bot ka actual current name automatic fetch karega
    try:
        bot_info = await bot.get_me()
        bot_name = bot_info.first_name.upper()
    except Exception:
        bot_name = "BOT"

    username_str = f"@{user.username}" if user.username else "@None"
    
    # Dynamic bot name ke sath fancy block
    log_text = (
        f"<b>╭─── • {bot_name} • ───╮</b>\n"
        f"<b>❖ {user.full_name} . JUST STARTED THE BOT.</b>\n\n"
        f"<b>⦿ USER ID :</b> <code>{user.id}</code>\n"
        f"<b>⦿ USERNAME :</b> {username_str}\n"
        "<b>╰──────────────────────╯</b>"
    )

    try:
        await bot.send_message(
            chat_id=LOG_CHANNEL_ID,
            text=log_text,
            parse_mode="HTML"
        )
    except Exception as exc:
        print(f"Start log error: {exc}")


# ==========================================================
# 2. GROUP ADD LOGGER
# ==========================================================
async def log_group_add(bot, chat, added_by):
    """
    Jab bot kisi naye group me add ho
    """
    if not LOG_CHANNEL_ID:
        return

    # Group Members Count Fetch karna
    try:
        members_count = await bot.get_chat_members_count(chat.id)
    except Exception:
        members_count = "Unknown"

    # Chat Link Fetch/Generate
    chat_username_str = f"@{chat.username}" if chat.username else "@None"
    
    if chat.username:
        chat_link = f"https://t.me/{chat.username}"
    else:
        try:
            chat_link = await bot.export_chat_invite_link(chat.id)
        except Exception:
            chat_link = None

    # Screenshot style Fancy Formatting
    log_caption = (
        "<b>📝 BOT ADDED IN A NEW GROUP</b>\n\n\n"
        f"<b>📌 CHAT NAME:</b> {chat.title}\n"
        f"<b>🍂 CHAT ID:</b> <code>{chat.id}</code>\n"
        f"<b>🔐 CHAT USERNAME:</b> {chat_username_str}\n"
        f"<b>🗺️ CHAT LINK:</b> " + (f"<a href='{chat_link}'>CLICK</a>" if chat_link else "<code>N/A</code>") + "\n"
        f"<b>📈 GROUP MEMBERS:</b> {members_count}\n"
        f"<b>🤔 ADDED BY:</b> {added_by.full_name}"
    )

    # Inline Button "SEE GROUP👀"
    reply_markup = None
    if chat_link:
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("SEE GROUP👀", url=chat_link)]
        ])

    try:
        # Photo + Caption send karega
        await bot.send_photo(
            chat_id=LOG_CHANNEL_ID,
            photo=START_IMAGE_URL,
            caption=log_caption,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    except Exception:
        # Fallback agar Photo send na ho sake
        await bot.send_message(
            chat_id=LOG_CHANNEL_ID,
            text=log_caption,
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
