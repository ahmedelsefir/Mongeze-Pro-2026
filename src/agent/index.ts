import { SYSTEM_PROMPT } from "./prompts/system";
import { tools, createOrder } from "./tools";
import {
  ensureSession,
  loadHistory,
  saveMessage,
  updateSessionState,
} from "./memory/dbMemory";
import { env } from "../config/env";
import type { AgentMessage, AgentStepLog } from "../types/agent";

function extractCode(text: string): string {
  const match = text.match(/```(?:[A-Za-z0-9_+#.-]*)?\s*([\s\S]*?)```/);
  if (match) return match[1].trim();
  const parts = text.split(":");
  return parts.length === 2 ? parts[1].trim() : text.trim();
}

function matches(text: string, pattern: RegExp): boolean {
  return pattern.test(text);
}

export interface RespondOptions {
  channel?: string;
  externalId?: string;
  isOwner?: boolean;
}

export class MongezAgent {
  /** Expose the behavior contract for integrations that supply their own model. */
  static readonly systemPrompt = SYSTEM_PROMPT;

  private logs: AgentStepLog[] = [];

  getStepLogs(): AgentStepLog[] {
    return this.logs;
  }

  private log(step: AgentStepLog["step"], detail: string): void {
    this.logs.push({ step, detail, at: new Date().toISOString() });
  }

  async respond(prompt: string, options: RespondOptions = {}): Promise<string> {
    const channel = options.channel ?? "api";
    const externalId = options.externalId ?? "anonymous";
    const isOwner = options.isOwner ?? false;
    this.logs = [];

    const text = (prompt ?? "").trim();
    this.log("perceive", `received ${text.length} chars via ${channel}`);
    if (!text) return "أرسل طلبك أو سؤالك حتى أساعدك.";

    const session = await ensureSession(channel, externalId);
    const history = await loadHistory(session.id);
    this.log("perceive", `loaded session ${session.id} with ${history.length} prior messages`);

    await saveMessage(session.id, { role: "user", content: text });

    const reply = isOwner
      ? await this.personalResponse(text, history)
      : await this.businessResponse(text);
    this.log("act", reply.slice(0, 80));

    await saveMessage(session.id, { role: "agent", content: reply });
    await updateSessionState(session.id, {
      ...session.state,
      lastIntent: this.logs.find((l) => l.step === "reason")?.detail ?? "unknown",
      lastReplyAt: new Date().toISOString(),
      lastStatus: "completed",
    });
    this.log("persist", "message history and session state updated");
    return reply;
  }

  think(prompt: string): Promise<string> {
    return this.respond(prompt, { isOwner: false });
  }

  private async personalResponse(
    text: string,
    history: AgentMessage[],
  ): Promise<string> {
    this.log("reason", "owner mode: matching personal tool");
    void history;

    if (matches(text, /(?:^remember\b|^تذكر\b|^احفظ\b|تذكر أن)/i)) {
      const fact = text.replace(
        /(?:^remember\b|^تذكر\b|^احفظ\b|تذكر أن)\s*[:،,\-]?\s*/i,
        "",
      );
      return tools.find((t) => t.name === "remember")!.run(fact);
    }

    if (matches(text, /(search memory|what do you remember|ابحث في الذاكرة|ماذا تتذكر|فكر في)/i)) {
      const query = text
        .replace(/(search memory|what do you remember|ابحث في الذاكرة|ماذا تتذكر|فكر في)/gi, "")
        .replace(/^[\s:؟?-]+|[\s:؟?-]+$/g, "");
      return tools.find((t) => t.name === "search_memory")!.run(query);
    }

    if (matches(text, /(summari[sz]e|لخص|تلخيص|اختصر)/i)) {
      const content = text
        .replace(/^(?:please\s+)?(?:summari[sz]e|لخص|تلخيص|اختصر)\s*[:：-]?\s*/i, "")
        .trim();
      if (!content || content === text) {
        return "أرسل النص بعد كلمة «لخص» لألخصه لك.";
      }
      let summary = content
        .split(/(?<=[.!؟?])\s+|\n+/)
        .map((part) => part.trim())
        .filter(Boolean)
        .join(" ");
      if (summary.length > 700) {
        summary = summary.slice(0, 697).replace(/\s+\S*$/, "") + "...";
      }
      return `الملخص:\n${summary}`;
    }

    if (matches(text, /(organize task|organize tasks|task|tasks|مهمة|مهام|نظم)/i)) {
      return tools.find((t) => t.name === "organize_task")!.run(text);
    }

    if (matches(text, /(explain|شرح|فسر|وضح)/i)) {
      const code = extractCode(text);
      if (code && code !== text) return tools.find((t) => t.name === "explain_code")!.run(code);
      return "أرسل الكود داخل ```code``` واطلب شرحه.";
    }

    if (matches(text, /(fix|debug|solve|صحح|اصلح|صلح|إصلاح)/i)) {
      const code = extractCode(text);
      if (code && code !== text) return tools.find((t) => t.name === "fix_code")!.run(code);
      return "أرسل الكود داخل ```code``` مع رسالة الخطأ وبيئة التشغيل لأساعدك في تشخيصه.";
    }

    if (matches(text, /(email|بريد|إيميل|ايميل|mail)/i)) {
      return MongezAgent.checkGmail();
    }

    if (matches(text, /(file|files|folder|directory|ملف|ملفات|مجلد)/i)) {
      return "أرسل أسماء الملفات والمجلدات وطريقة التنظيم المطلوبة؛ لن أغيّر ملفات جهازك دون طلب واضح.";
    }

    return (
      "أنا منجز، مساعدك الشخصي والبرمجي. أستطيع تلخيص النصوص وتنظيم المهام " +
      "وشرح الكود وإصلاحه مبدئياً وحفظ المعلومات والبحث في الذاكرة ومساعدتك في إعداد مسودات البريد."
    );
  }

  private async businessResponse(text: string): Promise<string> {
    this.log("reason", "business mode: matching business tool");

    if (matches(text, /(create order|new order|طلب جديد|عايز اطلب|أريد طلب|نحتاج طلب)/i)) {
      const nameMatch = text.match(/(?:name|الاسم)\s*[:=]\s*([^,\n]+)/i);
      const placeMatch = text.match(/(?:place|location|المكان|المنطقة)\s*[:=]\s*([^,\n]+)/i);
      const serviceMatch = text.match(/(?:service|الخدمة)\s*[:=]\s*([^,\n]+)/i);
      if (!(nameMatch && placeMatch && serviceMatch)) {
        return "لتسجيل طلب خدمة رؤية الخير في المهندسين، أرسل: الاسم: ...، المكان: ...، الخدمة: ...";
      }
      return createOrder(nameMatch[1], placeMatch[1], serviceMatch[1]);
    }

    if (
      matches(
        text,
        /(services|available services|الخدمات|ايه الخدمات|خدماتكم|camera|cctv|dvr|access control|دش|شاش|كاميرا|كاميرات|صيانة)/i,
      )
    ) {
      return tools.find((t) => t.name === "get_services")!.run("");
    }
    return MongezAgent.businessWelcome();
  }

  static businessWelcome(): string {
    return (
      "مرحباً، أنا مساعد أعمال شركة رؤية الخير في المهندسين فقط.\n" +
      "الخدمات: الكاميرات وصيانة DVR، أنظمة التحكم في الدخول، الدش والشاشات.\n" +
      "المعاينة مجانية للتركيب فقط؛ ويُحدد السعر بعد المعاينة.\nواتساب: 01111325395"
    );
  }

  static checkGmail(): string {
    return (
      "أنا منجز. ألصق نص الرسالة أو أرسل From وSubject ومحتوى الرسالة، " +
      "وسأساعدك في فهمها وصياغة مسودة للمراجعة. لا أفتح البريد ولا أرسل أو أحذف أي رسالة."
    );
  }

  static draftEmail(emailId: string, replyText: string): Record<string, string> {
    return {
      email_id: emailId,
      draft: replyText,
      status: "awaiting_owner_review",
      sent: "false",
    };
  }
}

export function isConfiguredOwner(telegramId: string, username = ""): boolean {
  if (telegramId && env.ownerTelegramIds.includes(telegramId)) return true;
  return env.legacyOwnerUsernames.includes(username.toLowerCase());
}

export function lastStepLogs(agent: MongezAgent): AgentStepLog[] {
  return agent.getStepLogs();
}
