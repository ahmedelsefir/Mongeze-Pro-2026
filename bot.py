"""Telegram bot and FastAPI backend for Mongez AI."""

import asyncio
import os
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from agent import MongezAgent, handle_email, handle_start, route_message

app = FastAPI(title="Mongez AI", version="1.2.0")

class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10_000)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to Mongez AI"}


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, str]:
    """Return a basic local response without requiring an LLM API key."""
    text = request.prompt.strip()
    if "ايميل" in text or "إيميل" in text or "gmail" in text.casefold():
        return {"response": MongezAgent().think(text)}
    return {"response": "أنا منجز، مساعدك الشخصي. وضّح لي المطلوب وسأساعدك."}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_start(update, context)


async def reply_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None or not message.text:
        return
    answer = await asyncio.to_thread(route_message, message.text, update)
    await message.reply_text(answer)


def run_telegram_bot() -> None:
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is not configured")
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ايميل", handle_email))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_to_message))
    application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_telegram_bot()
