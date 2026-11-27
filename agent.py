"""Mongez's central, deterministic personal/business assistant logic.

Personal tools are available only to the configured Telegram owner. Public users
receive the Rouyet El-Khair business assistant and cannot access personal memory.
Email support only creates a reviewable draft; it never sends or accesses email.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from tools import (
    tool_create_order,
    tool_explain_code,
    tool_fix_code,
    tool_get_services,
    tool_organize_tasks,
    tool_remember,
    tool_search_memory,
)

BASE_DIR = Path(__file__).resolve().parent
BRAIN_PATH = BASE_DIR / "mongez_brain.json"


def load_brain() -> dict[str, Any]:
    """Load optional owner configuration without making imports fragile."""
    import json

    try:
        with BRAIN_PATH.open("r", encoding="utf-8") as file:
            brain = json.load(file)
        return brain if isinstance(brain, dict) else {"owner_ids": []}
    except (OSError, json.JSONDecodeError):
        return {"owner_ids": []}


def _configured_owner_ids() -> set[str]:
    configured = load_brain().get("owner_ids", [])
    if not isinstance(configured, (list, tuple, set)):
        configured = []
    env_ids = os.getenv("OWNER_TELEGRAM_IDS", "").split(",")
    return {str(value).strip() for value in (*configured, *env_ids) if str(value).strip()}


def is_owner(update: Any) -> bool:
    """Check Telegram numeric IDs, with legacy usernames as compatibility fallback."""
    user = getattr(update, "effective_user", None)
    if user is None:
        return False
    telegram_id = str(getattr(user, "id", "") or "")
    if telegram_id and telegram_id in _configured_owner_ids():
        return True
    # Retain compatibility with the repository's original owner usernames.
    return (getattr(user, "username", "") or "").casefold() in {
        "ahmedelsefir", "ahmedmostafa"
    }


def extract_code(text: str) -> str:
    match = re.search(r"```(?:[A-Za-z0-9_+#.-]*)?\s*(.*?)```", text, flags=re.S)
    if match:
        return match.group(1).strip()
    parts = text.split(":", 1)
    return parts[1].strip() if len(parts) == 2 else text.strip()


class MongezAgent:
    """Single entry point for personal workflows and non-owner business replies."""

    def think(self, prompt: str) -> str:
        """Compatibility API for existing callers; treats input as non-owner."""
        return self.respond(prompt, is_owner=False)

    def respond(self, prompt: str, *, is_owner: bool) -> str:
        text = (prompt or "").strip()
        if not text:
            return "أرسل طلبك أو سؤالك حتى أساعدك."
        return self._personal_response(text) if is_owner else self._business_response(text)

    def _personal_response(self, text: str) -> str:
        lowered = text.casefold()

        if re.search(r"(?:^remember\b|^تذكر\b|^احفظ\b|تذكر أن)", text, re.I):
            fact = re.sub(r"(?:^remember\b|^تذكر\b|^احفظ\b|تذكر أن)\s*[:،,\-]?\s*", "", text, flags=re.I)
            return tool_remember(fact)

        if re.search(r"(search memory|what do you remember|ابحث في الذاكرة|ماذا تتذكر|فكر في)", text, re.I):
            query = re.sub(r"(search memory|what do you remember|ابحث في الذاكرة|ماذا تتذكر|فكر في)", "", text, flags=re.I).strip(" :؟?-")
            return tool_search_memory(query)

        if re.search(r"(summari[sz]e|لخص|تلخيص|اختصر)", text, re.I):
            content = re.sub(r"^(?:please\s+)?(?:summari[sz]e|لخص|تلخيص|اختصر)\s*[:：-]?\s*", "", text, flags=re.I).strip()
            if not content or content == text:
                return "أرسل النص بعد كلمة «لخص» لألخصه لك."
            sentences = re.split(r"(?<=[.!؟?])\s+|\n+", content)
            summary = " ".join(part.strip() for part in sentences if part.strip())
            if len(summary) > 700:
                summary = summary[:697].rsplit(" ", 1)[0] + "..."
            return f"الملخص:\n{summary}"

        if re.search(r"(organize task|organize tasks|task|tasks|مهمة|مهام|نظم)", lowered):
            return tool_organize_tasks(text)

        if re.search(r"(explain|شرح|فسر|وضح)", lowered):
            code = extract_code(text)
            if code and code != text:
                return tool_explain_code(code)
            return "أرسل الكود داخل ```code``` واطلب شرحه."

        if re.search(r"(fix|debug|solve|صحح|اصلح|صلح|إصلاح)", lowered):
            code = extract_code(text)
            if code and code != text:
                return tool_fix_code(code)
            return "أرسل الكود داخل ```code``` مع رسالة الخطأ وبيئة التشغيل لأساعدك في تشخيصه."

        if re.search(r"(email|بريد|إيميل|ايميل|mail)", lowered):
            return self.check_gmail()

        if re.search(r"(file|files|folder|directory|ملف|ملفات|مجلد)", lowered):
            return "أرسل أسماء الملفات والمجلدات وطريقة التنظيم المطلوبة؛ لن أغيّر ملفات جهازك دون طلب واضح."

        return "أنا منجز، مساعدك الشخصي والبرمجي. أستطيع تلخيص النصوص وتنظيم المهام وشرح الكود وإصلاحه مبدئياً وحفظ المعلومات والبحث في الذاكرة ومساعدتك في إعداد مسودات البريد."

    def _business_response(self, text: str) -> str:
        lowered = text.casefold()
        if re.search(r"(create order|new order|طلب جديد|عايز اطلب|أريد طلب|نحتاج طلب)", text, re.I):
            name_match = re.search(r"(?:name|الاسم)\s*[:=]\s*([^,\n]+)", text, re.I)
            place_match = re.search(r"(?:place|location|المكان|المنطقة)\s*[:=]\s*([^,\n]+)", text, re.I)
            service_match = re.search(r"(?:service|الخدمة)\s*[:=]\s*([^,\n]+)", text, re.I)
            if not (name_match and place_match and service_match):
                return "لتسجيل طلب خدمة رؤية الخير في المهندسين، أرسل: الاسم: ...، المكان: ...، الخدمة: ..."
            return tool_create_order(name_match.group(1), place_match.group(1), service_match.group(1))

        if re.search(r"(services|available services|الخدمات|ايه الخدمات|خدماتكم|camera|cctv|dvr|access control|دش|شاش|كاميرا|كاميرات|صيانة)", lowered):
            return tool_get_services()
        return self.business_welcome()

    @staticmethod
    def business_welcome() -> str:
        return (
            "مرحباً، أنا مساعد أعمال شركة رؤية الخير في المهندسين فقط.\n"
            "الخدمات: الكاميرات وصيانة DVR، أنظمة التحكم في الدخول، الدش والشاشات.\n"
            "المعاينة مجانية للتركيب فقط؛ ويُحدد السعر بعد المعاينة.\nواتساب: 01111325395"
        )

    @staticmethod
    def check_gmail() -> str:
        return (
            "أنا منجز. ألصق نص الرسالة أو أرسل From وSubject ومحتوى الرسالة، "
            "وسأساعدك في فهمها وصياغة مسودة للمراجعة. لا أفتح البريد ولا أرسل أو أحذف أي رسالة."
        )

    @staticmethod
    def draft_email(email_id: str, reply_text: str) -> dict[str, str]:
        """Return a local draft record; deliberately has no send-email capability."""
        return {
            "email_id": email_id,
            "draft": reply_text,
            "status": "awaiting_owner_review",
            "sent": "false",
        }


def route_message(text: str, update: Any = None) -> str:
    """Backward-compatible Telegram adapter used by bot.py and older callers."""
    return MongezAgent().respond(text, is_owner=is_owner(update))


async def handle_start(update: Any, context: Any) -> None:
    message = getattr(update, "effective_message", None)
    if message:
        await message.reply_text("مرحباً، أنا منجز. أرسل رسالتك بالعربية أو الإنجليزية.")


async def handle_email(update: Any, context: Any) -> None:
    message = getattr(update, "effective_message", None)
    if message is None:
        return
    if not is_owner(update):
        await message.reply_text("هذا الأمر متاح للمالك فقط.")
        return
    await message.reply_text(MongezAgent().check_gmail())


async def handle_message(update: Any, context: Any) -> None:
    message = getattr(update, "effective_message", None)
    if message is None or not getattr(message, "text", None):
        return
    import asyncio

    answer = await asyncio.to_thread(route_message, message.text, update)
    await message.reply_text(answer)


def run_agent() -> None:
    """Start the Telegram polling interface (legacy entry point)."""
    import os
    from telegram.ext import Application, CommandHandler, MessageHandler, filters

    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is not configured")
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("ايميل", handle_email))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()


if __name__ == "__main__":
    run_agent()
