import { getDb } from "../../db/client";

export async function organizeTask(task: string): Promise<string> {
  const clean = task.trim();
  if (!clean) return "أرسل المهمة التي تريد تنظيمها.";
  const { error } = await getDb()
    .from("agent_tasks")
    .insert({ title: clean, status: "open" });
  if (error) throw error;
  return `تمت إضافة المهمة إلى قائمة المهام:\n${clean}`;
}
