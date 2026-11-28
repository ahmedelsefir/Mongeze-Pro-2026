export type MessageRole = "user" | "agent";

export interface AgentMessage {
  role: MessageRole;
  content: string;
  metadata?: Record<string, unknown>;
}

export interface AgentSession {
  id: string;
  channel: string;
  externalId: string;
  state: Record<string, unknown>;
}

export interface MemoryFact {
  id: string;
  content: string;
  createdAt: string;
}

export interface AgentTask {
  id: string;
  title: string;
  status: string;
  createdAt: string;
}

export interface ServiceOrder {
  id: string;
  customerName: string;
  place: string;
  service: string;
  createdAt: string;
}

export type ToolName =
  | "get_services"
  | "create_order"
  | "organize_task"
  | "remember"
  | "search_memory"
  | "explain_code"
  | "fix_code";

export interface ToolDefinition {
  name: ToolName;
  description: string;
  run: (input: string) => Promise<string> | string;
}

export interface AgentStepLog {
  step: "perceive" | "reason" | "act" | "persist";
  detail: string;
  at: string;
}
