"""Telegram bot and optional FastAPI backend for Mongez AI.

Run the Telegram bot with ``python bot.py`` after setting TELEGRAM_TOKEN and
GEMINI_KEY in the environment. The FastAPI endpoints remain available via
``uvicorn bot:app``.
"""

import asyncio
import os

from fastapi import FastAPI, HTTPException
from google import genai
from pydantic import BaseModel, Field
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

MODEL_NAME = "gemini-2.5-flash"

app = FastAPI(title="Mongez AI", version="1.1.0")


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10_000)


def generate_answer(prompt: str) -> str:
    """Generate a response using Gemini 2.5 Flash."""
    api_key = os.getenv("GEMINI_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_KEY is not configured")

    client = genai.Client(api_key=api_key)
    result = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    answer = result.text
    if not answer:
        raise RuntimeError("Gemini returned an empty response")
    return answer


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a simple health/welcome response."""
    return {"message": "Welcome to Mongez AI"}


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, str]:
    """Generate a response through the HTTP API."""
    if not os.getenv("GEMINI_KEY"):
        raise HTTPException(
            status_code=503,
            detail="The Gemini API is not configured. Set the GEMINI_KEY environment variable.",
        )
    try:
        return {"response": generate_answer(request.prompt)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="The Gemini API request failed.") from exc


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome the user and explain how to chat with the bot."""
    if update.effective_message:
        await update.effective_message.reply_text(
            "مرحباً بك في مُنجز! أرسل رسالتك وسأجيبك باستخدام Gemini 2.5 Flash."
        )


async def reply_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a text message to Gemini and return its response."""
    message = update.effective_message
    if message is None or not message.text:
        return

    try:
        answer = await asyncio.to_thread(generate_answer, message.text)
        await message.reply_text(answer)
    except Exception:
        await message.reply_text("تعذر الاتصال بالمساعد حالياً. يرجى المحاولة لاحقاً.")


def run_telegram_bot() -> None:
    """Start the Telegram bot using credentials from environment variables."""
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is not configured")
    if not os.getenv("GEMINI_KEY"):
        raise RuntimeError("GEMINI_KEY is not configured")

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_to_message))
    application.run_polling()


if __name__ == "__main__":
    run_telegram_bot()
