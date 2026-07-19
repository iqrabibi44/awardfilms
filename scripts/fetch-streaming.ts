/**
 * scripts/fetch-streaming.ts
 *
 * Fetches streaming availability from TMDB Watch Providers API and stores
 * it in the streaming_links table. Runs against films that have a tmdbId.
 *
 * Usage:
 *   TMDB_API_KEY=your_key npx tsx scripts/fetch-streaming.ts
 *   npx tsx scripts/fetch-streaming.ts --limit=50
 *
 * Supported regions: US, GB, IN, PK, AU, CA, FR, DE, JP, KR (add more as needed)
 */

import * as dotenv from "dotenv";
dotenv.config({ path: ".env.local" });

import { db } from "../lib/db/client";
import { films, streamingLinks } from "../lib/db/schema";
import { isNotNull, sql } from "drizzle-orm";

const TMDB_API_KEY = process.env.TMDB_API_KEY;
const TMDB_BASE = "https://api.themoviedb.org/3";

// TMDB provider IDs → our platform slugs + names
const PROVIDER_MAP: Record<number, { slug: string; name: string }> = {
  8:   { slug: "netflix",      name: "Netflix" },
  9:   { slug: "prime",        name: "Amazon Prime Video" },
  337: { slug: "disney-plus",  name: "Disney+" },
  15:  { slug: "hulu",         name: "Hulu" },
  384: { slug: "hbo-max",      name: "Max" },
  2:   { slug: "apple-tv",     name: "Apple TV+" },
  531: { slug: "paramount",    name: "Paramount+" },
  386: { slug: "peacock",      name: "Peacock" },
  283: { slug: "crunchyroll",  name: "Crunchyroll" },
  // Regional
  209: { slug: "zee5",         name: "ZEE5" },
  122: { slug: "hotstar",      name: "Disney+ Hotstar" },
  220: { slug: "sony-liv",     name: "SonyLIV" },
  315: { slug: "ary-zap",      name: "ARY ZAP" },
};

const REGIONS = ["US", "GB", "IN", "PK", "AU", "CA", "FR", "DE", "JP", "KR"];

async function sleep(ms: number) {
  return new Promise((res) => setTimeout(res, ms));
}

async function fetchWatchProviders(tmdbId: number): Promise<
  Array<{ platformSlug: string; platformName: string; url: string; region: string }>
> {
  const url = `${TMDB_BASE}/movie/${tmdbId}/watch/providers?api_key=${TMDB_API_KEY}`;
  const res = await fetch(url);
  if (!res.ok) return [];
  const json = await res.json() as any;

  const results: Array<{ platformSlug: string; platformName: string; url: string; region: string }> = [];

  for (const region of REGIONS) {
    const regionData = json.results?.[region];
    if (!regionData) continue;

    const tmdbLink = regionData.link ?? `https://www.themoviedb.org/movie/${tmdbId}/watch`;

    // Flatrate = subscription streaming (Netflix, Prime, etc.)
    const providers = [
      ...(regionData.flatrate ?? []),
      ...(regionData.free ?? []),
    ];

    for (const provider of providers) {
      const mapped = PROVIDER_MAP[provider.provider_id as number];
      if (!mapped) continue;
      results.push({
        platformSlug: mapped.slug,
        platformName: mapped.name,
        url: tmdbLink,
        region: region.toLowerCase(),
      });
    }
  }

  return results;
}

async function main() {
  if (!TMDB_API_KEY) {
    console.error("❌ TMDB_API_KEY not set in .env.local");
    console.error("   Add: TMDB_API_KEY=your_tmdb_api_key_here");
    process.exit(1);
  }

  const args = process.argv.slice(2);
  const limitArg = args.find((a) => a.startsWith("--limit="));
  const limitN = limitArg ? parseInt(limitArg.split("=")[1], 10) : 200;

  console.log(`🎬 Fetching streaming links for up to ${limitN} films from TMDB...`);

  // Get films with tmdbId that haven't been fetched recently
  const filmsToFetch = await db
    .select({ id: films.id, title: films.title, tmdbId: films.tmdbId })
    .from(films)
    .where(isNotNull(films.tmdbId))
    .limit(limitN);

  console.log(`📋 Found ${filmsToFetch.length} films with TMDB IDs`);

  let processed = 0;
  let inserted = 0;

  for (const film of filmsToFetch) {
    if (!film.tmdbId) continue;

    try {
      const providers = await fetchWatchProviders(film.tmdbId);
      
      if (providers.length > 0) {
        // Upsert streaming links
        for (const p of providers) {
          await db
            .insert(streamingLinks)
            .values({
              filmId: film.id,
              platformName: p.platformName,
              platformSlug: p.platformSlug,
              url: p.url,
              region: p.region,
            })
            .onConflictDoUpdate({
              target: [streamingLinks.filmId, streamingLinks.platformSlug, streamingLinks.region],
              set: { url: p.url, updatedAt: sql`NOW()` },
            });
          inserted++;
        }
        console.log(`  ✅ ${film.title} — ${providers.length} streaming links`);
      }

      processed++;
      // Rate limit: TMDB allows ~40 req/10s
      await sleep(280);
    } catch (err) {
      console.error(`  ❌ Failed for ${film.title}:`, err);
    }
  }

  console.log(`\n✨ Done! Processed ${processed} films, inserted/updated ${inserted} streaming links.`);
  process.exit(0);
}

main();
