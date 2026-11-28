import "dotenv/config";

function requiredWithFallback(
  preferredName: string,
  fallbackName: string,
): string {
  const value = process.env[preferredName]?.trim() || process.env[fallbackName]?.trim();
  if (!value) {
    throw new Error(
      `Missing required environment variable: set ${preferredName} (preferred) or ${fallbackName}.`,
    );
  }
  return value;
}

function optional(name: string, fallback = ""): string {
  const value = process.env[name];
  return value ? value.trim() : fallback;
}

export const env = {
  supabaseUrl: requiredWithFallback("EXTERNAL_SUPABASE_URL", "SUPABASE_URL"),
  supabaseAnonKey: requiredWithFallback(
    "EXTERNAL_SUPABASE_ANON_KEY",
    "SUPABASE_ANON_KEY",
  ),
  telegramToken: optional("TELEGRAM_TOKEN"),
  ownerTelegramIds: optional("OWNER_TELEGRAM_IDS")
    .split(",")
    .map((id) => id.trim())
    .filter(Boolean),
  legacyOwnerUsernames: ["ahmedelsefir", "ahmedmostafa"],
};

export type Env = typeof env;
