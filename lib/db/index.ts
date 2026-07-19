/**
 * Drizzle ORM database client.
 *
 * This file initialises the Neon serverless driver and exports a
 * ready-to-use Drizzle client. Replace the placeholder logic once
 * DATABASE_URL is configured in .env.local.
 */

import { neon } from "@neondatabase/serverless";
import { drizzle } from "drizzle-orm/neon-http";
import * as schema from "./schema";

const sql = neon(process.env.DATABASE_URL!);

export const db = drizzle({ client: sql, schema });
