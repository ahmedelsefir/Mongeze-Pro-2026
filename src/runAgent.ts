import "dotenv/config";
import { MongezAgent } from "./agent/index";
import { env } from "./config/env";

async function main(): Promise<void> {
  if (!env.supabaseUrl || !env.supabaseAnonKey) {
    console.error("SUPABASE_URL / SUPABASE_ANON_KEY must be configured.");
    process.exit(1);
  }

  const agent = new MongezAgent();
  const demo = process.argv.slice(2).join(" ") || "ما هي خدماتكم؟";
  const reply = await agent.respond(demo, {
    channel: "smoke-test",
    externalId: "cli",
    isOwner: false,
  });
  console.log("Agent reply:\n" + reply);
  console.log("\nSteps:", agent.getStepLogs().map((l) => l.step).join(" -> "));
}

main().catch((error) => {
  console.error("Agent failed:", error instanceof Error ? error.message : error);
  process.exit(1);
});
