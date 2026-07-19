import { config } from "dotenv";
config({ path: ".env.local" });

import { eq, isNull, or } from "drizzle-orm";

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
    if (!res.ok) {
      console.error(`TMDB API error for ${title}: ${res.statusText}`);
      return null;
    }
    const data = await res.json();
    if (data.results && data.results.length > 0) {
      // Use the first result's poster path
      const posterPath = data.results[0].poster_path;
      if (posterPath) {
        return `https://image.tmdb.org/t/p/w500${posterPath}`;
      }
    }
    // Fallback search without year if year was provided but no results
    if (year && data.results && data.results.length === 0) {
      const fallbackUrl = `https://api.themoviedb.org/3/search/movie?api_key=${TMDB_API_KEY}&query=${encodeURIComponent(title)}`;
      const fallbackRes = await fetch(fallbackUrl);
      const fallbackData = await fallbackRes.json();
      if (fallbackData.results && fallbackData.results.length > 0) {
        const posterPath = fallbackData.results[0].poster_path;
        if (posterPath) {
          return `https://image.tmdb.org/t/p/w500${posterPath}`;
        }
      }
    }
  } catch (error) {
    console.error(`Fetch failed for ${title}:`, error);
  }
  return null;
}

async function run() {
  if (!TMDB_API_KEY) {
    console.error("Missing TMDB_API_KEY in .env.local");
    process.exit(1);
  }

  console.log("Fetching films missing posters from DB...");
  const { db } = await import("../../lib/db");
  const { films } = await import("../../lib/db/schema");

  const filmsToUpdate = await db
    .select()
    .from(films)
    .where(or(isNull(films.posterUrl), eq(films.posterUrl, "")));

  console.log(`Found ${filmsToUpdate.length} films missing posters.`);

  let updatedCount = 0;

  for (const film of filmsToUpdate) {
    console.log(`Searching TMDB for: ${film.title} (${film.year || 'N/A'})...`);
    const posterUrl = await fetchTMDBPoster(film.title, film.year);

    if (posterUrl) {
      console.log(`Found poster: ${posterUrl}`);
      await db
        .update(films)
        .set({ posterUrl })
        .where(eq(films.id, film.id));
      updatedCount++;
    } else {
      console.log(`No poster found for ${film.title}.`);
    }

    // Rate limiting (TMDB allows 40 requests per 10 seconds, ~4 req/s)
    await sleep(250);
  }

  console.log(`\nFinished! Updated ${updatedCount} out of ${filmsToUpdate.length} films.`);
  process.exit(0);
}

run();
