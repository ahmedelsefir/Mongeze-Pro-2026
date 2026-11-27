"""Telegram polling and FastAPI interface for Mongez AI."""

import os

from fastapi import FastAPI
from pydantic import BaseModel, Field
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from agent import MongezAgent, handle_email, handle_message, handle_start, is_owner

app = FastAPI(title="Mongez AI", version="2.0.0")


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10_000)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to Mongez AI"}


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, str]:
    """Public API; unauthenticated requests are kept in business mode."""
    return {"response": MongezAgent().respond(request.prompt, is_owner=False)}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_start(update, context)


async def reply_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_message(update, context)


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
