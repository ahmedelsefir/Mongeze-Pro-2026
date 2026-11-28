import { listFacts } from "../memory/dbMemory";

export async function searchMemory(query = ""): Promise<string> {
  const matches = await listFacts(query);
  if (!matches.length) {
    return query.trim()
      ? `لا توجد معلومات محفوظة تطابق: ${query}`
      : "لا توجد معلومات محفوظة حالياً.";
  }
  return (
    "تم العثور على المعلومات في الذاكرة:\n- " +
    matches.map((fact) => fact.content).join("\n- ")
  );
}
