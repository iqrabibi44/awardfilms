import { config } from "dotenv";
config({ path: ".env.local" });

import { eq, isNull, or, desc, sql } from "drizzle-orm";

const TMDB_API_KEY = process.env.TMDB_API_KEY;

async function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchTMDBPoster(title: string, year: number | null): Promise<string | null> {
  let url = `https://api.themoviedb.org/3/search/movie?api_key=${TMDB_API_KEY}&query=${encodeURIComponent(title)}`;
  if (year) {
    url += `&primary_release_year=${year}`;
  }

  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const data = await res.json();
    if (data.results && data.results.length > 0) {
      const posterPath = data.results[0].poster_path;
      if (posterPath) return `https://image.tmdb.org/t/p/w500${posterPath}`;
    }
    // Fallback search without year
    if (year && data.results && data.results.length === 0) {
      const fallbackUrl = `https://api.themoviedb.org/3/search/movie?api_key=${TMDB_API_KEY}&query=${encodeURIComponent(title)}`;
      const fallbackRes = await fetch(fallbackUrl);
      const fallbackData = await fallbackRes.json();
      if (fallbackData.results && fallbackData.results.length > 0) {
        const posterPath = fallbackData.results[0].poster_path;
        if (posterPath) return `https://image.tmdb.org/t/p/w500${posterPath}`;
      }
    }
  } catch (error) {}
  return null;
}

async function run() {
  const { db } = await import("../../lib/db");
  const { films } = await import("../../lib/db/schema");

  console.log("Fetching recent 100 films missing posters...");
  const filmsToUpdate = await db
    .select()
    .from(films)
    .where(or(isNull(films.posterUrl), eq(films.posterUrl, "")))
    .orderBy(desc(films.year))
    .limit(100);

  let updatedCount = 0;

  for (const film of filmsToUpdate) {
    console.log(`Searching TMDB for: ${film.title} (${film.year})...`);
    const posterUrl = await fetchTMDBPoster(film.title, film.year);

    if (posterUrl) {
      console.log(`Found: ${posterUrl}`);
      await db.update(films).set({ posterUrl }).where(eq(films.id, film.id));
      updatedCount++;
    }
    await sleep(250);
  }

  console.log(`Updated ${updatedCount} recent films.`);
  process.exit(0);
}

run();
