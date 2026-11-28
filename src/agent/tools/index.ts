import type { ToolDefinition } from "../../types/agent";
import { getServices } from "./getServices";
import { createOrder } from "./createOrder";
import { organizeTask } from "./organizeTask";
import { remember } from "./remember";
import { searchMemory } from "./searchMemory";
import { explainCode } from "./explainCode";
import { fixCode } from "./fixCode";

export {
  getServices,
  createOrder,
  organizeTask,
  remember,
  searchMemory,
  explainCode,
  fixCode,
};

export const tools: ToolDefinition[] = [
  {
    name: "get_services",
    description: "عرض خدمات رؤية الخير وقواعد العمل.",
    run: () => getServices(),
  },
  {
    name: "create_order",
    description: "تسجيل طلب خدمة جديد (الاسم، المكان، الخدمة).",
    run: () => "create_order requires structured fields; call createOrder(name, place, service).",
  },
  {
    name: "organize_task",
    description: "إضافة مهمة إلى قائمة المهام.",
    run: (input) => organizeTask(input),
  },
  {
    name: "remember",
    description: "حفظ معلومة في الذاكرة طويلة الأمد.",
    run: (input) => remember(input),
  },
  {
    name: "search_memory",
    description: "البحث في المعلومات المحفوظة.",
    run: (input) => searchMemory(input),
  },
  {
    name: "explain_code",
    description: "شرح بنيوي للكود دون تشغيله.",
    run: (input) => explainCode(input),
  },
  {
    name: "fix_code",
    description: "تشخيص مبدئي لأخطاء الكود دون تشغيله.",
    run: (input) => fixCode(input),
  },
];
