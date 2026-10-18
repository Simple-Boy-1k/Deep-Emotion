
import asyncio
import logging
import os
from threading import Thread
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

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
)

logger = logging.getLogger(__name__)


# ==========================================================
# HEALTH SERVER — HEROKU / RENDER
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
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        logger.debug("Health server: " + fmt, *args)


def start_health_server():
    port = int(os.environ.get("PORT", "10000"))

    server = ThreadingHTTPServer(
        ("0.0.0.0", port),
        HealthHandler,
    )
    server.daemon_threads = True

    logger.info("Health server listening on port %s", port)
    server.serve_forever()


# ==========================================================
# PERIODIC DATABASE CLEANUP
# ==========================================================

async def periodic_db_cleanup():
    while True:
        await asyncio.sleep(6 * 60 * 60)

        try:
            await cleanup_old_data()
            logger.info("Periodic database cleanup completed.")

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception("Periodic database cleanup failed.")


# ==========================================================
# MAIN BOT
# ==========================================================

async def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing. Set it in Heroku Config Vars."
        )

    await init_db()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
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
        )

    # ---------------- CALLBACK BUTTONS ----------------

    application.add_handler(
        CallbackQueryHandler(
            truth_dare_callback,
            pattern=r"^td:",
        )
    )

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    # ---------------- GROUP MEMBERS ----------------

    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome_new_member,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.LEFT_CHAT_MEMBER,
            goodbye_member,
        )
    )

    # ---------------- VOICE MESSAGES ----------------

    application.add_handler(
        MessageHandler(
            filters.VOICE,
            voice_message,
        )
    )

    # ---------------- MODERATION ----------------
    # Group 1: moderation runs before normal AI chat.

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            moderate_message,
        ),
        group=1,
    )

    # ---------------- NORMAL AI CHAT ----------------
    # Group 2 allows chat handling after group 1 moderation.
    # Ensure handlers.py prevents AI replies to moderated messages.

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            chat_message,
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

        proactive_task = asyncio.create_task(
            proactive_group_loop(application.bot),
            name="proactive-group-loop",
        )

        logger.info("Deep Emotions started successfully.")

        # Keep the application alive.
        await asyncio.Event().wait()

    finally:
        logger.info("Shutting down Deep Emotions...")

        for task in (proactive_task, cleanup_task):
            if task is not None:
                task.cancel()

        for task in (proactive_task, cleanup_task):
            if task is not None:
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception:
                    logger.exception("Background task shutdown failed.")

        if application.updater is not None:
            if application.updater.running:
                await application.updater.stop()

        if application.running:
            await application.stop()

        await application.shutdown()

        logger.info("Deep Emotions stopped.")


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

    except KeyboardInterrupt:
        logger.info("Shutdown requested.")

    except Exception:
        logger.exception("Bot crashed.")
        raise
