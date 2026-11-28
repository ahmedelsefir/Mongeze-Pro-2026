import "dotenv/config";

function required(name: string, value: string | undefined): string {
  if (!value || !value.trim()) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value.trim();
}

function optional(name: string, fallback = ""): string {
  const value = process.env[name];
  return value ? value.trim() : fallback;
}

export const env = {
  supabaseUrl: required("SUPABASE_URL", process.env.SUPABASE_URL),
  supabaseAnonKey: required("SUPABASE_ANON_KEY", process.env.SUPABASE_ANON_KEY),
  telegramToken: optional("TELEGRAM_TOKEN"),
  ownerTelegramIds: optional("OWNER_TELEGRAM_IDS")
    .split(",")
    .map((id) => id.trim())
    .filter(Boolean),
  legacyOwnerUsernames: ["ahmedelsefir", "ahmedmostafa"],
};

export type Env = typeof env;
