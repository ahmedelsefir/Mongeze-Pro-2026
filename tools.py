"""Tools used by the Mongez AI agent."""

import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MEMORY_PATH = BASE_DIR / "memory.json"
ORDERS_PATH = BASE_DIR / "orders.txt"
TASKS_PATH = BASE_DIR / "tasks.txt"


def _load_memory() -> dict:
    if not MEMORY_PATH.exists():
        return {"facts": [], "orders": []}

    try:
        with MEMORY_PATH.open("r", encoding="utf-8") as handle:
            memory = json.load(handle)
            if not isinstance(memory, dict):
                return {"facts": [], "orders": []}
            memory.setdefault("facts", [])
            memory.setdefault("orders", [])
            return memory
    except (json.JSONDecodeError, OSError):
        return {"facts": [], "orders": []}


def _save_memory(memory: dict) -> None:
    with MEMORY_PATH.open("w", encoding="utf-8") as handle:
        json.dump(memory, handle, ensure_ascii=False, indent=2)


def tool_get_services() -> str:
    """Return Rouyet El-Khair services and business rules."""
    return (
        "خدمات رؤية الخير - المهندسين فقط:\n"
        "• تركيب وصيانة الكاميرات وDVR\n"
        "• أنظمة التحكم في الدخول (access control)\n"
        "• تركيب الدش\n"
        "• تركيب الشاشات\n\n"
        "المعاينة مجانية لتركيب فقط.\n"
        "لا يوجد سعر ثابت؛ السعر يُحدد بعد المعاينة.\n"
        "واتساب: 01111325395"
    )


def tool_create_order(name: str, place: str, service: str) -> str:
    """Save an order to orders.txt and memory.json."""
    timestamp = datetime.now(timezone.utc).isoformat()

    order = {
        "name": name.strip() or "غير محدد",
        "place": place.strip() or "غير محدد",
        "service": service.strip() or "غير محدد",
        "timestamp": timestamp,
    }

    line = (
        f"[{timestamp}] name={order['name']} | "
        f"place={order['place']} | service={order['service']}\n"
    )
    with ORDERS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line)

    memory = _load_memory()
    memory.setdefault("orders", []).append(order)
    _save_memory(memory)

    return (
        "تم تسجيل الطلب بنجاح في orders.txt وفي memory.json.\n"
        f"الاسم: {order['name']}\n"
        f"المكان: {order['place']}\n"
        f"الخدمة: {order['service']}"
    )


def tool_organize_tasks(task: str) -> str:
    """Append a task to tasks.txt."""
    clean_task = task.strip()
    if not clean_task:
        return "أرسل المهمة التي تريد تنظيمها."

    timestamp = datetime.now(timezone.utc).isoformat()

    with TASKS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {clean_task}\n")

    return f"تمت إضافة المهمة إلى tasks.txt:\n{clean_task}"


def tool_explain_code(code: str) -> str:
    """Return a beginner-friendly, step-by-step Arabic explanation."""
    clean_code = code.strip()
    if not clean_code:
        return "لم يتم إرسال كود لشرحه."

    lines = [
        line for line in clean_code.splitlines()
        if line.strip()
    ]

    result = ["شرح الكود خطوة بخطوة:\n"]

    for number, line in enumerate(lines, start=1):
        stripped = line.strip()

        if stripped.startswith("#") or stripped.startswith("//"):
            result.append(
                f"{number}. تعليق توضيحي: {stripped.lstrip('#/ ').strip()}"
            )
        elif stripped.startswith(("def ", "async def ")):
            result.append(
                f"{number}. تعريف دالة: يبدأ الكود تعريف وظيفة يمكن استدعاؤها "
                "وتنفيذ تعليماتها."
            )
        elif stripped.startswith("class "):
            result.append(
                f"{number}. تعريف صنف: يتم إنشاء نموذج للكائنات يحتوي بيانات ودوال."
            )
        elif stripped.startswith(("for ", "while ")):
            result.append(
                f"{number}. حلقة تكرار: يتم تنفيذ الجزء الموجود بداخلها "
                "حسب شرط التكرار أو عدد العناصر."
            )
        elif stripped.startswith("if ") or stripped.startswith("elif "):
            result.append(
                f"{number}. شرط منطقي: ينفذ الكود التالي فقط إذا كان الشرط محققاً."
            )
        elif stripped.startswith("else"):
            result.append(
                f"{number}. البديل: ينفذ هذا الجزء عندما لا تتحقق الشروط السابقة."
            )
        elif stripped.startswith(("import ", "from ")):
            result.append(
                f"{number}. استيراد: يجعل المكتبة أو الأداة المحددة متاحة للاستخدام."
            )
        elif "=" in stripped:
            left, right = stripped.split("=", 1)
            result.append(
                f"{number}. تعيين قيمة: تخزن `{left.strip()}` القيمة "
                f"`{right.strip()}` لاستخدامها لاحقاً."
            )
        elif stripped.startswith("return "):
            result.append(
                f"{number}. إرجاع النتيجة: ينهي تنفيذ الدالة ويرجع القيمة المخصصة."
            )
        elif stripped.startswith(("print(", "console.log(")):
            result.append(
                f"{number}. إخراج للعرض: يطبع القيمة أو النص على شاشة المخرجات."
            )
        else:
            result.append(
                f"{number}. أمر تنفيذ: `{stripped}` "
                "وهو جزء من تدفق البرنامج ويعتمد على المتغيرات والسياق السابق."
            )

    result.append("\nيمكن إرسال رسالة الخطأ وبيئة التشغيل للحصول على شرح أكثر دقة.")
    return "\n".join(result)


def tool_fix_code(code: str) -> str:
    """Return the reviewed code and identify required follow-up information."""
    clean_code = code.strip()
    if not clean_code:
        return "لم يتم إرسال كود لإصلاحه."

    return (
        "الكود للمراجعة والإصلاح:\n"
        "```text\n"
        f"{clean_code}\n"
        "```\n\n"
        "ما الذي كان يحتاج إصلاحاً:\n"
        "لم يتم تشغيل الكود أو افتراض بيئة تشغيل محددة. "
        "أرسل رسالة الخطأ بالضبط وإصدار اللغة والمكتبات المستخدمة "
        "حتى يتمكن منجز من إجراء إصلاح دقيق."
    )


def tool_remember(fact: str) -> str:
    """Save a fact in memory.json."""
    clean_fact = fact.strip()
    if not clean_fact:
        return "أرسل المعلومة التي تريدني أن أحفظها."

    memory = _load_memory()
    memory.setdefault("facts", []).append({
        "fact": clean_fact,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _save_memory(memory)

    return f"تم حفظ المعلومة في memory.json:\n{clean_fact}"


def tool_search_memory(query: str) -> str:
    """Search saved facts in memory.json."""
    clean_query = (query or "").strip().lower()
    memory = _load_memory()

    matches = []

    for item in memory.get("facts", []):
        if isinstance(item, dict):
            value = item.get("fact", "")
        else:
            value = str(item)

        if not clean_query or clean_query in value.lower():
            matches.append(value)

    if not matches:
        if clean_query:
            return f"لا توجد معلومات محفوظة تطابق: {query}"
        return "لا توجد معلومات محفوظة حالياً."

    return "تم العثور على المعلومة في الذاكرة:\n- " + "\n- ".join(matches)
