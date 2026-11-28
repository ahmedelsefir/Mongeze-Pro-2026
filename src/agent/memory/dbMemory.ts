import type {
  AgentMessage,
  AgentSession,
  AgentTask,
  AgentTaskResult,
  AgentTaskStatus,
  MemoryFact,
  ServiceOrder,
} from "../../types/agent";
import { getDb } from "../../db/client";

const SUPABASE_CONFIGURATION_HINT =
  "Check EXTERNAL_SUPABASE_URL / EXTERNAL_SUPABASE_ANON_KEY (preferred) or SUPABASE_URL / SUPABASE_ANON_KEY, and verify database permissions.";

function errorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === "object" && error !== null && "message" in error) {
    return String(error.message);
  }
  return String(error);
}

async function withDbError<T>(operation: string, action: () => Promise<T>): Promise<T> {
  try {
    return await action();
  } catch (error) {
    throw new Error(
      `[agent memory] ${operation} failed: ${errorMessage(error)}. ${SUPABASE_CONFIGURATION_HINT}`,
      { cause: error },
    );
  }
}

function checkDbError(operation: string, error: unknown): void {
  if (error) {
    throw new Error(
      `[agent memory] ${operation} failed: ${errorMessage(error)}. ${SUPABASE_CONFIGURATION_HINT}`,
      { cause: error },
    );
  }
}

export async function ensureSession(
  channel: string,
  externalId: string,
): Promise<AgentSession> {
  return withDbError("ensure session", async () => {
    const db = getDb();
    const { data, error } = await db
      .from("agent_sessions")
      .select("id, channel, external_id, state")
      .eq("channel", channel)
      .eq("external_id", externalId)
      .maybeSingle();
    checkDbError("read session", error);

    if (data) {
      return {
        id: data.id,
        channel: data.channel,
        externalId: data.external_id,
        state: (data.state ?? {}) as Record<string, unknown>,
      };
    }

    const { data: inserted, error: insertError } = await db
      .from("agent_sessions")
      .insert({ channel, external_id: externalId, state: {} })
      .select("id, channel, external_id, state")
      .single();
    checkDbError("create session", insertError);
    if (!inserted) throw new Error("Database returned no session row after insert");

    return {
      id: inserted.id,
      channel: inserted.channel,
      externalId: inserted.external_id,
      state: (inserted.state ?? {}) as Record<string, unknown>,
    };
  });
}

export async function loadHistory(
  sessionId: string,
  limit = 50,
): Promise<AgentMessage[]> {
  return withDbError("load conversation history", async () => {
    const { data, error } = await getDb()
      .from("agent_messages")
      .select("role, content, metadata")
      .eq("session_id", sessionId)
      .order("created_at", { ascending: true })
      .limit(limit);
    checkDbError("load conversation history", error);
    return (data ?? []).map((row) => ({
      role: row.role as AgentMessage["role"],
      content: row.content,
      metadata: (row.metadata ?? {}) as Record<string, unknown>,
    }));
  });
}

export async function saveMessage(
  sessionId: string,
  message: AgentMessage,
): Promise<void> {
  return withDbError("save conversation message", async () => {
    const { error } = await getDb().from("agent_messages").insert({
      session_id: sessionId,
      role: message.role,
      content: message.content,
      metadata: message.metadata ?? {},
    });
    checkDbError("save conversation message", error);
  });
}

export async function updateSessionState(
  sessionId: string,
  state: Record<string, unknown>,
): Promise<void> {
  return withDbError("update session state", async () => {
    const { error } = await getDb()
      .from("agent_sessions")
      .update({ state, updated_at: new Date().toISOString() })
      .eq("id", sessionId);
    checkDbError("update session state", error);
  });
}

export async function saveFact(content: string): Promise<MemoryFact> {
  return withDbError("save memory fact", async () => {
    const { data, error } = await getDb()
      .from("agent_facts")
      .insert({ content })
      .select("id, content, created_at")
      .single();
    checkDbError("save memory fact", error);
    if (!data) throw new Error("Database returned no fact row after insert");
    return { id: data.id, content: data.content, createdAt: data.created_at };
  });
}

export async function listFacts(query = ""): Promise<MemoryFact[]> {
  return withDbError("list memory facts", async () => {
    let request = getDb()
      .from("agent_facts")
      .select("id, content, created_at")
      .order("created_at", { ascending: false })
      .limit(100);
    if (query.trim()) request = request.ilike("content", `%${query.trim()}%`);
    const { data, error } = await request;
    checkDbError("list memory facts", error);
    return (data ?? []).map((row) => ({
      id: row.id,
      content: row.content,
      createdAt: row.created_at,
    }));
  });
}

export async function saveTask(
  title: string,
  options: { status?: AgentTaskStatus; toolResult?: AgentTaskResult } = {},
): Promise<AgentTask> {
  return withDbError("save task", async () => {
    const { data, error } = await getDb()
      .from("agent_tasks")
      .insert({
        title,
        status: options.status ?? "open",
        tool_result: options.toolResult ?? null,
      })
      .select("id, title, status, tool_result, created_at, updated_at")
      .single();
    checkDbError("save task", error);
    if (!data) throw new Error("Database returned no task row after insert");
    return mapTask(data);
  });
}

export async function listTasks(status?: AgentTaskStatus): Promise<AgentTask[]> {
  return withDbError("list tasks", async () => {
    let request = getDb()
      .from("agent_tasks")
      .select("id, title, status, tool_result, created_at, updated_at")
      .order("created_at", { ascending: false })
      .limit(100);
    if (status) request = request.eq("status", status);
    const { data, error } = await request;
    checkDbError("list tasks", error);
    return (data ?? []).map(mapTask);
  });
}

export async function updateTask(
  taskId: string,
  update: { status?: AgentTaskStatus; toolResult?: AgentTaskResult },
): Promise<AgentTask> {
  return withDbError("update task", async () => {
    const patch: { status?: AgentTaskStatus; tool_result?: AgentTaskResult | null; updated_at: string } = {
      updated_at: new Date().toISOString(),
    };
    if (update.status !== undefined) patch.status = update.status;
    if (update.toolResult !== undefined) patch.tool_result = update.toolResult;

    const { data, error } = await getDb()
      .from("agent_tasks")
      .update(patch)
      .eq("id", taskId)
      .select("id, title, status, tool_result, created_at, updated_at")
      .single();
    checkDbError("update task", error);
    if (!data) throw new Error(`Task ${taskId} was not found`);
    return mapTask(data);
  });
}

function mapTask(row: {
  id: string;
  title: string;
  status: string;
  tool_result: AgentTaskResult | null;
  created_at: string;
  updated_at: string;
}): AgentTask {
  return {
    id: row.id,
    title: row.title,
    status: row.status as AgentTaskStatus,
    result: row.tool_result ?? null,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

export async function saveOrder(
  customerName: string,
  place: string,
  service: string,
): Promise<ServiceOrder> {
  return withDbError("save service order", async () => {
    const { data, error } = await getDb()
      .from("agent_orders")
      .insert({ customer_name: customerName, place, service })
      .select("id, customer_name, place, service, created_at")
      .single();
    checkDbError("save service order", error);
    if (!data) throw new Error("Database returned no order row after insert");
    return {
      id: data.id,
      customerName: data.customer_name,
      place: data.place,
      service: data.service,
      createdAt: data.created_at,
    };
  });
}
