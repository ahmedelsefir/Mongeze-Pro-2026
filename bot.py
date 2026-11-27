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
FALLBACK_REPLY = "أهلاً بيك، أنا منجز، مساعدك الشخصي المتكامل\n\nاكتب:\n/خدمات - خدمات رؤية الخير\n/متجر - الكاميرات والهاردات\n/استمارة - طلب معاينة\n/كود - أساعدك في البرمجة\n/نظملي - أنظم شغلك"
_brain: dict[str, Any] | None = None
_brain_loaded = False

app = FastAPI(title="Mongez AI", version="1.1.0")

class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10_000)

def get_gemini_key() -> str | None:
    return os.getenv("GEMINI_KEY") or os.getenv("GEMINI_API_KEY")

def load_local_brain() -> dict[str, Any] | None:
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
        _brain = None
    return _brain

def answer_locally(prompt: str) -> str | None:
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
        return None

def check_keywords(prompt: str) -> str | None:
    text = (prompt or "").strip()
    if "نظملي" in text or "نظم" in text or "رتب" in text:
        return "تمام يا أحمد، هساعدك تنظم شغلك. ابعتلي اللي عايز تنظمه، عملاء المهندسين ولا أرض اللواء ولا شغل بكره؟ وهسجلهولك."
    if "السلام" in text or "سلام عليكم" in text:
        return "وعليكم السلام يا أحمد، أنا منجز، مساعدك الشخصي المتكامل. اكتب /نظملي عشان أنظم شغلك، أو /خدمات للخدمات."
    if "كاميرات" in text or "تركيب" in text:
        return "تمام، عايز تركب كاميرات في المهندسين؟ المعاينة مجانية للتركيب. ابعتلي اسمك وعنوانك ورقمك، وهعملك استمارة."
    if "بكام" in text or "سعر" in text or "المعاينة بكام" in text:
        return "المعاينة مجانية للتركيب فقط، والصيانة المعاينة مدفوعة. السعر النهائي بعد المعاينة."
    if "بتشتغل فين" in text or text == "فين":
        return "أنا بشتغل في المهندسين فقط، رؤية الخير."
    if "هيكفيجن" in text:
        return "أيوه عندنا كاميرات هيكفيجن، والهاردات، والدش، والشاشات. السعر النهائي بعد المعاينة."
    if "DVR" in text or "مشكلة" in text:
        return "تمام، قولي ايه المشكلة في DVR بالظبط؟ والجهاز بيشتغل ولا لأ؟ الصيانة المعاينة مدفوعة."
    if "كود" in text or "code" in text.lower():
        return "تمام، أنا جاهز أساعدك في البرمجة خطوة خطوة، ابعتلي الكود اللي واقف معاك."
    if "مهمة" in text or "فكرني" in text:
        return "تمام، ابعتلي المهمة اللي عايز أضيفها، وهسجلها ليك. اكتب: المهمة + اللي عايزه."
    return None

def generate_answer(prompt: str) -> str:
    keyword_answer = check_keywords(prompt)
    if keyword_answer:
        return keyword_answer
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
            pass
    return FALLBACK_REPLY

@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to Mongez AI"}

@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, str]:
    return {"response": generate_answer(request.prompt)}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text("أهلاً بيك، أنا منجز، مساعدك الشخصي المتكامل\n\nأنا أحمد، مساعدك في الشغل والبرمجة والحياة\nبشتغل في المهندسين فقط - رؤية الخير\nتركيب كاميرات - صيانة DVR - اكسس كنترول - شبكات - دش وشاشات\nالمعاينة مجانية للتركيب فقط، الصيانة المعاينة مدفوعة\nالسعر النهائي بعد المعاينة\nواتساب: 01111325395\n\nاكتب /خدمات للخدمات، و /نظملي عشان أنظم شغلك")

async def reply_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None or not message.text:
        return
    answer = await asyncio.to_thread(generate_answer, message.text)
    await message.reply_text(answer)

def run_telegram_bot() -> None:
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is not configured")
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_to_message))
    application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    run_telegram_bot()
