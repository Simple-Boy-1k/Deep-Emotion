
# 𝐃ᴇᴇᴘ 𝐄ᴍᴏᴛɪᴏɴs

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/Simple-Boy-1k/Deep-Emotion)

Telegram + Gemini AI chatbot with long-term memory,
group conversation context, AI tools, voice support,
privacy controls and basic moderation.

## ✨ Features

- 🤖 Gemini AI conversations
- 🧠 Long-term personal memory
- 💬 Group conversation context
- 👋 Welcome and goodbye messages
- 🛡️ Basic anti-spam moderation
- 🛠️ AI tools
  - Rewrite
  - Summarize
  - Translate
  - Explain
  - Study Help
- 🎙️ Voice message transcription
- 🔒 Privacy and memory controls
- 📊 User statistics
- ⚡ Rate limiting
- 🌐 Render health server support

## 📁 Project Structure

```text
TelegramAIBot/
├── .env
├── .env.example
├── .gitignore
├── config.py
├── main.py
├── requirements.txt
├── README.md
├── Procfile
├── app.json
├── data/
│   └── deep_emotions.db
└── bot/
    ├── __init__.py
    ├── ai.py
    ├── database.py
    └── handlers.py
```

## 🚀 Deploy to Heroku

1. Click the **Deploy to Heroku** button above.
2. Enter your Heroku app name.
3. Configure these environment variables:
   - `BOT_TOKEN` — Telegram bot token from `@BotFather`
   - `GEMINI_API_KEY` — Google AI Studio API key
   - `OWNER_ID` — Your numeric Telegram user ID
   - `GEMINI_MODEL` — `gemini-2.5-flash`
4. Click **Deploy app**.
5. Open the Heroku logs to check whether the bot started successfully.

## 💾 Database Note

The bot uses SQLite at `data/deep_emotions.db`. Heroku's local filesystem is ephemeral, so saved memories may be lost after a restart or redeployment. Use a persistent external database if you need long-term storage.
