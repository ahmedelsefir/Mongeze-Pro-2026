"""Telegram-only entry point for the Mongez personal AI agent."""

import json
import os
from pathlib import Path
from typing import Any

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

BASE_DIR = Path(__file__).resolve().parent
BRAIN_PATH = BASE_DIR / "mongez_brain.json"
UNKNOWN_RESPONSE = "تمام يا أحمد، سجلتها، هرد عليك"


def load_brain() -> dict[str, Any]:
    """Load Mongez answers from the JSON brain."""
    if not BRAIN_PATH.exists():
        return {}
    try:
        with BRAIN_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_unknown_question(question: str) -> None:
    """Save unanswered questions in mongez_brain.json."""
    brain = load_brain()
    unanswered = brain.setdefault("unanswered", [])
    if not isinstance(unanswered, list):
        unanswered = []
        brain["unanswered"] = unanswered
    unanswered.append({"question": question.strip()})
    with BRAIN_PATH.open("w", encoding="utf-8") as file:
        json.dump(brain, file, ensure_ascii=False, indent=2)


def answer_question(question: str) -> str:
    """Return a brain answer in Egyptian Arabic or record the unknown question."""
    text = (question or "").strip()
    if not text:
        return "أرسل رسالتك، يا أحمد."

    brain = load_brain()
    answers = brain.get("answers", {})
    if isinstance(answers, dict):
        direct = answers.get(text)
        if isinstance(direct, str) and direct.strip():
            return direct.strip()

        normalized = text.casefold()
        for key, value in answers.items():
            if isinstance(key, str) and isinstance(value, str):
                if normalized == key.strip().casefold():
                    return value.strip()

    save_unknown_question(text)
    return UNKNOWN_RESPONSE


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = getattr(update, "effective_message", None)
    if message:
        await message.reply_text("أهلاً يا أحمد، أنا منجز. ابعتلي رسالتك.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = getattr(update, "effective_message", None)
    text = getattr(message, "text", None)
    if message and text:
        await message.reply_text(answer_question(text))


def main() -> None:
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is not configured")

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
