import { saveTask } from "../memory/dbMemory";

export async function organizeTask(task: string): Promise<string> {
  const clean = task.trim();
  if (!clean) return "أرسل المهمة التي تريد تنظيمها.";
  const saved = await saveTask(clean);
  return `تمت إضافة المهمة إلى قائمة المهام:\n${saved.title}`;
}
