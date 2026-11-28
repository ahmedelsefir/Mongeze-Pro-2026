export function explainCode(code: string): string {
  const clean = code.trim();
  if (!clean) return "لم يتم إرسال كود لشرحه.";
  const lines = clean.split("\n").map((line) => line.trim()).filter(Boolean);
  const result = ["شرح بنيوي للكود (دون تشغيله):"];
  lines.forEach((line, index) => {
    let description: string;
    if (line.startsWith("//") || line.startsWith("#")) {
      description = "تعليق توضيحي.";
    } else if (/^(async\s+)?(def|function)\b/.test(line)) {
      description = "تعريف دالة قابلة للاستدعاء.";
    } else if (/^class\b/.test(line)) {
      description = "تعريف صنف يجمع بيانات وسلوكاً.";
    } else if (/^(for|while)\b/.test(line)) {
      description = "حلقة تكرار.";
    } else if (/^(if|elif|else)\b/.test(line) || line === "else" || line === "}") {
      description = "فرع أو شرط للتحكم في التنفيذ.";
    } else if (/^(import|from|const|let|var)\b/.test(line)) {
      description = "استيراد مكتبة أو مكوّن أو تعيين متغير.";
    } else if (/^return\b/.test(line)) {
      description = "إرجاع نتيجة من الدالة.";
    } else if (line.includes("=")) {
      description = "تعيين قيمة لمتغير أو خاصية.";
    } else {
      description = "تعليمة؛ تفسيرها الدقيق يعتمد على سياق البرنامج.";
    }
    result.push(`${index + 1}. \`${line}\` — ${description}`);
  });
  result.push("لم يتم تنفيذ الكود. أرسل اللغة والسياق إن أردت شرحاً أعمق.");
  return result.join("\n");
}
