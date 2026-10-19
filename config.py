# ==========================================================
# DEEP EMOTIONS — CONFIGURATION (Fixed)
# ==========================================================

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Fixed default model to stable gemini-2.0-flash
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

try:
    OWNER_ID = int(os.getenv("OWNER_ID", "8885285219") or 0)
except ValueError:
    OWNER_ID = 0

SUPPORT_CHAT_URL = os.getenv("SUPPORT_CHAT_URL", "").strip()
SUPPORT_CHANNEL_URL = os.getenv("SUPPORT_CHANNEL_URL", "").strip()
UPDATES_CHANNEL_URL = os.getenv("UPDATES_CHANNEL_URL", "https://t.me/deep_emotions_01").strip()
START_IMAGE_URL = os.getenv("START_IMAGE_URL", "https://raw.githubusercontent.com/AashishTechs/Deep-Emotion/main/Welcome.jpg?v=2").strip()
OUR_BOTS_URL = os.getenv("OUR_BOTS_URL", "").strip()
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "").strip().lstrip("@")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing.")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing.")

print(f"Deep Emotions config loaded | Model: {GEMINI_MODEL}")
