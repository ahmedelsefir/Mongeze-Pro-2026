export function fixCode(code: string): string {
  const clean = code.trim();
  if (!clean) return "لم يتم إرسال كود لإصلاحه.";
  return (
    "لا يمكن تحديد إصلاح خطأ التشغيل من الكود وحده. أرسل رسالة الخطأ الكاملة، " +
    "إصدار اللغة، المدخلات المتوقعة والسلوك الفعلي. لم يتم تشغيل الكود.\n" +
    "```text\n" + clean + "\n```"
  );
}
