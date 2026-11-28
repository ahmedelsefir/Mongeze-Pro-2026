import type {
  AgentMessage,
  AgentSession,
  MemoryFact,
  ServiceOrder,
} from "../../types/agent";
import { getDb } from "../../db/client";

export async function ensureSession(
  channel: string,
  externalId: string,
): Promise<AgentSession> {
  const db = getDb();
  const { data, error } = await db
    .from("agent_sessions")
    .select("id, channel, external_id, state")
    .eq("channel", channel)
    .eq("external_id", externalId)
    .maybeSingle();

  if (error) throw error;
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
  if (insertError) throw insertError;

  return {
    id: inserted.id,
    channel: inserted.channel,
    externalId: inserted.external_id,
    state: (inserted.state ?? {}) as Record<string, unknown>,
  };
}

export async function loadHistory(
  sessionId: string,
  limit = 50,
): Promise<AgentMessage[]> {
  const db = getDb();
  const { data, error } = await db
    .from("agent_messages")
    .select("role, content, metadata")
    .eq("session_id", sessionId)
    .order("created_at", { ascending: true })
    .limit(limit);

  if (error) throw error;
  return (data ?? []).map((row) => ({
    role: row.role as AgentMessage["role"],
    content: row.content,
    metadata: (row.metadata ?? {}) as Record<string, unknown>,
  }));
}

export async function saveMessage(
  sessionId: string,
  message: AgentMessage,
): Promise<void> {
  const db = getDb();
  const { error } = await db.from("agent_messages").insert({
    session_id: sessionId,
    role: message.role,
    content: message.content,
    metadata: message.metadata ?? {},
  });
  if (error) throw error;
}

export async function updateSessionState(
  sessionId: string,
  state: Record<string, unknown>,
): Promise<void> {
  const db = getDb();
  const { error } = await db
    .from("agent_sessions")
    .update({ state, updated_at: new Date().toISOString() })
    .eq("id", sessionId);
  if (error) throw error;
}

export async function saveFact(content: string): Promise<MemoryFact> {
  const db = getDb();
  const { data, error } = await db
    .from("agent_facts")
    .insert({ content })
    .select("id, content, created_at")
    .single();
  if (error) throw error;
  return { id: data.id, content: data.content, createdAt: data.created_at };
}

export async function listFacts(query = ""): Promise<MemoryFact[]> {
  const db = getDb();
  let request = db
    .from("agent_facts")
    .select("id, content, created_at")
    .order("created_at", { ascending: false })
    .limit(100);
  if (query.trim()) {
    request = request.ilike("content", `%${query.trim()}%`);
  }
  const { data, error } = await request;
  if (error) throw error;
  return (data ?? []).map((row) => ({
    id: row.id,
    content: row.content,
    createdAt: row.created_at,
  }));
}

export async function saveOrder(
  customerName: string,
  place: string,
  service: string,
): Promise<ServiceOrder> {
  const db = getDb();
  const { data, error } = await db
    .from("agent_orders")
    .insert({ customer_name: customerName, place, service })
    .select("id, customer_name, place, service, created_at")
    .single();
  if (error) throw error;
  return {
    id: data.id,
    customerName: data.customer_name,
    place: data.place,
    service: data.service,
    createdAt: data.created_at,
  };
}
