# 𝐒𝐚𝐫𝐤𝐚𝐫 𝐎𝐰𝐧𝐞𝐫

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/Simple-Boy-1k)

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
├── data/
│   └── deep_emotions.db
├── bot/
│   ├── __init__.py
│   ├── ai.py
│   ├── database.py
│   └── handlers.py
└── .venv/
