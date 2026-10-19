
import asyncio
import logging
import os
from threading import Thread
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
# LOGGING
# ==========================================================

logging.basicConfig(
format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ==========================================================
# HEALTH SERVER — HEROKU / RENDER
# PERIODIC DATABASE CLEANUP
# ==========================================================

async def periodic_db_cleanup():
    """
    Periodically remove expired conversation and memory data.
    Startup cleanup is handled by init_db(); this keeps cleanup
    running while the bot stays online.
    """

    while True:

        await asyncio.sleep(6 * 60 * 60)

        try:

            await cleanup_old_data()

            logger.info(
                "Periodic database cleanup completed."
            )

        except Exception:

            logger.exception(
                "Periodic database cleanup failed."
            )


# ==========================================================
# RENDER HEALTH SERVER
# ==========================================================

class HealthHandler(BaseHTTPRequestHandler):

def do_GET(self):
        if self.path not in ("/", "/health"):
            self.send_error(404, "Not Found")
            return

        body = b"Deep Emotions is alive!"

self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))

        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8",
        )

self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        logger.debug("Health server: " + fmt, *args)
        self.wfile.write(
            b"Deep Emotions is alive!"
        )

    def log_message(self, format, *args):
        return


def start_health_server():
    port = int(os.environ.get("PORT", "10000"))

    server = ThreadingHTTPServer(
    port = int(
        os.environ.get("PORT", 10000)
    )

    server = HTTPServer(
("0.0.0.0", port),
HealthHandler,
)
    server.daemon_threads = True

    logger.info("Health server listening on port %s", port)
    logger.info(
        f"Health server running on port {port}"
    )

server.serve_forever()


# ==========================================================
# PERIODIC DATABASE CLEANUP
# MAIN BOT
# ==========================================================

async def periodic_db_cleanup():
    while True:
        await asyncio.sleep(6 * 60 * 60)
async def main():

        try:
            await cleanup_old_data()
            logger.info("Periodic database cleanup completed.")
    # ------------------------------------------------------
    # INITIALIZE DATABASE
    # ------------------------------------------------------

        except asyncio.CancelledError:
            raise
    await init_db()

        except Exception:
            logger.exception("Periodic database cleanup failed.")
    # ------------------------------------------------------
    # CREATE TELEGRAM APPLICATION
    # ------------------------------------------------------

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

# ==========================================================
# MAIN BOT
# ==========================================================
    # ======================================================
    # COMMAND HANDLERS
    # ======================================================

async def main():
    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing. Set it in Heroku Config Vars."
    application.add_handler(
        CommandHandler(
            "help",
            help_command,
)
    )

    await init_db()
    application.add_handler(
        CommandHandler(
            "ask",
            ask,
        )
    )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    application.add_handler(
        CommandHandler(
            "game",
            game_command,
        )
)

    # ---------------- COMMANDS ----------------

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
    application.add_handler(
        CommandHandler(
            "truth",
            truth_command,
)
    )

    application.add_handler(
        CommandHandler(
            "dare",
            dare_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "td",
            truth_dare_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "memory",
            memory_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "forget",
            forget_memory,
        )
    )

    application.add_handler(
        CommandHandler(
            "forget_all",
            forget_all,
        )
    )

    application.add_handler(
        CommandHandler(
            "clear",
            clear_memory,
        )
    )

    application.add_handler(
        CommandHandler(
            "stats",
            stats,
        )
    )

    application.add_handler(
        CommandHandler(
            "privacy",
            privacy_command,
        )
    )

    # ---------------- CALLBACK BUTTONS ----------------
    # ======================================================
    # TRUTH OR DARE BUTTONS
    # ======================================================

application.add_handler(
CallbackQueryHandler(
truth_dare_callback,
pattern=r"^td:",
)
)

    # ======================================================
    # INLINE BUTTONS
    # ======================================================

application.add_handler(
        CallbackQueryHandler(button_handler)
        CallbackQueryHandler(
            button_handler
        )
)

    # ---------------- GROUP MEMBERS ----------------
    # ======================================================
    # WELCOME NEW MEMBERS
    # ======================================================

application.add_handler(
MessageHandler(
filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome_new_member,
            welcome_new_member
)
)

    # ======================================================
    # GOODBYE MEMBERS
    # ======================================================

application.add_handler(
MessageHandler(
filters.StatusUpdate.LEFT_CHAT_MEMBER,
            goodbye_member,
            goodbye_member
)
)

    # ---------------- VOICE MESSAGES ----------------
    # ======================================================
    # STEP 7 — VOICE AI
    # ======================================================
    #
    # Voice message
    #       ↓
    # voice_message()
    #       ↓
    # Gemini transcription
    #       ↓
    # AI response
    #

application.add_handler(
MessageHandler(
filters.VOICE,
            voice_message,
        )
            voice_message
        ),
        group=0,
)

    # ---------------- MODERATION ----------------
    # Group 1: moderation runs before normal AI chat.
    # ======================================================
    # STEP 4 — ANTI SPAM
    # ======================================================
    #
    # Handles:
    # - Flood spam
    # - Links
    # - Warnings
    # - Temporary mute
    #

application.add_handler(
MessageHandler(
filters.TEXT & ~filters.COMMAND,
            moderate_message,
            moderate_message
),
group=1,
)

    # ---------------- NORMAL AI CHAT ----------------
    # Group 2 allows chat handling after group 1 moderation.
    # Ensure handlers.py prevents AI replies to moderated messages.
    # ======================================================
    # AI CHAT
    # ======================================================
    #
    # Normal text
    #       ↓
    # chat_message()
    #       ↓
    # Memory / Group Context
    #       ↓
    # Gemini
    #       ↓
    # Response
    #

application.add_handler(
MessageHandler(
filters.TEXT & ~filters.COMMAND,
            chat_message,
            chat_message
),
group=2,
)

    cleanup_task = None
    proactive_task = None

    try:
        logger.info("Initializing Telegram application...")

        await application.initialize()
        await application.start()

        if application.updater is None:
            raise RuntimeError("Telegram polling updater is unavailable.")

        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=False,
        )

        cleanup_task = asyncio.create_task(
            periodic_db_cleanup(),
            name="database-cleanup",
        )
    # ======================================================
    # START BOT
    # ======================================================

        proactive_task = asyncio.create_task(
            proactive_group_loop(application.bot),
            name="proactive-group-loop",
        )

        logger.info("Deep Emotions started successfully.")

        # Keep the application alive.
        await asyncio.Event().wait()
    logger.info(
        "Deep Emotions is running..."
    )

    finally:
        logger.info("Shutting down Deep Emotions...")
    await application.initialize()

        for task in (proactive_task, cleanup_task):
            if task is not None:
                task.cancel()
    await application.start()

        for task in (proactive_task, cleanup_task):
            if task is not None:
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception:
                    logger.exception("Background task shutdown failed.")
    await application.updater.start_polling(
        allowed_updates=Update.ALL_TYPES
    )

        if application.updater is not None:
            if application.updater.running:
                await application.updater.stop()
    # Start slow, rate-limited proactive group engagement.
    asyncio.create_task(proactive_group_loop(application.bot))
    asyncio.create_task(periodic_db_cleanup())

        if application.running:
            await application.stop()
    # ======================================================
    # KEEP BOT RUNNING
    # ======================================================

        await application.shutdown()
    while True:

        logger.info("Deep Emotions stopped.")
        await asyncio.sleep(
            3600
        )


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

health_thread = Thread(
target=start_health_server,
        name="health-server",
daemon=True,
)

health_thread.start()

try:
        asyncio.run(main())

        asyncio.run(
            main()
        )

except KeyboardInterrupt:
        logger.info("Shutdown requested.")

        logger.info(
            "Deep Emotions stopped."
        )

except Exception:
        logger.exception("Bot crashed.")

        logger.exception(
            "Bot crashed."
        )

raise
