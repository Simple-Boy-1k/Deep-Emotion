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
# LOGGING
# ==========================================================

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
)

logger = logging.getLogger(__name__)


# ==========================================================
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
# RENDER / HEROKU HEALTH SERVER
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

    def log_message(self, format, *args):
        return


def start_health_server():
    port = int(os.environ.get("PORT", "10000"))

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler,
    )
    server.daemon_threads = True

    logger.info(
        f"Health server running on port {port}"
    )

    server.serve_forever()


# ==========================================================
# MAIN BOT
# ==========================================================

async def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing. Set it in Heroku Config Vars."
        )

    # ------------------------------------------------------
    # INITIALIZE DATABASE
    # ------------------------------------------------------
    await init_db()

    # ------------------------------------------------------
    # CREATE TELEGRAM APPLICATION
    # ------------------------------------------------------
    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # ======================================================
    # COMMAND HANDLERS
    # ======================================================

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "ask",
            ask,
        )
    )

    application.add_handler(
        CommandHandler(
            "game",
            game_command,
        )
    )

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
        CallbackQueryHandler(
            button_handler
        )
    )

    # ======================================================
    # WELCOME NEW MEMBERS
    # ======================================================

    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome_new_member
        )
    )

    # ======================================================
    # GOODBYE MEMBERS
    # ======================================================

    application.add_handler(
        MessageHandler(
            filters.StatusUpdate.LEFT_CHAT_MEMBER,
            goodbye_member
        )
    )

    # ======================================================
    # VOICE MESSAGES
    # ======================================================
    
    application.add_handler(
        MessageHandler(
            filters.VOICE,
            voice_message
        ),
        group=0,
    )

    # ======================================================
    # MODERATION (Group 1)
    # ======================================================
    
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            moderate_message
        ),
        group=1,
    )

    # ======================================================
    # AI CHAT (Group 2)
    # ======================================================
    
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
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

        proactive_task = asyncio.create_task(
            proactive_group_loop(application.bot),
            name="proactive-group-loop",
        )

        logger.info(
            "Deep Emotions is running..."
        )

        # Keep the application alive.
        await asyncio.Event().wait()

    finally:
        logger.info("Shutting down Deep Emotions...")

        for task in (proactive_task, cleanup_task):
            if task is not None:
                task.cancel()
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
        asyncio.run(
            main()
        )
    except KeyboardInterrupt:
        logger.info(
            "Deep Emotions stopped."
        )
    except Exception:
        logger.exception(
            "Bot crashed."
        )
        raise
