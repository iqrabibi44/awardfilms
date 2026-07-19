import * as dotenv from "dotenv";
dotenv.config({ path: ".env.local" });

import { db } from "../lib/db/client";
import { sql } from "drizzle-orm";
import fs from "fs";
import path from "path";

async function runMigration() {
  console.log("Starting Full-Text Search migration...");
  try {
    const sqlFile = path.join(__dirname, "add_search.sql");
    const query = fs.readFileSync(sqlFile, "utf-8");
    
    const queries = query.split(';').map(q => q.trim()).filter(q => q.length > 0);
    
    for (const q of queries) {
      console.log(`Executing: ${q.substring(0, 50)}...`);
      await db.execute(sql.raw(q));
    }
    
    console.log("Migration completed successfully!");
    process.exit(0);
  } catch (err) {
    console.error("Migration failed:", err);
    process.exit(1);
  }
}

runMigration();
