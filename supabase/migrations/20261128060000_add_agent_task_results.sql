-- Add durable task result/status tracking used by src/agent/memory/dbMemory.ts.
-- Safe to apply after the initial agent memory migration; all changes are idempotent.

ALTER TABLE public.agent_tasks
  ADD COLUMN IF NOT EXISTS tool_result jsonb,
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

-- Keep updated_at current when task state or tool output changes.
CREATE OR REPLACE FUNCTION public.set_agent_task_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS agent_tasks_set_updated_at ON public.agent_tasks;
CREATE TRIGGER agent_tasks_set_updated_at
  BEFORE UPDATE ON public.agent_tasks
  FOR EACH ROW
  EXECUTE FUNCTION public.set_agent_task_updated_at();

CREATE INDEX IF NOT EXISTS idx_agent_tasks_status_updated_at
  ON public.agent_tasks (status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_created_at
  ON public.agent_tasks (created_at DESC);

COMMENT ON TABLE public.agent_tasks IS
  'Agent tasks with lifecycle status and optional JSONB result from the tool execution.';
COMMENT ON COLUMN public.agent_tasks.tool_result IS
  'Optional structured result returned by the tool that processed this task.';
COMMENT ON COLUMN public.agent_tasks.updated_at IS
  'Timestamp of the latest task state or result update.';
