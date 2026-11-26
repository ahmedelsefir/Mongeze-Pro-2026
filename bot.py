"""Telegram bot and optional FastAPI backend for Mongez AI.

Run the Telegram bot with ``python bot.py`` after setting TELEGRAM_TOKEN.
The local model trained from data.csv is the primary answer source; Gemini is
an optional fallback when a key is available. The FastAPI endpoints remain
available via ``uvicorn bot:app``.
"""

import asyncio
import os
from pathlib import Path
from typing import Any

import joblib
from fastapi import FastAPI
from google import genai
from pydantic import BaseModel, Field
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

MODEL_NAME = "gemini-2.5-flash"
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "mongez_model.pkl"
FALLBACK_REPLY = "أهلاً بيك، أنا مُنجز، سيب رسالتك والمهندس أحمد هيرد عليك"
_brain: dict[str, Any] | None = None
_brain_loaded = False

app = FastAPI(title="Mongez AI", version="1.1.0")


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10_000)


def get_gemini_key() -> str | None:
    """Return a Gemini key from either supported environment variable."""
    return os.getenv("GEMINI_KEY") or os.getenv("GEMINI_API_KEY")


def load_local_brain() -> dict[str, Any] | None:
    """Load the local model, training it from data.csv if possible."""
    global _brain, _brain_loaded
    if _brain_loaded:
        return _brain

    _brain_loaded = True
    try:
        if not MODEL_PATH.exists():
            from train import train_model

            train_model()
        _brain = joblib.load(MODEL_PATH)
    except Exception:
        # Missing model/data or an invalid model should not stop the bot.
        _brain = None
    return _brain


def answer_locally(prompt: str) -> str | None:
    """Answer using the locally trained intent model when it recognizes a prompt."""
    text = (prompt or "").strip()
    if not text:
        return None

    try:
        brain = load_local_brain()
        if not brain:
            return None
        classifier = brain["classifier"]
        probabilities = classifier.predict_proba([text])[0]
        best_index = probabilities.argmax()
        if float(probabilities[best_index]) < brain.get("min_confidence", 0.30):
            return None
        intent = classifier.classes_[best_index]
        return brain["answers"].get(intent)
    except Exception:
        # Fall back to Gemini or the fixed response if local inference fails.
        return None


def generate_answer(prompt: str) -> str:
    """Prefer the local model, then Gemini, then a safe fixed response."""
    local_answer = answer_locally(prompt)
    if local_answer:
        return local_answer

    api_key = get_gemini_key()
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            result = client.models.generate_content(model=MODEL_NAME, contents=prompt)
            if result.text:
                return result.text
        except Exception:
            # Gemini is optional; the bot can still answer with the fixed message.
            pass

    return FALLBACK_REPLY


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a simple health/welcome response."""
    return {"message": "Welcome to Mongez AI"}


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, str]:
    """Generate a response using the local model and optional Gemini fallback."""
    return {"response": generate_answer(request.prompt)}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome the user and explain how to chat with the bot."""
    if update.effective_message:
        await update.effective_message.reply_text(FALLBACK_REPLY)


async def reply_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message to the local model, with optional Gemini fallback."""
    message = update.effective_message
    if message is None or not message.text:
        return

    answer = await asyncio.to_thread(generate_answer, message.text)
    await message.reply_text(answer)


def run_telegram_bot() -> None:
    """Start the Telegram bot using its token from the environment."""
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is not configured")

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_to_message))
    application.run_polling()


if __name__ == "__main__":
    run_telegram_bot()
