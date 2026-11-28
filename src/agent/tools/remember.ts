import { saveFact } from "../memory/dbMemory";

export async function remember(fact: string): Promise<string> {
  const clean = fact.trim();
  if (!clean) return "أرسل المعلومة التي تريدني أن أحفظها.";
  await saveFact(clean);
  return `تم حفظ المعلومة في الذاكرة:\n${clean}`;
}
