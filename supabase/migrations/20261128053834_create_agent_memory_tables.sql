/*
# Create agent memory tables for the Mongez AI agent

1. Plain-English explanation
The TypeScript agent (`src/agent/`) needs a durable place to store conversation
context, saved facts ("memory"), tasks, service orders, and per-session message
history. This migration creates those tables in Supabase so the agent can read
and update its state after every step.

2. New Tables
- `agent_sessions`: one row per conversation/channel the agent talks to.
  - `id` (uuid, primary key)
  - `channel` (text): where the session happens, e.g. "telegram" or "api"
  - `external_id` (text): the chat/channel identifier from that platform
  - `state` (jsonb): free-form agent state (last intent, owner flag, counters)
  - `created_at`, `updated_at` (timestamps)
- `agent_messages`: full message history per session (user + agent turns).
  - `id` (uuid, primary key)
  - `session_id` (uuid, foreign key -> agent_sessions, cascade delete)
  - `role` (text): "user" or "agent"
  - `content` (text): message text
  - `metadata` (jsonb): optional extras (intent, confidence, tool used)
  - `created_at` (timestamp)
- `agent_facts`: saved personal facts ("remember that ...").
  - `id`, `content` (text), `metadata` (jsonb), `created_at`
- `agent_tasks`: organized tasks.
  - `id`, `title` (text), `status` (text, default "open"), `created_at`
- `agent_orders`: service inquiries captured by the order tool.
  - `id`, `customer_name`, `place`, `service` (text), `created_at`

3. Indexes
- Unique index on `(channel, external_id)` so sessions are idempotent.
- Index on `agent_messages.session_id` for fast history loading.

4. Security
- RLS enabled on all five tables. This agent is single-tenant (no sign-in):
  the anon-key runtime is the agent itself, so policies target
  `anon, authenticated` with `USING (true)` / `WITH CHECK (true)`.
- CRUD grants given to `anon` and `authenticated` only (minimum verbs used).
- `service_role` is granted access for any future server-side (edge function) use.
*/

CREATE TABLE IF NOT EXISTS agent_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  channel text NOT NULL DEFAULT 'api',
  external_id text NOT NULL,
  state jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (channel, external_id)
);

CREATE TABLE IF NOT EXISTS agent_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES agent_sessions(id) ON DELETE CASCADE,
  role text NOT NULL CHECK (role IN ('user', 'agent')),
  content text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_messages_session ON agent_messages (session_id, created_at);

CREATE TABLE IF NOT EXISTS agent_facts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  status text NOT NULL DEFAULT 'open',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_orders (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_name text NOT NULL,
  place text NOT NULL,
  service text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE agent_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_orders ENABLE ROW LEVEL SECURITY;

GRANT SELECT, INSERT, UPDATE ON agent_sessions TO anon, authenticated;
GRANT SELECT, INSERT ON agent_messages TO anon, authenticated;
GRANT SELECT, INSERT ON agent_facts TO anon, authenticated;
GRANT SELECT ON agent_tasks TO anon, authenticated;
GRANT INSERT ON agent_tasks TO anon, authenticated;
GRANT SELECT, INSERT ON agent_orders TO anon, authenticated;

GRANT SELECT, INSERT, UPDATE, DELETE ON agent_sessions, agent_messages, agent_facts, agent_tasks, agent_orders TO service_role;

-- Single-tenant agent runtime: the anon-key process IS the agent, so full
-- read/write access for it is intentional. No sign-in flow exists in this app.
DROP POLICY IF EXISTS "agent_sessions_select" ON agent_sessions;
CREATE POLICY "agent_sessions_select" ON agent_sessions FOR SELECT
TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "agent_sessions_insert" ON agent_sessions;
CREATE POLICY "agent_sessions_insert" ON agent_sessions FOR INSERT
TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "agent_sessions_update" ON agent_sessions;
CREATE POLICY "agent_sessions_update" ON agent_sessions FOR UPDATE
TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "agent_messages_select" ON agent_messages;
CREATE POLICY "agent_messages_select" ON agent_messages FOR SELECT
TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "agent_messages_insert" ON agent_messages;
CREATE POLICY "agent_messages_insert" ON agent_messages FOR INSERT
TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "agent_facts_select" ON agent_facts;
CREATE POLICY "agent_facts_select" ON agent_facts FOR SELECT
TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "agent_facts_insert" ON agent_facts;
CREATE POLICY "agent_facts_insert" ON agent_facts FOR INSERT
TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "agent_tasks_select" ON agent_tasks;
CREATE POLICY "agent_tasks_select" ON agent_tasks FOR SELECT
TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "agent_tasks_insert" ON agent_tasks;
CREATE POLICY "agent_tasks_insert" ON agent_tasks FOR INSERT
TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "agent_orders_select" ON agent_orders;
CREATE POLICY "agent_orders_select" ON agent_orders FOR SELECT
TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "agent_orders_insert" ON agent_orders;
CREATE POLICY "agent_orders_insert" ON agent_orders FOR INSERT
TO anon, authenticated WITH CHECK (true);
