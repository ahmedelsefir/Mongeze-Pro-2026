"""Mongez - Personal and business AI agent for Telegram."""

import asyncio
import os
import re
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

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
MEMORY_PATH = BASE_DIR / "memory.json"


def load_brain() -> dict:
    import json

    with BRAIN_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


BRAIN = load_brain()


def is_owner(update: Update) -> bool:
    """Identify Ahmed as the owner using Telegram username or user ID."""
    user = update.effective_user
    if not user:
        return False

    username = (user.username or "").lower()
    owner_usernames = {"ahmedelsefir", "ahmedmostafa"}

    owner_ids = BRAIN.get("owner_ids", [])
    telegram_id = str(user.id) if user.id else ""

    return username in owner_usernames or telegram_id in owner_ids


def extract_code(text: str) -> str:
    match = re.search(r"```(?:[A-Za-z0-9_+#.-]*)?\s*(.*?)```", text, flags=re.S)
    if match:
        return match.group(1).strip()

    parts = text.split(":", 1)
    return parts[1].strip() if len(parts) == 2 else text.strip()


def route_message(text: str, update: Update) -> str:
    """Understand Arabic or English and route the message to a tool or assistant mode."""
    message = text.strip()
    lowered = message.lower()

    # Remember a fact
    if re.search(r"(?:^remember\b|^تذكر\b|^احفظ\b|تذكر أن)", lowered):
        fact = re.sub(
            r"(?:^remember\b|^تذكر\b|^احفظ\b|تذكر أن)\s*[:،,\-]?\s*",
            "",
            message,
            flags=re.I,
        )
        return tool_remember(fact)

    # Search memory
    if re.search(
        r"(search memory|what do you remember|ابحث في الذاكرة|ماذا تتذكر|فكر في)",
        lowered,
    ):
        query = re.sub(
            r"(search memory|what do you remember|ابحث في الذاكرة|ماذا تتذكر|فكر في)",
            "",
            message,
            flags=re.I,
        ).strip(" :؟?-")
        return tool_search_memory(query)

    # Organize tasks
    if re.search(r"(organize task|organize tasks|task|tasks|مهمة|مهام|نظم)", lowered):
        return tool_organize_tasks(message)

    # Show services
    if re.search(
        r"(services|available services|الخدمات|ايه الخدمات|خدماتكم|خدماتكم؟)",
        lowered,
    ):
        return tool_get_services()

    # Create an order
    if re.search(
        r"(create order|new order|طلب جديد|عايز اطلب|أريد طلب|نحتاج طلب)",
        lowered,
    ):
        name_match = re.search(r"(?:name|الاسم)\s*[:=]\s*([^,\n]+)", message, re.I)
        place_match = re.search(r"(?:place|location|المكان|المنطقة)\s*[:=]\s*([^,\n]+)", message, re.I)
        service_match = re.search(r"(?:service|الخدمة)\s*[:=]\s*([^,\n]+)", message, re.I)

        name = name_match.group(1).strip() if name_match else "غير محدد"
        place = place_match.group(1).strip() if place_match else "غير محدد"
        service = service_match.group(1).strip() if service_match else message
        return tool_create_order(name, place, service)

    code = extract_code(message)

    # Explain code
    if re.search(r"(explain|شرح|فسر|وضح)", lowered) and code:
        return tool_explain_code(code)

    # Fix code
    if re.search(
        r"(fix|debug|debug this|solve|صحح|اصلح|صلح|fix code|إصلاح)",
        lowered,
    ) and code:
        return tool_fix_code(code)

    business_keywords = (
        r"(camera|cctv|dvr|access control|entry control|"
        r"camera maintenance|دش|شاش|شاشة|شاشات|"
        r"كاميرا|كاميرات|كنترول دخول|تحكم في الدخول|صيانة)"
    )

    # Customers receive only the Rouyet El-Khair / Mohandessin business mode
    if re.search(business_keywords, lowered) and not is_owner(update):
        return (
            "أنا مساعد أعمال شركة رؤية الخير في المهندسين فقط.\n\n"
            "الخدمات المتاحة:\n"
            "• تركيب وصيانة كاميرات المراقبة\n"
            "• صيانة DVR\n"
            "• أنظمة التحكم في الدخول\n"
            "• تركيب الدش\n"
            "• تركيب الشاشات\n\n"
            "المعاينة مجانية للتركيب فقط.\n"
            "لا يوجد سعر ثابت؛ يتم تحديد السعر فقط بعد المعاينة.\n"
            "واتساب: 01111325395"
        )

    # Ahmed owner mode
    if is_owner(update):
        if re.search(r"(email|بريد|إيميل|mail)", lowered):
            return (
                "سأساعدك في صياغة البريد وتنظيم المراسلات.\n"
                "أرسل: المستلم، الموضوع، الهدف، ونقاط الرسالة."
            )

        if re.search(r"(file|files|folder|directory|ملف|ملفات|مجلد)", lowered):
            return (
                "سأساعدك في تنظيم الملفات والمجلدات.\n"
                "أرسل أسماء الملفات، المطلوب تنظيمه، والمجلدات المقصودة."
            )

        if re.search(r"(order|طلب|شراء)", lowered):
            return (
                "لنظم الطلب: أرسل اسم الصنف، الكمية، المكان، وتاريخ الطلب المطلوب."
            )

        if re.search(r"(programming|برمجة|كود|python|code|bug)", lowered):
            return (
                "أنا منجز، مساعدك البرمجي الشخصي.\n"
                "يمكنني شرح الكود خطوة بخطوة أو مساعدتك في إصلاحه.\n"
                "الصق الكود داخل علامات الكود الثلاثية، أو اكتب: شرح الكود أو أصلح الكود."
            )

        return (
            "أنا منجز، المساعد الشخصي للمهندس أحمد مصطفى.\n"
            "أساعدك في البرمجة وشرح الكود وإصلاحه وتنظيم المهام والملفات "
            "والبريد والطلبات. أرسل المهمة التي تريد تنفيذها."
        )

    # Default customer mode
    return (
        "مرحباً، أنا منجز، المساعد التجاري لشركة رؤية الخير في المهندسين فقط.\n"
        "الخدمات: الكاميرات، صيانة DVR، أنظمة التحكم في الدخول، الدش والشاشات.\n"
        "المعاينة مجانية للتركيب فقط فقط؛ السعر يحدد بعد المعاينة ولا توجد أسعار ثابتة.\n"
        "واتساب: 01111325395"
    )


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            "مرحباً، أنا منجز. أرسل رسالتك بالعربية أو الإنجليزية."
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None or not message.text:
        return

    answer = await asyncio.to_thread(route_message, message.text, update)
    await message.reply_text(answer)


def run_agent() -> None:
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    if not telegram_token:
        raise RuntimeError("TELEGRAM_TOKEN is not configured")

    application = Application.builder().token(telegram_token).build()
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.run_polling()


if __name__ == "__main__":
    run_agent()
