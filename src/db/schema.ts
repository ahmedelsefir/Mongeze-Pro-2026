/*
Schema for the Mongez agent memory, mirroring the applied Supabase migration
`create_agent_memory_tables`. Kept in code so new environments can be provisioned
from source.

Tables:
- agent_sessions: (id uuid pk, channel text, external_id text, state jsonb,
  created_at, updated_at) with UNIQUE (channel, external_id)
- agent_messages: (id uuid pk, session_id -> agent_sessions ON DELETE CASCADE,
  role text in ('user','agent'), content text, metadata jsonb, created_at)
  indexed on (session_id, created_at)
- agent_facts: (id uuid pk, content text, metadata jsonb, created_at)
- agent_tasks: (id uuid pk, title text, status text default 'open', created_at)
- agent_orders: (id uuid pk, customer_name text, place text, service text,
  created_at)

All tables have RLS enabled; the anon-key runtime acts as the agent itself,
so policies allow the anon role full CRUD per the migration comments.
*/
export const SCHEMA_VERSION = "2026-11-28-create_agent_memory_tables";
