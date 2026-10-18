# ==========================================================
# DEEP EMOTIONS — AI ENGINE (Debug Mode)
# ==========================================================

import asyncio
import json

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL

client = genai.Client(
    api_key=GEMINI_API_KEY
)

SYSTEM_PROMPT = """
You are 𝐃ᴇᴇᴘ 𝐄ᴍᴏᴛɪᴏɴ, a warm, playful, cute and natural female AI companion.
You are ALWAYS a girl/female in your own speaking style.
"""

async def generate_reply(
    history,
    user_message,
    memories=None,
    group_context=None,
    is_group=False,
    current_user_name=None,
):
    history = history or []
    memories = memories or []
    group_context = group_context or []

    prompt_parts = []
    if current_user_name:
        prompt_parts.append(f"Current user name: {current_user_name}.")
    prompt_parts.append(f"Current user message:\n{user_message}")
    final_prompt = "\n\n".join(prompt_parts)

    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=GEMINI_MODEL,
            contents=final_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.8,
                max_output_tokens=2048,
            ),
        )
        return response.text.strip() if response.text else "Sorry, I couldn't generate a response."
    
    except Exception as exc:
        # Yahan exact error print aur chat mein return hoga taaki pata chale problem kya hai
        print(f"Gemini API Error Detail: {exc}")
        return f"❌ Asli Error: {str(exc)}"


async def extract_memories(user_message):
    return []

async def ai_tool(tool, text):
    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=GEMINI_MODEL,
            contents=f"Process: {text}",
            config=types.GenerateContentConfig(temperature=0.7),
        )
        return response.text.strip() if response.text else "Done!"
    except Exception as exc:
        return f"Tool Error: {str(exc)}"

async def rewrite_text(text):
    return text

async def summarize_text(text):
    return text

async def translate_text(text):
    return text

async def explain_text(text):
    return text

async def study_help(text):
    return text

async def transcribe_voice(audio_path):
    return None
