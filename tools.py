"""Persistent local tools used by MongezAgent."""

import ast
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
        "• تركيب الدش والشاشات\n\n"
        "المعاينة مجانية للتركيب فقط.\n"
        "لا يوجد سعر ثابت؛ السعر يُحدد بعد المعاينة.\n"
        "واتساب: 01111325395"
    )


def tool_create_order(name: str, place: str, service: str) -> str:
    """Save a service inquiry to the existing text log and JSON memory."""
    timestamp = datetime.now(timezone.utc).isoformat()
    order = {
        "name": name.strip() or "غير محدد",
        "place": place.strip() or "غير محدد",
        "service": service.strip() or "غير محدد",
        "timestamp": timestamp,
    }
    with ORDERS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(
            f"[{timestamp}] name={order['name']} | place={order['place']} | service={order['service']}\n"
        )
    memory = _load_memory()
    memory.setdefault("orders", []).append(order)
    _save_memory(memory)
    return f"تم تسجيل طلب الخدمة.\nالاسم: {order['name']}\nالمكان: {order['place']}\nالخدمة: {order['service']}"


def tool_organize_tasks(task: str) -> str:
    """Append a personal task to the existing tasks.txt file."""
    clean_task = task.strip()
    if not clean_task:
        return "أرسل المهمة التي تريد تنظيمها."
    timestamp = datetime.now(timezone.utc).isoformat()
    with TASKS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {clean_task}\n")
    return f"تمت إضافة المهمة إلى tasks.txt:\n{clean_task}"


def tool_explain_code(code: str) -> str:
    """Provide a lightweight structural explanation without executing code."""
    clean_code = code.strip()
    if not clean_code:
        return "لم يتم إرسال كود لشرحه."
    lines = [line.strip() for line in clean_code.splitlines() if line.strip()]
    result = ["شرح بنيوي للكود (دون تشغيله):"]
    for number, line in enumerate(lines, start=1):
        if line.startswith(("#", "//")):
            description = "تعليق توضيحي."
        elif line.startswith(("def ", "async def ")):
            description = "تعريف دالة قابلة للاستدعاء."
        elif line.startswith("class "):
            description = "تعريف صنف يجمع بيانات وسلوكاً."
        elif line.startswith(("for ", "while ")):
            description = "حلقة تكرار."
        elif line.startswith(("if ", "elif ", "else")):
            description = "فرع أو شرط للتحكم في التنفيذ."
        elif line.startswith(("import ", "from ")):
            description = "استيراد مكتبة أو مكوّن."
        elif line.startswith("return "):
            description = "إرجاع نتيجة من الدالة."
        elif "=" in line:
            description = "تعيين قيمة لمتغير أو خاصية."
        else:
            description = "تعليمة؛ تفسيرها الدقيق يعتمد على سياق البرنامج."
        result.append(f"{number}. `{line}` — {description}")
    result.append("لم يتم تنفيذ الكود. أرسل اللغة والسياق إن أردت شرحاً أعمق.")
    return "\n".join(result)


def tool_fix_code(code: str) -> str:
    """Perform safe Python syntax diagnostics and request context for runtime bugs."""
    clean_code = code.strip()
    if not clean_code:
        return "لم يتم إرسال كود لإصلاحه."
    try:
        ast.parse(clean_code)
    except SyntaxError as error:
        location = f"السطر {error.lineno or '?'}"
        if error.offset:
            location += f"، العمود {error.offset}"
        detail = error.msg or "خطأ نحوي"
        return (
            f"وجدت خطأً نحوياً مبدئياً في Python عند {location}: {detail}.\n"
            "تحقق من النقطتين بعد if/for/def، والأقواس وعلامات الاقتباس. "
            "هذا تشخيص نحوي فقط؛ لم يتم تشغيل الكود أو تعديله تلقائياً.\n"
            f"```python\n{clean_code}\n```"
        )
    except (ValueError, TypeError):
        pass
    return (
        "اجتاز النص فحص البنية النحوية الأساسية لـ Python (إن كان Python)، "
        "لكن لا يمكن تحديد إصلاح خطأ التشغيل من الكود وحده. أرسل رسالة الخطأ "
        "الكاملة، إصدار اللغة، المدخلات المتوقعة والسلوك الفعلي. لم يتم تشغيل الكود.\n"
        f"```text\n{clean_code}\n```"
    )


def tool_remember(fact: str) -> str:
    """Save a personal fact in the existing memory.json store."""
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
    """Search the existing JSON fact memory case-insensitively."""
    clean_query = (query or "").strip().casefold()
    memory = _load_memory()
    matches = []
    for item in memory.get("facts", []):
        value = item.get("fact", "") if isinstance(item, dict) else str(item)
        if not clean_query or clean_query in value.casefold():
            matches.append(value)
    if not matches:
        return f"لا توجد معلومات محفوظة تطابق: {query}" if clean_query else "لا توجد معلومات محفوظة حالياً."
    return "تم العثور على المعلومات في الذاكرة:\n- " + "\n- ".join(matches)
