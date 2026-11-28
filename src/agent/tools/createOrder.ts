import { saveOrder } from "../memory/dbMemory";

export async function createOrder(
  name: string,
  place: string,
  service: string,
): Promise<string> {
  const order = await saveOrder(
    name.trim() || "غير محدد",
    place.trim() || "غير محدد",
    service.trim() || "غير محدد",
  );
  return (
    "تم تسجيل طلب الخدمة.\n" +
    `الاسم: ${order.customerName}\n` +
    `المكان: ${order.place}\n` +
    `الخدمة: ${order.service}`
  );
}
