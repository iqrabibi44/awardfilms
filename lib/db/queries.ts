// lib/db/queries.ts
import { db } from "./client";
import * as schema from "./schema";
import { eq, desc, and, sql, ilike, or } from "drizzle-orm";
import { unstable_cache } from "next/cache";
import { NAV_DATA } from "../data/navigation";

async function getStatsRaw() {
  const [filmsRes, personsRes, nominationsRes, ceremoniesRes] = await Promise.all([
    db.select({ count: sql<string>`COUNT(*)` }).from(schema.films),
    db.select({ count: sql<string>`COUNT(*)` }).from(schema.persons),
    db.select({ count: sql<string>`COUNT(*)` }).from(schema.nominations),
    db.select({ count: sql<string>`COUNT(*)` }).from(schema.ceremonies),
  ]);
  return {
    films:       Number(filmsRes[0].count),
    persons:     Number(personsRes[0].count),
    nominations: Number(nominationsRes[0].count),
    ceremonies:  Number(ceremoniesRes[0].count),
  };
}

export const getStats = unstable_cache(
  getStatsRaw,
  ["get-stats"],
  { revalidate: 86400 }
);


export async function getAllCeremonies() {
  return await db.select().from(schema.ceremonies);
}

export async function getCeremonyBySlug(slug: string) {
  const rows = await db.select().from(schema.ceremonies).where(eq(schema.ceremonies.slug, slug));
  return rows[0] ?? null;
}

export async function getEditionsByCeremonyId(ceremonyId: number) {
  return await db.select().from(schema.editions).where(eq(schema.editions.ceremonyId, ceremonyId)).orderBy(desc(schema.editions.year));
}

export async function getTopFilmsByWins(ceremonyId: number, limit = 5) {
  const rows = await db
    .select({ filmId: schema.films.id, wins: sql<number>`COUNT(*)` })
    .from(schema.nominations)
    .innerJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .where(and(eq(schema.editions.ceremonyId, ceremonyId), eq(schema.nominations.isWinner, true)))
    .groupBy(schema.films.id)
    .orderBy(desc(sql<number>`COUNT(*)`))
    .limit(limit);
  return rows;
}

export async function getTopPersonsByWins(ceremonyId: number, limit = 5) {
  const rows = await db
    .select({ personId: schema.persons.id, wins: sql<number>`COUNT(*)` })
    .from(schema.nominations)
    .innerJoin(schema.persons, eq(schema.nominations.personId, schema.persons.id))
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .where(and(eq(schema.editions.ceremonyId, ceremonyId), eq(schema.nominations.isWinner, true)))
    .groupBy(schema.persons.id)
    .orderBy(desc(sql<number>`COUNT(*)`))
    .limit(limit);
  return rows;
}

export async function getEditionParams() {
  const rows = await db.select({ ceremonySlug: schema.ceremonies.slug, year: schema.editions.year }).from(schema.editions).innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id));
  return rows;
}

export async function getEditionDetails(ceremonySlug: string, year: number) {
  const editionRows = await db
    .select()
    .from(schema.editions)
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .where(and(eq(schema.ceremonies.slug, ceremonySlug), eq(schema.editions.year, year)));
  return editionRows[0] ?? null;
}

export async function getCategoriesWithWinners(editionId: number) {
  const rows = await db
    .select({
      categoryId: schema.categories.id,
      categoryName: schema.categories.name,
      winnerNominee: schema.nominations.nomineeText,
      winnerFilmId: schema.nominations.filmId,
    })
    .from(schema.categories)
    .innerJoin(schema.nominations, and(eq(schema.nominations.categoryId, schema.categories.id), eq(schema.nominations.editionId, editionId), eq(schema.nominations.isWinner, true)));
  return rows;
}

export async function getFilmBySlug(slug: string) {
  const rows = await db.select().from(schema.films).where(eq(schema.films.slug, slug));
  return rows[0] ?? null;
}

export async function getPersonBySlug(slug: string) {
  const rows = await db.select().from(schema.persons).where(eq(schema.persons.slug, slug));
  return rows[0] ?? null;
}

export async function getFilmNominations(filmId: number) {
  const rows = await db
    .select({
      ceremonySlug: schema.ceremonies.slug,
      year: schema.editions.year,
      categoryName: schema.categories.name,
      isWinner: schema.nominations.isWinner,
    })
    .from(schema.nominations)
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
    .where(eq(schema.nominations.filmId, filmId))
    .orderBy(desc(schema.editions.year));
  return rows;
}

export async function getPersonNominations(personId: number) {
  const rows = await db
    .select({
      filmTitle: schema.films.title,
      ceremonySlug: schema.ceremonies.slug,
      year: schema.editions.year,
      categoryName: schema.categories.name,
      isWinner: schema.nominations.isWinner,
    })
    .from(schema.nominations)
    .innerJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
    .where(eq(schema.nominations.personId, personId))
    .orderBy(desc(schema.editions.year));
  return rows;
}

// ─── Extended queries for core pages ────────────────────────────────────────

/** Ceremonies with edition counts for homepage / listing pages */
async function listCeremoniesWithStatsRaw() {
  const rows = await db
    .select({
      id: schema.ceremonies.id,
      slug: schema.ceremonies.slug,
      name: schema.ceremonies.name,
      shortName: schema.ceremonies.shortName,
      country: schema.ceremonies.country,
      foundedYear: schema.ceremonies.foundedYear,
      description: schema.ceremonies.description,
      editionCount: sql<string>`COUNT(DISTINCT ${schema.editions.id})`,
    })
    .from(schema.ceremonies)
    .leftJoin(schema.editions, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .groupBy(schema.ceremonies.id)
    .orderBy(schema.ceremonies.name);
  return rows;
}

export const listCeremoniesWithStats = unstable_cache(
  listCeremoniesWithStatsRaw,
  ["list-ceremonies-with-stats"],
  { revalidate: 86400 }
);

/** All editions for a ceremony, each with its nomination/win counts */
export async function getEditionsWithStats(ceremonyId: number) {
  const rows = await db
    .select({
      id: schema.editions.id,
      year: schema.editions.year,
      editionNumber: schema.editions.editionNumber,
      venue: schema.editions.venue,
      dateHeld: schema.editions.dateHeld,
      nominationCount: sql<string>`COUNT(DISTINCT ${schema.nominations.id})`,
      winnerCount: sql<string>`COUNT(DISTINCT CASE WHEN ${schema.nominations.isWinner} THEN ${schema.nominations.id} END)`,
    })
    .from(schema.editions)
    .leftJoin(schema.nominations, eq(schema.nominations.editionId, schema.editions.id))
    .where(eq(schema.editions.ceremonyId, ceremonyId))
    .groupBy(schema.editions.id)
    .orderBy(desc(schema.editions.year));
  return rows;
}

/** All nominations for an edition, joined with category / film / person */
export async function getEditionNominations(editionId: number) {
  return await db
    .select({
      nominationId: schema.nominations.id,
      nomineeText: schema.nominations.nomineeText,
      isWinner: schema.nominations.isWinner,
      note: schema.nominations.note,
      categoryId: schema.categories.id,
      categoryName: schema.categories.name,
      department: schema.categories.department,
      filmId: schema.films.id,
      filmTitle: schema.films.title,
      filmSlug: schema.films.slug,
      filmPosterUrl: schema.films.posterUrl,
      personId: schema.persons.id,
      personName: schema.persons.name,
      personSlug: schema.persons.slug,
    })
    .from(schema.nominations)
    .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
    .leftJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .leftJoin(schema.persons, eq(schema.nominations.personId, schema.persons.id))
    .where(eq(schema.nominations.editionId, editionId))
    .orderBy(schema.categories.name, desc(schema.nominations.isWinner));
}

/** Film + full nomination list with ceremony/edition context */
export async function getFilmWithNominations(slug: string) {
  const film = await getFilmBySlug(slug);
  if (!film) return null;

  const noms = await db
    .select({
      nominationId: schema.nominations.id,
      isWinner: schema.nominations.isWinner,
      nomineeText: schema.nominations.nomineeText,
      categoryName: schema.categories.name,
      year: schema.editions.year,
      ceremonySlug: schema.ceremonies.slug,
      ceremonyName: schema.ceremonies.name,
    })
    .from(schema.nominations)
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
    .where(eq(schema.nominations.filmId, film.id))
    .orderBy(desc(schema.editions.year), schema.ceremonies.name);

  const wins = noms.filter((n) => n.isWinner).length;
  return { film, nominations: noms, wins, nominationCount: noms.length };
}

/** Person + full nomination list with film/ceremony context */
export async function getPersonWithNominations(slug: string) {
  const person = await getPersonBySlug(slug);
  if (!person) return null;

  const noms = await db
    .select({
      nominationId: schema.nominations.id,
      isWinner: schema.nominations.isWinner,
      nomineeText: schema.nominations.nomineeText,
      categoryName: schema.categories.name,
      year: schema.editions.year,
      ceremonySlug: schema.ceremonies.slug,
      ceremonyName: schema.ceremonies.name,
      filmTitle: schema.films.title,
      filmSlug: schema.films.slug,
    })
    .from(schema.nominations)
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
    .leftJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .where(eq(schema.nominations.personId, person.id))
    .orderBy(desc(schema.editions.year));

  const wins = noms.filter((n) => n.isWinner).length;
  return { person, nominations: noms, wins, nominationCount: noms.length };
}

/** Recent Best Picture / Best Film winners for homepage hero */
async function getRecentWinnersRaw(limit = 8) {
  return await db
    .select({
      filmId: schema.films.id,
      filmTitle: schema.films.title,
      filmSlug: schema.films.slug,
      filmPosterUrl: schema.films.posterUrl,
      filmYear: schema.films.year,
      categoryName: schema.categories.name,
      ceremonyName: schema.ceremonies.name,
      ceremonySlug: schema.ceremonies.slug,
      editionYear: schema.editions.year,
    })
    .from(schema.nominations)
    .innerJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .where(
      and(
        eq(schema.nominations.isWinner, true),
        sql`(${schema.categories.name} ILIKE '%Best Picture%' OR ${schema.categories.name} ILIKE '%Best Film%')`,
        sql`${schema.films.title} != ''`
      )
    )
    .orderBy(desc(schema.editions.year))
    .limit(limit);
}

export const getRecentWinners = unstable_cache(
  async (limit = 8) => getRecentWinnersRaw(limit),
  ["get-recent-winners"],
  { revalidate: 86400 }
);

export async function getBestPictureWinnerForEdition(editionId: number) {
  const row = await db
    .select({ filmTitle: schema.films.title })
    .from(schema.nominations)
    .innerJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
    .where(
      and(
        eq(schema.nominations.editionId, editionId),
        eq(schema.nominations.isWinner, true),
        sql`(${schema.categories.name} ILIKE '%Best Picture%' OR ${schema.categories.name} ILIKE '%Best Film%' OR ${schema.categories.name} ILIKE '%Outstanding British Film%')`
      )
    )
    .limit(1);
  return row[0]?.filmTitle ?? null;
}

export async function searchAll(query: string, limit: number = 5, offset: number = 0, type: 'all' | 'films' | 'persons' = 'all') {
  let filmsRes: { id: number; slug: string; title: string; year: number | null; posterUrl: string | null; }[] = [];
  let personsRes: { id: number; slug: string; name: string; photoUrl: string | null; }[] = [];
  let ceremoniesRes: { id: number; slug: string; name: string; }[] = [];

  const cleanQuery = query.trim();
  if (!cleanQuery) {
    return { films: [], persons: [], ceremonies: [] };
  }

  // 1. Build prefix full-text search query (e.g. "12 fail" -> "12:* & fail:*")
  const rawTokens = cleanQuery.split(/[\s,.\-\/]+/).filter(Boolean);
  if (rawTokens.length === 0) {
    return { films: [], persons: [], ceremonies: [] };
  }

  // Remove common generic words that break exact matching for titles
  const stopwords = new Set(["movie", "movies", "film", "films", "award", "awards", "ceremony", "festival", "show", "cinema"]);
  const meaningfulTokens = rawTokens.filter(t => !stopwords.has(t.toLowerCase()));
  const tokens = meaningfulTokens.length > 0 ? meaningfulTokens : rawTokens;

  const tsQuery = tokens.map(t => `${t}:*`).join(" & ");
  const likePattern = `%${tokens.join(" ")}%`;

  // Fallback token-based ILIKE matches (all tokens must match in title)
  const filmTitleConditions = tokens.map(t => ilike(schema.films.title, `%${t}%`));
  const filmAltTitleConditions = tokens.map(t => ilike(schema.filmAlternateTitles.title, `%${t}%`));
  const personNameConditions = tokens.map(t => ilike(schema.persons.name, `%${t}%`));

  if (type === 'all' || type === 'films') {
    filmsRes = await db
      .select({
        id: schema.films.id,
        slug: schema.films.slug,
        title: schema.films.title,
        year: schema.films.year,
        posterUrl: schema.films.posterUrl,
      })
      .from(schema.films)
      .leftJoin(schema.filmAlternateTitles, eq(schema.films.id, schema.filmAlternateTitles.filmId))
      .where(
        or(
          sql`(search_vector IS NOT NULL AND search_vector @@ to_tsquery('simple', ${tsQuery}))`,
          ilike(schema.films.title, likePattern),
          ilike(schema.filmAlternateTitles.title, likePattern),
          and(...filmTitleConditions),
          and(...filmAltTitleConditions)
        )
      )
      .groupBy(schema.films.id)
      .orderBy(
        desc(sql`
          CASE
            WHEN ${schema.films.title} ILIKE ${cleanQuery} THEN 1000
            WHEN ${schema.films.title} ILIKE ${cleanQuery + '%'} THEN 500
            WHEN ${schema.films.title} ILIKE ${'% ' + cleanQuery + '%'} THEN 100
            WHEN search_vector IS NOT NULL THEN ts_rank(search_vector, to_tsquery('simple', ${tsQuery}))
            ELSE 0
          END
        `)
      )
      .limit(limit)
      .offset(offset);
  }

  if (type === 'all' || type === 'persons') {
    personsRes = await db
      .select({
        id: schema.persons.id,
        slug: schema.persons.slug,
        name: schema.persons.name,
        photoUrl: schema.persons.photoUrl,
      })
      .from(schema.persons)
      .where(
        or(
          sql`(search_vector IS NOT NULL AND search_vector @@ to_tsquery('simple', ${tsQuery}))`,
          ilike(schema.persons.name, likePattern),
          and(...personNameConditions)
        )
      )
      .orderBy(
        desc(sql`
          CASE
            WHEN ${schema.persons.name} ILIKE ${cleanQuery} THEN 1000
            WHEN ${schema.persons.name} ILIKE ${cleanQuery + '%'} THEN 500
            WHEN ${schema.persons.name} ILIKE ${'% ' + cleanQuery + '%'} THEN 100
            WHEN search_vector IS NOT NULL THEN ts_rank(search_vector, to_tsquery('simple', ${tsQuery}))
            ELSE 0
          END
        `)
      )
      .limit(limit)
      .offset(offset);
  }

  if (type === 'all') {
    // Strip year (4-digit number) from the query for ceremonies matching
    const ceremonyWords = tokens.filter(t => !/^(19\d{2}|20[0-2]\d)$/.test(t)).map(t => t.toLowerCase());

    if (ceremonyWords.length > 0) {
      // 1. Search static NAV_DATA (all words must match name or slug)
      const navCeremonies: { id: number; slug: string; name: string; }[] = [];
      let idCounter = 999000;
      for (const cat of NAV_DATA) {
        for (const ind of cat.industries) {
          for (const c of ind.ceremonies) {
            const targetStr = `${c.name} ${c.slug}`.toLowerCase();
            const matchesAll = ceremonyWords.every(word => targetStr.includes(word));
            if (matchesAll) {
              navCeremonies.push({
                id: idCounter++,
                slug: c.slug,
                name: c.name,
              });
            }
          }
        }
      }

      // 2. Search database ceremonies (all words must match via AND/ILIKE conditions)
      const dbQueryConditions = ceremonyWords.map(word => ilike(schema.ceremonies.name, `%${word}%`));
      const dbCeremonies = await db
        .select({ id: schema.ceremonies.id, slug: schema.ceremonies.slug, name: schema.ceremonies.name })
        .from(schema.ceremonies)
        .where(and(...dbQueryConditions))
        .limit(limit)
        .offset(offset);

      // 3. Merge to avoid duplicates
      const seenSlugs = new Set<string>();
      const mergedCeremonies: { id: number; slug: string; name: string; }[] = [];
      for (const c of navCeremonies) {
        if (!seenSlugs.has(c.slug)) {
          seenSlugs.add(c.slug);
          mergedCeremonies.push(c);
        }
      }
      for (const c of dbCeremonies) {
        if (!seenSlugs.has(c.slug)) {
          seenSlugs.add(c.slug);
          mergedCeremonies.push(c);
        }
      }

      ceremoniesRes = mergedCeremonies.slice(0, limit);
    }
  }

  return {
    films: filmsRes,
    persons: personsRes,
    ceremonies: ceremoniesRes,
  };
}


export async function getFilmAlsoWonIn(filmId: number) {
  const rows = await db
    .select({
      ceremonySlug: schema.ceremonies.slug,
      ceremonyName: schema.ceremonies.name,
      ceremonyCountry: schema.ceremonies.country,
      wins: sql<number>`COUNT(*)::int`,
    })
    .from(schema.nominations)
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .where(
      and(
        eq(schema.nominations.filmId, filmId),
        eq(schema.nominations.isWinner, true)
      )
    )
    .groupBy(schema.ceremonies.slug, schema.ceremonies.name, schema.ceremonies.country)
    .orderBy(desc(sql<number>`COUNT(*)::int`));
    
  return rows;
}

export async function getFilmsByDecade(startYear: number, endYear: number, limit: number = 24, offset: number = 0) {
  const rows = await db
    .select({
      filmId: schema.films.id,
      filmSlug: schema.films.slug,
      filmTitle: schema.films.title,
      filmYear: schema.films.year,
      filmPosterUrl: schema.films.posterUrl,
      wins: sql<number>`COUNT(CASE WHEN ${schema.nominations.isWinner} THEN 1 END)::int`,
      noms: sql<number>`COUNT(*)::int`,
    })
    .from(schema.films)
    .innerJoin(schema.nominations, eq(schema.films.id, schema.nominations.filmId))
    .where(
      and(
        sql`${schema.films.year} >= ${startYear}`,
        sql`${schema.films.year} <= ${endYear}`
      )
    )
    .groupBy(schema.films.id)
    .having(sql`COUNT(CASE WHEN ${schema.nominations.isWinner} THEN 1 END) > 0`)
    .orderBy(desc(sql<number>`COUNT(*)`))
    .limit(limit)
    .offset(offset);
  
  return rows;
}

export async function getFilmsByGenre(genre: string, limit: number = 24, offset: number = 0) {
  const rows = await db
    .select({
      filmId: schema.films.id,
      filmSlug: schema.films.slug,
      filmTitle: schema.films.title,
      filmYear: schema.films.year,
      filmPosterUrl: schema.films.posterUrl,
      wins: sql<number>`COUNT(CASE WHEN ${schema.nominations.isWinner} THEN 1 END)::int`,
      noms: sql<number>`COUNT(*)::int`,
    })
    .from(schema.films)
    .innerJoin(schema.nominations, eq(schema.films.id, schema.nominations.filmId))
    .where(ilike(schema.films.genre, `%${genre}%`))
    .groupBy(schema.films.id)
    .having(sql`COUNT(CASE WHEN ${schema.nominations.isWinner} THEN 1 END) > 0`)
    .orderBy(desc(sql<number>`COUNT(*)`))
    .limit(limit)
    .offset(offset);
  return rows;
}

export async function getFilmsByCountry(country: string, limit: number = 24, offset: number = 0) {
  const rows = await db
    .select({
      filmId: schema.films.id,
      filmSlug: schema.films.slug,
      filmTitle: schema.films.title,
      filmYear: schema.films.year,
      filmPosterUrl: schema.films.posterUrl,
      wins: sql<number>`COUNT(CASE WHEN ${schema.nominations.isWinner} THEN 1 END)::int`,
      noms: sql<number>`COUNT(*)::int`,
    })
    .from(schema.films)
    .innerJoin(schema.nominations, eq(schema.films.id, schema.nominations.filmId))
    .where(ilike(schema.films.country, `%${country}%`))
    .groupBy(schema.films.id)
    .having(sql`COUNT(CASE WHEN ${schema.nominations.isWinner} THEN 1 END) > 0`)
    .orderBy(desc(sql<number>`COUNT(*)`))
    .limit(limit)
    .offset(offset);
  return rows;
}

/** Country-level film+win counts — drives the world map coloring */
export async function getCountriesWithFilmCounts() {
  const rows = await db
    .select({
      country: schema.films.country,
      filmCount: sql<number>`COUNT(DISTINCT ${schema.films.id})::int`,
      winCount: sql<number>`COUNT(CASE WHEN ${schema.nominations.isWinner} THEN 1 END)::int`,
    })
    .from(schema.films)
    .innerJoin(schema.nominations, eq(schema.films.id, schema.nominations.filmId))
    .where(sql`${schema.films.country} IS NOT NULL`)
    .groupBy(schema.films.country)
    .orderBy(desc(sql<number>`COUNT(DISTINCT ${schema.films.id})`));
  return rows;
}

/** Streaming availability for a film */
export async function getStreamingLinks(filmId: number) {
  return await db
    .select()
    .from(schema.streamingLinks)
    .where(eq(schema.streamingLinks.filmId, filmId))
    .orderBy(schema.streamingLinks.platformName);
}

/** Paginated all award-winning films for /films listing */
async function listAwardWinningFilmsRaw(limit: number = 24, offset: number = 0) {
  return await db
    .select({
      filmId: schema.films.id,
      filmSlug: schema.films.slug,
      filmTitle: schema.films.title,
      filmYear: schema.films.year,
      filmCountry: schema.films.country,
      filmPosterUrl: schema.films.posterUrl,
      wins: sql<number>`COUNT(CASE WHEN ${schema.nominations.isWinner} THEN 1 END)::int`,
      noms: sql<number>`COUNT(*)::int`,
    })
    .from(schema.films)
    .innerJoin(schema.nominations, eq(schema.films.id, schema.nominations.filmId))
    .groupBy(schema.films.id)
    .having(sql`COUNT(CASE WHEN ${schema.nominations.isWinner} THEN 1 END) > 0`)
    .orderBy(desc(sql<number>`COUNT(CASE WHEN ${schema.nominations.isWinner} THEN 1 END)`))
    .limit(limit)
    .offset(offset);
}

export const listAwardWinningFilms = unstable_cache(
  async (limit: number = 24, offset: number = 0) => listAwardWinningFilmsRaw(limit, offset),
  ["list-award-winning-films"],
  { revalidate: 86400 }
);

/** Paginated all award-winning persons for /persons listing */
async function listAwardWinningPersonsRaw(limit: number = 24, offset: number = 0) {
  return await db
    .select({
      personId: schema.persons.id,
      personSlug: schema.persons.slug,
      personName: schema.persons.name,
      personNationality: schema.persons.nationality,
      personPhotoUrl: schema.persons.photoUrl,
      wins: sql<number>`COUNT(CASE WHEN ${schema.nominations.isWinner} THEN 1 END)::int`,
      noms: sql<number>`COUNT(*)::int`,
    })
    .from(schema.persons)
    .innerJoin(schema.nominations, eq(schema.persons.id, schema.nominations.personId))
    .groupBy(schema.persons.id)
    .having(sql`COUNT(CASE WHEN ${schema.nominations.isWinner} THEN 1 END) > 0`)
    .orderBy(desc(sql<number>`COUNT(CASE WHEN ${schema.nominations.isWinner} THEN 1 END)`))
    .limit(limit)
    .offset(offset);
}

export const listAwardWinningPersons = unstable_cache(
  async (limit: number = 24, offset: number = 0) => listAwardWinningPersonsRaw(limit, offset),
  ["list-award-winning-persons"],
  { revalidate: 86400 }
);

export async function getFilmAlternateTitles(filmId: number) {
  return await db
    .select()
    .from(schema.filmAlternateTitles)
    .where(eq(schema.filmAlternateTitles.filmId, filmId));
}
