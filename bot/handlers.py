# ==========================================================
# DEEP EMOTIONS — TELEGRAM HANDLERS
# Step 1–8 (With Exact Button Color Styles)
# ==========================================================

import html
import re
import time
from pathlib import Path
from collections import defaultdict, deque

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatPermissions,
    MessageEntity,
)

from telegram.constants import ChatAction

from telegram.ext import ContextTypes, ApplicationHandlerStop

from config import (
    OWNER_ID, SUPPORT_CHAT_URL, SUPPORT_CHANNEL_URL, UPDATES_CHANNEL_URL,
    START_IMAGE_URL, OUR_BOTS_URL, OWNER_USERNAME,
)

from bot.social_engine import (
    should_reply_group,
    mark_group_reply,
    social_game,
)

from bot.ai import (
    generate_reply,
    extract_memories,
    ai_tool,
    transcribe_voice,
)

from bot.database import (
    add_message,
    get_history,
    clear_history,
    count_messages,

    add_memory,
    get_memories,
    delete_memory,
    clear_memories,
    count_memories,

    add_group_message,
    get_group_context,
    clear_group_context,
    count_group_messages,
)


# ==========================================================
# RATE LIMIT
# ==========================================================

user_requests = defaultdict(deque)

WINDOW_SECONDS = 20
MAX_REQUESTS = 5

GROUP_REPLY_ALWAYS = True


def allowed(user_id):
    now = time.monotonic()
    q = user_requests[user_id]
    while q and now - q[0] > WINDOW_SECONDS:
        q.popleft()
    if len(q) >= MAX_REQUESTS:
        return False
    q.append(now)
    return True


# ==========================================================
# STEP 4 — ANTI SPAM
# ==========================================================

spam_tracker = defaultdict(deque)
warnings = defaultdict(int)

SPAM_WINDOW_SECONDS = 10
SPAM_MESSAGE_LIMIT = 6

MAX_WARNINGS = 3
MUTE_SECONDS = 300

LINK_PATTERN = re.compile(
    r"(https?://|www\.|t\.me/|telegram\.me/)",
    re.IGNORECASE,
)


async def is_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user or chat.type not in ("group", "supergroup"):
        return False

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ("administrator", "creator")
    except Exception as exc:
        print("Admin check error:", repr(exc))
        return False


async def moderate_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return False

    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user or chat.type not in ("group", "supergroup") or user.is_bot:
        return False

    if await is_admin(update, context):
        return False

    text = update.message.text or ""
    key = (chat.id, user.id)
    now = time.monotonic()

    q = spam_tracker[key]
    while q and now - q[0] > SPAM_WINDOW_SECONDS:
        q.popleft()
    q.append(now)

    flood_detected = len(q) > SPAM_MESSAGE_LIMIT
    link_detected = bool(LINK_PATTERN.search(text))

    if not flood_detected and not link_detected:
        return False

    try:
        await update.message.delete()
    except Exception as exc:
        print("Message delete error:", repr(exc))

    warnings[key] += 1
    current_warning = warnings[key]

    if current_warning < MAX_WARNINGS:
        try:
            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    f"⚠️ **[DANGER WARNING]** {user.first_name or 'User'}, "
                    f"spam/link detected.\n\n"
                    f"Warning {current_warning}/{MAX_WARNINGS}."
                ),
                parse_mode="Markdown",
            )
        except Exception as exc:
            print("Warning message error:", repr(exc))
        raise ApplicationHandlerStop

    try:
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_audios=False,
            can_send_documents=False,
            can_send_photos=False,
            can_send_videos=False,
            can_send_video_notes=False,
            can_send_voice_notes=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
        )

        until_date = int(time.time() + MUTE_SECONDS)

        await context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=user.id,
            permissions=permissions,
            until_date=until_date,
        )

        await context.bot.send_message(
            chat_id=chat.id,
            text=(
                f"🛑 **[MUTED]** {user.first_name or 'User'} "
                f"ko 5 minutes ke liye mute kiya gaya.\n\n"
                f"Reason: repeated spam/link activity."
            ),
            parse_mode="Markdown",
        )
    except Exception as exc:
        print("Mute error:", repr(exc))

    warnings[key] = 0
    spam_tracker[key].clear()
    raise ApplicationHandlerStop


# ==========================================================
# STEP 6 — AI TOOL STATE
# ==========================================================

pending_ai_tools = {}


# ==========================================================
# STEP 5 — MAIN MENU & BUTTON STYLING (MATCHING IMAGE COLORS)
# ==========================================================

WELCOME_IMAGE_URL = START_IMAGE_URL or "https://raw.githubusercontent.com/AashishTechs/Deep-Emotion/main/Welcome.jpg?v=2"


def _btn(text, *, callback_data=None, url=None, style=None):
    # Supporting style parameter for custom UI rendering matching screenshot colors
    kwargs = {}
    if style:
        kwargs["style"] = style
    return InlineKeyboardButton(
        text=text,
        callback_data=callback_data,
        url=url,
        **kwargs
    )


def _welcome_caption(bot_name):
    safe_name = html.escape(bot_name or "ʜɪ ʜᴇʟʟᴏ")
    return (
        f"✨ ʜɪ ʜᴇʟʟᴏ, ɪ'ᴍ <b>{safe_name}</b> 💗\n\n"
        "Your friendly AI companion for chat, memory, games and everyday help. 🌸\n\n"
        "🧠 Smart Memory • 💬 Natural Chat\n"
        "🎮 Games • 🛠️ AI Tools • 🎙️ Voice AI\n"
        "👥 Group Conversations • 📊 Stats\n\n"
        "Choose an option below and let's get started. 👇"
    )


def main_menu_keyboard(bot_username="deepemotions01", is_owner=False):
    username = (bot_username or "deepemotions01").lstrip("@")
    rows = [
        # 🔴 Red / Danger style buttons (matching screenshot)
        [_btn("💬 ᴄʜᴀᴛ ᴡɪᴛʜ ᴍᴇ", callback_data="chat", style="danger")],
        [_btn("💗 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs", callback_data="help_main", style="danger")],
    ]
    links = []
    if UPDATES_CHANNEL_URL:
        # 🟢 Green / Success style buttons
        links.append(_btn("🔔 ᴜᴘᴅَاتᴇs", url=UPDATES_CHANNEL_URL, style="success"))
    if SUPPORT_CHANNEL_URL:
        links.append(_btn("📢 ꜱᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=SUPPORT_CHANNEL_URL, style="success"))
    if links:
        rows.append(links)
    if SUPPORT_CHAT_URL:
        rows.append([_btn("🛠️ ꜱᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ", url=SUPPORT_CHAT_URL, style="success")])
    if OUR_BOTS_URL:
        # 🔵 Blue / Primary style buttons
        rows.append([_btn("🤖 ᴏᴜʀ ʙᴏᴛs", url=OUR_BOTS_URL, style="primary")])
    owner_username = (OWNER_USERNAME or "").strip().lstrip("@")
    if owner_username:
        rows.append([_btn("👑 ᴏᴡɴᴇʀ", url=f"https://t.me/{owner_username}", style="primary")])
    rows.append([_btn("➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ", url=f"https://t.me/{username}?startgroup=true", style="primary")])
    if is_owner:
        rows.append([_btn("🔴 👑 ᴏᴡɴᴇʀ ᴘᴀɴᴇʟ", callback_data="owner_panel", style="danger")])
    return InlineKeyboardMarkup(rows)


def help_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                _btn("💬 ᴄʜᴀᴛ", callback_data="help_chat", style="danger"),
                _btn("🧠 ᴍᴇᴍᴏʀʏ", callback_data="help_memory", style="danger"),
                _btn("🛠️ ᴀɪ ᴛᴏᴏʟs", callback_data="help_ai_tools", style="danger"),
            ],
            [
                _btn("🎙️ ᴠᴏɪᴄᴇ", callback_data="help_voice", style="primary"),
                _btn("👥 ɢʀᴏᴜᴘ", callback_data="help_group", style="primary"),
                _btn("🔒 ᴘʀɪᴠᴀᴄʏ", callback_data="help_privacy", style="primary"),
            ],
            [
                _btn("🎮 ɢᴀᴍᴇs", callback_data="help_games", style="success"),
                _btn("📊 ꜱᴛᴀᴛs", callback_data="help_stats", style="success"),
                _btn("📖 ᴄᴏᴍᴍᴀɴᴅs", callback_data="help_commands", style="success"),
            ],
            [_btn("🔙 ʙᴀᴄᴋ", callback_data="home", style="danger")],
        ]
    )


HELP_SECTION_TEXT = {
    "help_chat": (
        "💬 **Chat With Me**\n\n"
        "Private chat mein directly baat karo. 🌸\n\n"
        "Group mein normal text par bhi AI reply karegi, "
        "aur @mention/reply par bhi response degi."
    ),
    "help_memory": (
        "🧠 **Memory**\n\n"
        "Useful long-term memories private chat mein save ho sakti hain.\n\n"
        "/memory — saved memories\n"
        "/forget ID — ek memory delete\n"
        "/forget_all — all memories delete\n"
        "/clear — chat history clear"
    ),
    "help_ai_tools": (
        "🛠️ **AI Tools**\n\n"
        "Rewrite • Summarize • Translate • Explain • Study Help.\n\n"
        "AI Tools open karke koi tool choose karo."
    ),
    "help_voice": (
        "🎙️ **Voice AI**\n\n"
        "Voice message bhejo aur main usse transcribe karke AI response dungi.\n\n"
        "Group voice ke liye bot ko reply ya @mention karo."
    ),
    "help_group": (
        "👥 **Group Chats**\n\n"
        "Normal group text par AI reply karegi.\n"
        "Reply/@mention bhi supported hai.\n\n"
        "Admins moderation aur group controls use kar sakte hain."
    ),
    "help_privacy": (
        "🔒 **Privacy**\n\n"
        "/privacy se memory aur group-data information dekho.\n\n"
        "Personal memories group AI context mein automatically include nahi hoti."
    ),
    "help_games": (
        "🎮 **Games**\n\n"
        "/game truth\n"
        "/game dare\n"
        "/game wyr\n"
        "/game joke\n\n"
        "Group mein social games play kar sakte ho."
    ),
    "help_stats": (
        "📊 **Stats**\n\n"
        "/stats se saved messages, memories aur group context stats dekho."
    ),
    "help_commands": (
        "📖 **Commands**\n\n"
        "/start — Welcome panel\n"
        "/help — Help & Commands\n"
        "/ask <question> — Ask AI\n"
        "/game <truth|dare|wyr|joke> — Play a game\n"
        "/memory — View saved memories\n"
        "/forget <ID> — Delete one memory\n"
        "/forget_all — Delete all memories\n"
        "/clear — Clear chat history\n"
        "/stats — View your stats\n"
        "/privacy — Privacy information\n\n"
        "💡 Tip: /ask ke baad apna question likho.\n"
        "Example: /ask Python kya hai?"
    ),
}


def help_section_keyboard(section):
    rows = []
    if section == "help_ai_tools":
        rows.append([_btn("🛠️ ᴏᴘᴇɴ ᴀɪ ᴛᴏᴏʟs", callback_data="ai_tools", style="success")])
    rows.append([_btn("🔙 ʙᴀᴄᴋ ᴛᴏ ʜᴇʟᴘ", callback_data="help_main", style="primary")])
    return InlineKeyboardMarkup(rows)


def back_button():
    return InlineKeyboardMarkup(
        [
            [
                _btn(
                    "🔙 ʙᴀᴄᴋ",
                    callback_data="home",
                    style="danger",
                )
            ]
        ]
    )


def ai_tools_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                _btn("✍️ Rewrite", callback_data="tool_rewrite", style="danger"),
                _btn("📝 Summarize", callback_data="tool_summarize", style="danger"),
            ],
            [
                _btn("🌐 Translate", callback_data="tool_translate", style="primary"),
                _btn("💡 Explain", callback_data="tool_explain", style="primary"),
            ],
            [_btn("📚 Study Help", callback_data="tool_study", style="success")],
            [_btn("🔙 ʙᴀᴄᴋ ᴛᴏ ʜᴇʟᴘ", callback_data="help_main", style="primary")],
        ]
    )


# ==========================================================
# COMMAND HANDLERS (START, HELP, PRIVACY, ETC.)
# ==========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    me = await context.bot.get_me()
    bot_username = me.username or "deepemotions01"
    bot_name = me.first_name or "ʜɪ ʜᴇʟʟᴏ"
    user = update.effective_user
    is_owner = bool(user and OWNER_ID != 0 and user.id == OWNER_ID)

    await update.message.reply_photo(
        photo=WELCOME_IMAGE_URL,
        caption=_welcome_caption(bot_name),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(bot_username, is_owner=is_owner),
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    text = (
        "💗 **Deep Emotions — Help & Commands**\n\n"
        "Choose a category below. 👇\n\n"
        "🔴 Chat, Memory & AI Tools\n"
        "🔵 Voice, Groups & Privacy\n"
        "🟢 Games, Stats & Commands"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=help_menu_keyboard(),
    )


async def privacy_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    privacy_text = (
        "🔒 **𝐃ᴇᴇᴘ 𝐄ᴍᴏᴛɪᴏɴs — Privacy**\n\n"
        "🧠 **Memory**\n"
        "Main useful non-sensitive information ko "
        "future conversations ko better banane ke liye "
        "save kar sakti hoon.\n\n"
        "👤 **Personal Memory**\n"
        "Personal memories private conversations ke liye hain "
        "aur group conversation mein automatically share nahi hoti.\n\n"
        "👥 **Group Chat**\n"
        "Group mein AI recent group conversation ka context "
        "use kar sakti hai, lekin personal memory ko group "
        "AI prompt mein include nahi kiya jata.\n\n"
        "🧹 **Clear Chat**\n"
        "`/clear` se conversation history clear kar sakte ho.\n\n"
        "🔴🗑️ **Delete Memory**\n"
        "`/forget ID` se specific memory delete kar sakte ho.\n\n"
        "🔴🗑️ **Delete All Memories**\n"
        "`/forget_all` se saari saved memories delete kar sakte ho."
    )

    await update.message.reply_text(
        privacy_text,
        parse_mode="Markdown",
        reply_markup=back_button(),
    )


async def game_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    game = (context.args[0] if context.args else "joke").lower()
    if game not in {"truth", "dare", "wyr", "would", "joke"}:
        await update.message.reply_text(
            "🎮 Games: /game truth | /game dare | /game wyr | /game joke"
        )
        return

    await update.message.reply_text(social_game(game))


async def ask(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text(
            "💬 Example:\n\n`/ask Python kya hai?`",
            parse_mode="Markdown",
        )
        return

    await process_ai(update, text, context)


async def clear_memory(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    await clear_history(
        update.effective_chat.id,
        update.effective_user.id,
    )

    if update.effective_chat.type in ("group", "supergroup"):
        await clear_group_context(update.effective_chat.id)

    await update.message.reply_text(
        "🔴🧹 Tumhari conversation history clear kar di.\n\n"
        "🧠 Long-term memories safe hain."
    )


async def memory_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    user_id = update.effective_user.id
    memories = await get_memories(user_id, limit=10)

    if not memories:
        await update.message.reply_text(
            "🧠 Abhi meri memory mein tumhare baare mein kuch saved nahi hai.",
            reply_markup=back_button(),
        )
        return

    lines = ["🧠 **Tumhari Long-Term Memories**\n"]
    for memory_id, memory in memories:
        lines.append(f"**{memory_id}.** {memory}")

    lines.append(
        "\n🔴 **Danger Actions / Deletion:**"
        "\nDelete karne ke liye: `/forget ID`"
        "\nSab delete karne ke liye: `/forget_all`"
    )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=back_button(),
    )


async def forget_memory(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text(
            "Example:\n`/forget 3`\n\nPehle `/memory` se memory ID dekho.",
            parse_mode="Markdown",
        )
        return

    try:
        memory_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Memory ID number mein do.\n\nExample: `/forget 3`",
            parse_mode="Markdown",
        )
        return

    deleted = await delete_memory(update.effective_user.id, memory_id)
    if deleted:
        await update.message.reply_text(f"🔴🗑️ Memory #{memory_id} delete kar di.")
    else:
        await update.message.reply_text("❌ Ye memory ID tumhari memory mein nahi mili.")


async def forget_all(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    user_id = update.effective_user.id
    total = await count_memories(user_id)

    if total == 0:
        await update.message.reply_text("🧠 Tumhari memory already empty hai.")
        return

    await clear_memories(user_id)
    await update.message.reply_text("🔴🧹 Tumhari saari long-term memories delete kar di.")


async def stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    total_messages = await count_messages(chat_id, user_id)
    total_memories = await count_memories(user_id)
    group_messages = 0

    if update.effective_chat.type != "private":
        group_messages = await count_group_messages(chat_id)

    await update.message.reply_text(
        "📊 **Deep Emotions Stats**\n\n"
        f"💬 Saved messages: {total_messages}\n"
        f"🧠 Long-term memories: {total_memories}\n"
        f"👥 Group context messages: {group_messages}",
        parse_mode="Markdown",
    )


async def save_group_context(update: Update):
    if not update.message:
        return

    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user or chat.type == "private":
        return

    text = update.message.text
    if not text:
        return

    await add_group_message(
        chat_id=chat.id,
        user_id=user.id,
        username=f"@{user.username}" if user.username else None,
        display_name=user.full_name or "Unknown",
        content=text,
    )


async def chat_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if not text:
        return

    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return

    if chat.type != "private":
        await save_group_context(update)

    me = await context.bot.get_me()
    mentioned = f"@{me.username}".lower() in text.lower() if me.username else False
    replied_to_bot = (
        update.message.reply_to_message is not None
        and update.message.reply_to_message.from_user is not None
        and update.message.reply_to_message.from_user.id == me.id
    )

    replied_to_other_user = (
        update.message.reply_to_message is not None
        and update.message.reply_to_message.from_user is not None
        and update.message.reply_to_message.from_user.id != me.id
    )

    other_user_mentioned = replied_to_other_user and not mentioned

    if chat.type != "private":
        if not should_reply_group(
            chat.id,
            text,
            mentioned=mentioned,
            replied_to_bot=replied_to_bot,
            other_user_mentioned=other_user_mentioned,
        ):
            return
        mark_group_reply(chat.id)

    if mentioned and me.username:
        text = re.sub(rf"@{re.escape(me.username)}", "", text, flags=re.IGNORECASE).strip()

    tool_key = (chat.id, user.id)
    selected_tool = pending_ai_tools.pop(tool_key, None)

    if selected_tool:
        await process_ai_tool(update, context, selected_tool, text)
        return

    await process_ai(update, text or "Hi", context)


async def process_ai_tool(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    tool: str,
    text: str,
):
    if not update.message:
        return

    text = text.strip()
    if not text:
        await update.message.reply_text("🛠️ Pehle text bhejo jise main process karun.")
        return

    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        reply = await ai_tool(tool, text)
        await send_text_with_user_mentions(update, context, reply)
    except Exception as exc:
        print("AI tool error:", repr(exc))
        await update.message.reply_text("Sorry 💗 AI Tool use karte waqt problem aa gayi.")


async def process_ai(
    update,
    text,
    context: ContextTypes.DEFAULT_TYPE = None,
):
    user = update.effective_user
    if not user or not update.message:
        return

    if not allowed(user.id) and user.id != OWNER_ID:
        await update.message.reply_text("⏳ Thoda slow... bahut requests aa gayi 😅")
        return

    chat = update.effective_chat
    chat_id = chat.id
    user_id = user.id
    is_group = chat.type in ("group", "supergroup")

    history = await get_history(chat_id, user_id)
    memories = [] if is_group else await get_memories(user_id, limit=10)
    group_context = await get_group_context(chat_id, limit=15) if is_group else []

    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        reply = await generate_reply(
            history=history,
            user_message=text,
            memories=memories,
            group_context=group_context,
            is_group=is_group,
            current_user_name=user.first_name or user.full_name,
        )

        await add_message(chat_id, user_id, "user", text)
        await add_message(chat_id, user_id, "model", reply)

        if not is_group:
            new_memories = await extract_memories(text)
            for memory in new_memories:
                await add_memory(user_id, memory)

        if context is not None:
            await send_text_with_user_mentions(update, context, reply)
        else:
            await update.message.reply_text(reply)
    except Exception as exc:
        print("AI error:", repr(exc))
        await update.message.reply_text("Sorry 💗 abhi AI service se connection nahi ho pa raha.")


async def send_text_with_user_mentions(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
):
    pattern = re.compile(
        r'<a\s+href=["\']tg://user\?id=(\d+)["\']>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    bot = context.bot if hasattr(context, "bot") else context

    parts = []
    entities = []
    last_end = 0

    for match in pattern.finditer(text):
        user_id = int(match.group(1))
        name = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        try:
            member = await bot.get_chat_member(update.effective_chat.id, user_id)
            mentioned_user = member.user
        except Exception:
            mentioned_user = None

        if not mentioned_user:
            continue

        parts.append(text[last_end:match.start()])
        clean_text_so_far = "".join(parts)
        mention_offset = len(clean_text_so_far.encode("utf-16-le")) // 2
        parts.append(name)
        mention_length = len(name.encode("utf-16-le")) // 2

        entities.append(
            MessageEntity(
                type=MessageEntity.TEXT_MENTION,
                offset=mention_offset,
                length=mention_length,
                user=mentioned_user,
            )
        )
        last_end = match.end()

    parts.append(text[last_end:])
    clean_text = "".join(parts)

    if not entities:
        clean_text = re.sub(
            r'<a\s+href=["\']tg://user\?id=\d+["\']>(.*?)</a>',
            lambda m: re.sub(r"<[^>]+>", "", m.group(1)),
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        await update.message.reply_text(clean_text)
        return

    await update.message.reply_text(clean_text, entities=entities)


# ==========================================================
# BUTTON HANDLER (WITH EXACT STYLES AND COLORS)
# ==========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    if not query or not query.message:
        return

    data = query.data

    if data == "owner_panel" and (OWNER_ID == 0 or query.from_user.id != OWNER_ID):
        await query.answer("⛔ [DANGER] This panel is only for the bot owner.", show_alert=True)
        return

    await query.answer()

    async def edit_panel(text, markup):
        if query.message.photo:
            await query.edit_message_caption(caption=text, parse_mode="Markdown", reply_markup=markup)
        else:
            await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=markup)

    async def show_home():
        pending_ai_tools.pop((query.message.chat.id, query.from_user.id), None)
        me = await context.bot.get_me()
        text = _welcome_caption(me.first_name or "ʜɪ ʜᴇʟʟᴏ")

        try:
            await query.message.delete()
        except Exception:
            pass

        await context.bot.send_photo(
            chat_id=query.message.chat.id,
            photo=WELCOME_IMAGE_URL,
            caption=text,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(
                getattr(context.bot, "username", None),
                is_owner=(OWNER_ID != 0 and query.from_user.id == OWNER_ID),
            ),
        )

    if data == "owner_panel":
        await edit_panel(
            "🔴👑 **Owner Panel (Restricted)**\n\n"
            f"Owner ID: `{OWNER_ID}`\n"
            "Configuration is managed through your hosting Variables.",
            InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ", callback_data="home", style="danger")]]),
        )
        return

    if data in {"home", "back"}:
        await show_home()
        return

    if data == "help_main":
        await edit_panel(
            "💗 **Deep Emotions — Help & Commands**\n\nChoose a category below. 👇",
            help_menu_keyboard(),
        )
        return

    if data == "help_commands":
        await edit_panel(
            HELP_SECTION_TEXT["help_commands"],
            InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ ᴛᴏ ʜᴇʟᴘ", callback_data="help_main", style="primary")]]),
        )
        return

    if data in HELP_SECTION_TEXT:
        await edit_panel(HELP_SECTION_TEXT[data], help_section_keyboard(data))
        return

    if data == "chat":
        await edit_panel(
            "💬 **Chat With Me**\n\nBas apna message bhejo. 😊",
            InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ", callback_data="home", style="danger")]]),
        )
        return

    if data == "ai_tools":
        await edit_panel(
            "🛠️ **AI Tools**\n\nNeeche se tool choose karo.",
            ai_tools_keyboard(),
        )
        return

    tool_map = {
        "tool_rewrite": ("rewrite", "✍️ **Rewrite**\n\nApna text bhejo."),
        "tool_summarize": ("summarize", "📝 **Summarize**\n\nApna long text bhejo."),
        "tool_translate": ("translate", "🌐 **Translate**\n\nText bhejo."),
        "tool_explain": ("explain", "💡 **Explain**\n\nKoi topic bhejo."),
        "tool_study": ("study", "📚 **Study Help**\n\nApna study question bhejo."),
    }

    if data in tool_map:
        tool_name, text = tool_map[data]
        pending_ai_tools[(query.message.chat.id, query.from_user.id)] = tool_name
        await edit_panel(
            text + "\n\n🔙 Cancel karne ke liye Back dabao.",
            InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ ᴛᴏ ᴀɪ ᴛᴏᴏʟs", callback_data="ai_tools", style="primary")]]),
        )
        return

    if data == "memory":
        memories = await get_memories(query.from_user.id, limit=10)
        if memories:
            lines = ["🧠 **Tumhari Long-Term Memories**\n"]
            for memory_id, memory in memories:
                lines.append(f"**{memory_id}.** {memory}")
            text = "\n".join(lines)
        else:
            text = "🧠 **Memory**\n\nAbhi meri memory mein kuch saved nahi hai."

        await edit_panel(
            text,
            InlineKeyboardMarkup(
                [
                    [_btn("🔴🗑️ ғᴏʀɢᴇᴛ ᴀʟʟ (ᴅᴀɴɢᴇʀ)", callback_data="forget_all_confirm", style="danger")],
                    [_btn("🔙 ʙᴀᴄᴋ ᴛᴏ ʜᴇʟᴘ", callback_data="help_main", style="primary")],
                ]
            ),
        )
        return

    if data == "forget_all_confirm":
        await clear_memories(query.from_user.id)
        await edit_panel(
            "🔴🧹 **Memory cleared**",
            InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ ᴛᴏ ʜᴇʟᴘ", callback_data="help_main", style="primary")]]),
        )
        return

    if data == "stats":
        user_id = query.from_user.id
        chat_id = query.message.chat.id
        total_messages = await count_messages(chat_id, user_id)
        total_memories = await count_memories(user_id)
        group_messages = await count_group_messages(chat_id) if query.message.chat.type != "private" else 0

        await edit_panel(
            "📊 **Deep Emotions Stats**\n\n"
            f"💬 Saved messages: {total_messages}\n"
            f"🧠 Long-term memories: {total_memories}\n"
            f"👥 Group context messages: {group_messages}",
            InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ ᴛᴏ ʜᴇʟᴘ", callback_data="help_main", style="success")]]),
        )
        return
