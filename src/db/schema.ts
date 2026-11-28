/*
 * Supabase schema version for the Agent persistence layer.
 * Apply SQL migrations from supabase/migrations in order.
 *
 * agent_sessions: id, channel, external_id, state, created_at, updated_at
 * agent_messages: id, session_id, role, content, metadata, created_at
 * agent_tasks: id, title, status, tool_result, created_at, updated_at
 * agent_facts and agent_orders are retained for existing tools.
 */
export const SCHEMA_VERSION = "2026-11-28-agent-memory-tasks-v2";
