import asyncio
import logging
import os
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import BOT_TOKEN

from bot.database import init_db, cleanup_old_data
from bot.proactive import proactive_group_loop

from bot.handlers import (
    start,
    help_command,
    ask,
    game_command,
    clear_memory,
    stats,
    chat_message,
    memory_command,
    forget_memory,
    forget_all,
    welcome_new_member,
    goodbye_member,
    moderate_message,
    button_handler,
    voice_message,
    privacy_command,
)

from bot.truth_dare import (
    truth_command,
    dare_command,
    truth_dare_command,
    truth_dare_callback,
)


# ==========================================================
# ✨ 𝐋𝐎𝐆𝐆𝐈𝐍𝐆
# ==========================================================

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("DeepEmotions")


# ==========================================================
# 🧹 𝐏𝐄𝐑𝐈𝐎𝐃𝐈𝐂 𝐃𝐀𝐓𝐀𝐁𝐀𝐒𝐄 𝐂𝐋𝐄𝐀𝐍𝐔𝐏
# ==========================================================

async def periodic_db_cleanup():
    """Periodically clean expired conversation and memory data."""

    while True:
        await asyncio.sleep(6 * 60 * 60)

        try:
            await cleanup_old_data()
            logger.info("Database cleanup completed successfully.")

        except Exception:
            logger.exception("Database cleanup failed.")


# ==========================================================
# 🌐 𝐑𝐄𝐍𝐃𝐄𝐑 / 𝐇𝐄𝐑𝐎𝐊𝐔 𝐇𝐄𝐀𝐋𝐓𝐇 𝐒𝐄𝐑𝐕𝐄𝐑
# ==========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8",
        )

        self.end_headers()

        self.wfile.write(
            b"Deep Emotions Bot is running!"
        )

    def log_message(self, format, *args):
        pass


def start_health_server():
    port = int(os.environ.get("PORT", 10000))

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler,
    )

    logger.info("Health server started on port %s", port)

    server.serve_forever()


# ==========================================================
# 🤖 𝐌𝐀𝐈𝐍 𝐁𝐎𝐓
# ==========================================================

async def main():

    # Initialize database
    await init_db()

    # Create Telegram application
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # ------------------------------------------------------
    # 📌 COMMAND HANDLERS
    # ------------------------------------------------------

    command_handlers = [
        ("start", start),
        ("help", help_command),
        ("ask", ask),
        ("game", game_command),
        ("truth", truth_command),
        ("dare", dare_command),
        ("td", truth_dare_command),
        ("memory", memory_command),
        ("forget", forget_memory),
        ("forget_all", forget_all),
        ("clear", clear_memory),
        ("stats", stats),
        ("privacy", privacy_command),
    ]

    for command, callback in command_handlers:
        application.add_handler(
            CommandHandler(command, callback)
        )

    # ------------------------------------------------------
    # 🎮 TRUTH OR DARE CALLBACKS
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            truth_dare_callback,
            pattern=r"^td:",
        )
    )

    # ------------------------------------------------------
    # 🔘 INLINE BUTTONS
    # ------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    # ------------------------------------------------------
    # 👋 WELCOME NEW MEMBERS
    # ------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome_new_member,
        )
    )

    # ------------------------------------------------------
    # 👋 GOODBYE MEMBERS
    # ------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.LEFT_CHAT_MEMBER,
            goodbye_member,
        )
    )

    # ------------------------------------------------------
    # 🎙️ VOICE AI
    # ------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.VOICE,
            voice_message,
        ),
        group=0,
    )

    # ------------------------------------------------------
    # 🛡️ ANTI-SPAM MODERATION
    # ------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            moderate_message,
        ),
        group=1,
    )

    # ------------------------------------------------------
    # 🧠 AI CHAT
    # ------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            chat_message,
        ),
        group=2,
    )

    # ------------------------------------------------------
    # 🚀 START BOT
    # ------------------------------------------------------

    logger.info("Starting Deep Emotions Bot...")

    await application.initialize()
    await application.start()

    await application.updater.start_polling(
        allowed_updates=Update.ALL_TYPES
    )

    # Background tasks
    asyncio.create_task(
        proactive_group_loop(application.bot)
    )

    asyncio.create_task(
        periodic_db_cleanup()
    )

    logger.info("Bot started successfully!")

    # Keep the bot running
    while True:
        await asyncio.sleep(3600)


# ==========================================================
# ▶️ ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    health_thread = Thread(
        target=start_health_server,
        daemon=True,
    )

    health_thread.start()

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Bot stopped.")

    except Exception:
        logger.exception("Bot crashed.")
        raise
