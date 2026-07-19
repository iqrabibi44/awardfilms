// lib/db/client.ts
// Re-export the Neon HTTP Drizzle client from index.ts so that
// any file importing from "@/lib/db/client" continues to work.
export { db } from "./index";
