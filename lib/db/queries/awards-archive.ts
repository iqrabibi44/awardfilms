import { db } from "../client";
import * as schema from "../schema";
import { eq, desc, and, sql, or, ilike } from "drizzle-orm";
import { unstable_cache } from "next/cache";
import { NAV_DATA } from "../../data/navigation";

export interface CeremonyEditionHighlight {
  category_name: string;
  film_title: string;
  person_name: string;
  is_winner: boolean;
}

export interface CeremonyEdition {
  id: number;
  year: number;
  edition_number: number | null;
  date_held: string | null;
  venue: string | null;
  host: string | null;
  broadcast_network: string | null;
  slug: string | null;
  total_categories: number;
  total_nominations: number;
  total_winners: number;
  highlight_winners: CeremonyEditionHighlight[];
}

export interface CeremonyWithAllEditions {
  ceremony: {
    id: number;
    name: string;
    slug: string;
    country: string | null;
    founded_year: number | null;
    frequency: string | null;
    description: string | null;
    website_url: string | null;
  };
  editions: CeremonyEdition[];
  stats: {
    total_editions: number;
    total_films_honoured: number;
    total_persons_honoured: number;
    most_decorated_film: { title: string; year: number; win_count: number } | null;
    most_decorated_person: { name: string; win_count: number } | null;
  };
}

async function getCeremonyWithAllEditionsRaw(ceremonySlugInput: string): Promise<CeremonyWithAllEditions | null> {
  const ceremonySlug = ceremonySlugInput === "producers-guild-film-awards" ? "producers-guild" : ceremonySlugInput;
  // 1. Get ceremony info
  const ceremonyRows = await db
    .select()
    .from(schema.ceremonies)
    .where(eq(schema.ceremonies.slug, ceremonySlug))
    .limit(1);

  let ceremony: {
    id: number;
    name: string;
    slug: string;
    country: string | null;
    foundedYear: number | null;
    frequency: string | null;
    description: string | null;
    websiteUrl: string | null;
  };
  let noEditionsFallback = false;

  if (ceremonyRows.length === 0) {
    // Look up in NAV_DATA
    let foundInNav = null;
    for (const cat of NAV_DATA) {
      for (const ind of cat.industries) {
        const match = ind.ceremonies.find((c) => c.slug === ceremonySlug);
        if (match) {
          foundInNav = match;
          break;
        }
      }
      if (foundInNav) break;
    }

    if (!foundInNav) return null;

    ceremony = {
      id: 999000,
      name: foundInNav.name,
      slug: foundInNav.slug,
      country: foundInNav.country,
      foundedYear: foundInNav.founded,
      frequency: "Annual",
      description: null,
      websiteUrl: null,
    };
    noEditionsFallback = true;
  } else {
    ceremony = ceremonyRows[0];
  }

  // 2. Get all editions for this ceremony
  const editionsRows = noEditionsFallback ? [] : await db
    .select()
    .from(schema.editions)
    .where(eq(schema.editions.ceremonyId, ceremony.id))
    .orderBy(desc(schema.editions.year));

  if (editionsRows.length === 0) {
    return {
      ceremony: {
        id: ceremony.id,
        name: ceremony.name,
        slug: ceremony.slug,
        country: ceremony.country,
        founded_year: ceremony.foundedYear,
        frequency: ceremony.frequency,
        description: ceremony.description,
        website_url: ceremony.websiteUrl,
      },
      editions: [],
      stats: {
        total_editions: 0,
        total_films_honoured: 0,
        total_persons_honoured: 0,
        most_decorated_film: null,
        most_decorated_person: null,
      },
    };
  }

  const editionIds = editionsRows.map((e) => e.id);

  // 3. Get total categories, nominations, and winners per edition in a single grouped query
  const countsPerEdition = await db
    .select({
      editionId: schema.nominations.editionId,
      total_categories: sql<number>`COUNT(DISTINCT ${schema.nominations.categoryId})::int`,
      total_nominations: sql<number>`COUNT(${schema.nominations.id})::int`,
      total_winners: sql<number>`COUNT(CASE WHEN ${schema.nominations.isWinner} = true THEN 1 END)::int`,
    })
    .from(schema.nominations)
    .where(sql`${schema.nominations.editionId} IN (${sql.raw(editionIds.join(","))})`)
    .groupBy(schema.nominations.editionId);

  const countsMap = new Map(countsPerEdition.map((c) => [c.editionId, c]));

  // 4. Get highlight winners (top 3 winners) for preview per edition
  const allWinners = await db
    .select({
      editionId: schema.nominations.editionId,
      category_name: schema.categories.name,
      film_title: schema.films.title,
      person_name: schema.persons.name,
      is_winner: schema.nominations.isWinner,
    })
    .from(schema.nominations)
    .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
    .leftJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .leftJoin(schema.persons, eq(schema.nominations.personId, schema.persons.id))
    .where(
      and(
        sql`${schema.nominations.editionId} IN (${sql.raw(editionIds.join(","))})`,
        eq(schema.nominations.isWinner, true)
      )
    )
    .orderBy(schema.nominations.editionId, schema.categories.department, schema.categories.name);

  // Group winners by editionId, take first 3
  const winnersMap = new Map<number, CeremonyEditionHighlight[]>();
  for (const win of allWinners) {
    if (!win.editionId) continue;
    const current = winnersMap.get(win.editionId) || [];
    if (current.length < 3) {
      current.push({
        category_name: win.category_name,
        film_title: win.film_title || "",
        person_name: win.person_name || win.category_name, // Fallback if no person name
        is_winner: win.is_winner || false,
      });
      winnersMap.set(win.editionId, current);
    }
  }

  // 5. Map editions list
  const editions: CeremonyEdition[] = editionsRows.map((e) => {
    const counts = countsMap.get(e.id);
    return {
      id: e.id,
      year: e.year,
      edition_number: e.editionNumber,
      date_held: e.dateHeld,
      venue: e.venue,
      host: e.host,
      broadcast_network: e.broadcastNetwork,
      slug: e.slug,
      total_categories: counts?.total_categories || 0,
      total_nominations: counts?.total_nominations || 0,
      total_winners: counts?.total_winners || 0,
      highlight_winners: winnersMap.get(e.id) || [],
    };
  });

  // 6. Global stats calculations
  // total films honoured
  const filmsHonouredRes = await db
    .select({ count: sql<number>`COUNT(DISTINCT ${schema.nominations.filmId})::int` })
    .from(schema.nominations)
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .where(
      and(
        eq(schema.editions.ceremonyId, ceremony.id),
        eq(schema.nominations.isWinner, true),
        sql`${schema.nominations.filmId} IS NOT NULL`
      )
    );

  // total persons honoured
  const personsHonouredRes = await db
    .select({ count: sql<number>`COUNT(DISTINCT ${schema.nominations.personId})::int` })
    .from(schema.nominations)
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .where(
      and(
        eq(schema.editions.ceremonyId, ceremony.id),
        eq(schema.nominations.isWinner, true),
        sql`${schema.nominations.personId} IS NOT NULL`
      )
    );

  // most decorated film (wins in a single edition)
  const mostDecoratedFilmRes = await db
    .select({
      title: schema.films.title,
      year: schema.editions.year,
      win_count: sql<number>`COUNT(*)::int`,
    })
    .from(schema.nominations)
    .innerJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .where(
      and(
        eq(schema.editions.ceremonyId, ceremony.id),
        eq(schema.nominations.isWinner, true)
      )
    )
    .groupBy(schema.films.id, schema.films.title, schema.editions.id, schema.editions.year)
    .orderBy(desc(sql`COUNT(*)`))
    .limit(1);

  // most decorated person (total wins across all editions)
  const mostDecoratedPersonRes = await db
    .select({
      name: schema.persons.name,
      win_count: sql<number>`COUNT(*)::int`,
    })
    .from(schema.nominations)
    .innerJoin(schema.persons, eq(schema.nominations.personId, schema.persons.id))
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .where(
      and(
        eq(schema.editions.ceremonyId, ceremony.id),
        eq(schema.nominations.isWinner, true)
      )
    )
    .groupBy(schema.persons.id, schema.persons.name)
    .orderBy(desc(sql`COUNT(*)`))
    .limit(1);

  return {
    ceremony: {
      id: ceremony.id,
      name: ceremony.name,
      slug: ceremony.slug,
      country: ceremony.country,
      founded_year: ceremony.foundedYear,
      frequency: ceremony.frequency,
      description: ceremony.description,
      website_url: ceremony.websiteUrl,
    },
    editions,
    stats: {
      total_editions: editions.length,
      total_films_honoured: filmsHonouredRes[0]?.count || 0,
      total_persons_honoured: personsHonouredRes[0]?.count || 0,
      most_decorated_film: mostDecoratedFilmRes[0] || null,
      most_decorated_person: mostDecoratedPersonRes[0] || null,
    },
  };
}

export const getCeremonyWithAllEditions = unstable_cache(
  async (ceremonySlug: string) => getCeremonyWithAllEditionsRaw(ceremonySlug),
  ["get-ceremony-with-all-editions"],
  { revalidate: 86400 }
);

export interface Nomination {
  id: number;
  nominee_text: string;
  note: string | null;
  is_winner: boolean;
  film: {
    title: string;
    slug: string;
    year: number | null;
    poster_url: string | null;
    genre: string | null;
  } | null;
  person: {
    name: string;
    slug: string;
    photo_url: string | null;
    nationality: string | null;
  } | null;
}

export interface CategoryWithNominations {
  id: number;
  name: string;
  slug: string;
  department: string;
  nominations: Nomination[];
}

export interface EditionWithAllCategories {
  ceremony: {
    name: string;
    slug: string;
    country: string | null;
  };
  edition: {
    id: number;
    year: number;
    edition_number: number | null;
    date_held: string | null;
    venue: string | null;
    host: string | null;
    broadcast_network: string | null;
  };
  categories: CategoryWithNominations[];
  summary: {
    total_categories: number;
    total_nominations: number;
    total_winners: number;
  };
}

async function getEditionWithAllCategoriesRaw(
  ceremonySlugInput: string,
  year: number
): Promise<EditionWithAllCategories | null> {
  const ceremonySlug = ceremonySlugInput === "producers-guild-film-awards" ? "producers-guild" : ceremonySlugInput;
  // 1. Get ceremony & edition details
  const editionRows = await db
    .select({
      ceremonyId: schema.ceremonies.id,
      ceremonyName: schema.ceremonies.name,
      ceremonySlug: schema.ceremonies.slug,
      ceremonyCountry: schema.ceremonies.country,
      editionId: schema.editions.id,
      year: schema.editions.year,
      editionNumber: schema.editions.editionNumber,
      dateHeld: schema.editions.dateHeld,
      venue: schema.editions.venue,
      host: schema.editions.host,
      broadcastNetwork: schema.editions.broadcastNetwork,
    })
    .from(schema.editions)
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .where(
      and(
        eq(schema.ceremonies.slug, ceremonySlug),
        eq(schema.editions.year, year)
      )
    )
    .limit(1);

  if (editionRows.length === 0) return null;
  const ed = editionRows[0];

  // 2. Get all nominations for this edition
  const noms = await db
    .select({
      nominationId: schema.nominations.id,
      nomineeText: schema.nominations.nomineeText,
      note: schema.nominations.note,
      isWinner: schema.nominations.isWinner,
      categoryId: schema.categories.id,
      categoryName: schema.categories.name,
      categorySlug: schema.categories.slug,
      categoryDepartment: schema.categories.department,
      filmId: schema.films.id,
      filmTitle: schema.films.title,
      filmSlug: schema.films.slug,
      filmYear: schema.films.year,
      filmPosterUrl: schema.films.posterUrl,
      filmGenre: schema.films.genre,
      personId: schema.persons.id,
      personName: schema.persons.name,
      personSlug: schema.persons.slug,
      personPhotoUrl: schema.persons.photoUrl,
      personNationality: schema.persons.nationality,
    })
    .from(schema.nominations)
    .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
    .leftJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .leftJoin(schema.persons, eq(schema.nominations.personId, schema.persons.id))
    .where(eq(schema.nominations.editionId, ed.editionId))
    .orderBy(
      schema.categories.department,
      schema.categories.name,
      desc(schema.nominations.isWinner)
    );

  // Group by category
  const categoriesMap = new Map<number, CategoryWithNominations>();

  for (const r of noms) {
    if (!categoriesMap.has(r.categoryId)) {
      categoriesMap.set(r.categoryId, {
        id: r.categoryId,
        name: r.categoryName,
        slug: r.categorySlug,
        department: r.categoryDepartment || "General",
        nominations: [],
      });
    }

    categoriesMap.get(r.categoryId)!.nominations.push({
      id: r.nominationId,
      nominee_text: r.nomineeText,
      note: r.note,
      is_winner: r.isWinner || false,
      film: r.filmId
        ? {
            title: r.filmTitle || "",
            slug: r.filmSlug || "",
            year: r.filmYear,
            poster_url: r.filmPosterUrl,
            genre: r.filmGenre,
          }
        : null,
      person: r.personId
        ? {
            name: r.personName || "",
            slug: r.personSlug || "",
            photo_url: r.personPhotoUrl,
            nationality: r.personNationality,
          }
        : null,
    });
  }

  const categories = Array.from(categoriesMap.values()).sort((a, b) => {
    const depA = a.department.toLowerCase();
    const depB = b.department.toLowerCase();
    if (depA !== depB) return depA.localeCompare(depB);
    return a.name.localeCompare(b.name);
  });

  return {
    ceremony: {
      name: ed.ceremonyName,
      slug: ed.ceremonySlug,
      country: ed.ceremonyCountry,
    },
    edition: {
      id: ed.editionId,
      year: ed.year,
      edition_number: ed.editionNumber,
      date_held: ed.dateHeld,
      venue: ed.venue,
      host: ed.host,
      broadcast_network: ed.broadcastNetwork,
    },
    categories,
    summary: {
      total_categories: categories.length,
      total_nominations: noms.length,
      total_winners: noms.filter((n) => n.isWinner).length,
    },
  };
}

export const getEditionWithAllCategories = unstable_cache(
  async (ceremonySlug: string, year: number) => getEditionWithAllCategoriesRaw(ceremonySlug, year),
  ["get-edition-with-all-categories"],
  { revalidate: 86400 }
);

export interface CategoryWinner {
  year: number;
  edition_number: number | null;
  film: {
    title: string;
    slug: string;
    poster_url: string | null;
  } | null;
  person: {
    name: string;
    slug: string;
    photo_url: string | null;
  } | null;
  nominee_text: string;
}

export interface CategoryAllWinners {
  ceremony: {
    name: string;
    slug: string;
  };
  category: {
    name: string;
    slug: string;
    department: string;
  };
  winners: CategoryWinner[];
}

async function getCategoryAllWinnersRaw(
  ceremonySlugInput: string,
  categorySlug: string
): Promise<CategoryAllWinners | null> {
  const ceremonySlug = ceremonySlugInput === "producers-guild-film-awards" ? "producers-guild" : ceremonySlugInput;
  // 1. Get ceremony
  const ceremonyRows = await db
    .select()
    .from(schema.ceremonies)
    .where(eq(schema.ceremonies.slug, ceremonySlug))
    .limit(1);

  if (ceremonyRows.length === 0) return null;
  const ceremony = ceremonyRows[0];

  // 2. Get category
  const categoryRows = await db
    .select()
    .from(schema.categories)
    .where(
      and(
        eq(schema.categories.ceremonyId, ceremony.id),
        eq(schema.categories.slug, categorySlug)
      )
    )
    .limit(1);

  if (categoryRows.length === 0) return null;
  const category = categoryRows[0];

  // 3. Get all winners
  const winnersRows = await db
    .select({
      year: schema.editions.year,
      edition_number: schema.editions.editionNumber,
      filmId: schema.films.id,
      filmTitle: schema.films.title,
      filmSlug: schema.films.slug,
      filmPosterUrl: schema.films.posterUrl,
      personId: schema.persons.id,
      personName: schema.persons.name,
      personSlug: schema.persons.slug,
      personPhotoUrl: schema.persons.photoUrl,
      nomineeText: schema.nominations.nomineeText,
    })
    .from(schema.nominations)
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .leftJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .leftJoin(schema.persons, eq(schema.nominations.personId, schema.persons.id))
    .where(
      and(
        eq(schema.nominations.categoryId, category.id),
        eq(schema.nominations.isWinner, true)
      )
    )
    .orderBy(desc(schema.editions.year));

  const winners: CategoryWinner[] = winnersRows.map((w) => ({
    year: w.year,
    edition_number: w.edition_number,
    film: w.filmId
      ? {
          title: w.filmTitle || "",
          slug: w.filmSlug || "",
          poster_url: w.filmPosterUrl,
        }
      : null,
    person: w.personId
      ? {
          name: w.personName || "",
          slug: w.personSlug || "",
          photo_url: w.personPhotoUrl,
        }
      : null,
    nominee_text: w.nomineeText,
  }));

  return {
    ceremony: {
      name: ceremony.name,
      slug: ceremony.slug,
    },
    category: {
      name: category.name,
      slug: category.slug,
      department: category.department || "General",
    },
    winners,
  };
}

export const getCategoryAllWinners = unstable_cache(
  async (ceremonySlug: string, categorySlug: string) => getCategoryAllWinnersRaw(ceremonySlug, categorySlug),
  ["get-category-all-winners"],
  { revalidate: 86400 }
);

export interface PreviewWinner {
  category_name: string;
  winner_text: string;
  film_title: string | null;
  person_name: string | null;
}

export interface EditionYearPreview {
  year: number;
  venue: string | null;
  host: string | null;
  top_winners: PreviewWinner[];
  total_categories: number;
  total_winners: number;
}

async function getEditionYearPreviewRaw(
  ceremonySlugInput: string,
  year: number
): Promise<EditionYearPreview | null> {
  const ceremonySlug = ceremonySlugInput === "producers-guild-film-awards" ? "producers-guild" : ceremonySlugInput;
  const editionRows = await db
    .select({
      editionId: schema.editions.id,
      year: schema.editions.year,
      venue: schema.editions.venue,
      host: schema.editions.host,
    })
    .from(schema.editions)
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .where(
      and(
        eq(schema.ceremonies.slug, ceremonySlug),
        eq(schema.editions.year, year)
      )
    )
    .limit(1);

  if (editionRows.length === 0) return null;
  const ed = editionRows[0];

  // Get total categories & winners counts for the footer
  const counts = await db
    .select({
      total_categories: sql<number>`COUNT(DISTINCT ${schema.nominations.categoryId})::int`,
      total_winners: sql<number>`COUNT(CASE WHEN ${schema.nominations.isWinner} = true THEN 1 END)::int`,
    })
    .from(schema.nominations)
    .where(eq(schema.nominations.editionId, ed.editionId));

  // Get top 5 winners
  const winnersRows = await db
    .select({
      category_name: schema.categories.name,
      winner_text: schema.nominations.nomineeText,
      film_title: schema.films.title,
      person_name: schema.persons.name,
    })
    .from(schema.nominations)
    .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
    .leftJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .leftJoin(schema.persons, eq(schema.nominations.personId, schema.persons.id))
    .where(
      and(
        eq(schema.nominations.editionId, ed.editionId),
        eq(schema.nominations.isWinner, true)
      )
    )
    .orderBy(schema.categories.department, schema.categories.name)
    .limit(5);

  return {
    year: ed.year,
    venue: ed.venue,
    host: ed.host,
    total_categories: counts[0]?.total_categories || 0,
    total_winners: counts[0]?.total_winners || 0,
    top_winners: winnersRows.map((w) => ({
      category_name: w.category_name,
      winner_text: w.winner_text,
      film_title: w.film_title || null,
      person_name: w.person_name || null,
    })),
  };
}

export const getEditionYearPreview = unstable_cache(
  async (ceremonySlug: string, year: number) => getEditionYearPreviewRaw(ceremonySlug, year),
  ["get-edition-year-preview"],
  { revalidate: 86400 }
);

export interface ArchiveSearchResult {
  year: number;
  categoryName: string;
  winnerName: string;
  filmTitle: string | null;
  personName: string | null;
}

export async function searchCeremonyArchive(
  ceremonySlug: string,
  query: string
): Promise<ArchiveSearchResult[]> {
  const likeQuery = `%${query}%`;

  return await db
    .select({
      year: schema.editions.year,
      categoryName: schema.categories.name,
      winnerName: schema.nominations.nomineeText,
      filmTitle: schema.films.title,
      personName: schema.persons.name,
    })
    .from(schema.nominations)
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
    .leftJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .leftJoin(schema.persons, eq(schema.nominations.personId, schema.persons.id))
    .where(
      and(
        eq(schema.ceremonies.slug, ceremonySlug),
        or(
          ilike(schema.nominations.nomineeText, likeQuery),
          ilike(schema.films.title, likeQuery),
          ilike(schema.persons.name, likeQuery)
        )
      )
    )
    .orderBy(desc(schema.editions.year))
    .limit(100);
}

export interface CeremonyRecords {
  most_decorated_film: { title: string; year: number; win_count: number } | null;
  most_total_wins_film: { title: string; win_count: number } | null;
  most_decorated_person: { name: string; win_count: number } | null;
  longest_streak: { name: string; streak: number; start_year: number; end_year: number } | null;
  first_edition_winner: { title: string; year: number; category: string } | null;
  latest_winner: { title: string; year: number; category: string } | null;
}

async function getCeremonyRecordsRaw(ceremonySlugInput: string): Promise<CeremonyRecords> {
  const ceremonySlug = ceremonySlugInput === "producers-guild-film-awards" ? "producers-guild" : ceremonySlugInput;
  // 1. most decorated film (single edition wins)
  const mostDecoratedFilmRes = await db
    .select({
      title: schema.films.title,
      year: schema.editions.year,
      win_count: sql<number>`COUNT(*)::int`,
    })
    .from(schema.nominations)
    .innerJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .where(
      and(
        eq(schema.ceremonies.slug, ceremonySlug),
        eq(schema.nominations.isWinner, true)
      )
    )
    .groupBy(schema.films.id, schema.films.title, schema.editions.id, schema.editions.year)
    .orderBy(desc(sql`COUNT(*)`))
    .limit(1);

  // 1b. most total wins across all editions (film)
  const mostWinsFilmAllTimeRes = await db
    .select({
      title: schema.films.title,
      win_count: sql<number>`COUNT(*)::int`,
    })
    .from(schema.nominations)
    .innerJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .where(
      and(
        eq(schema.ceremonies.slug, ceremonySlug),
        eq(schema.nominations.isWinner, true)
      )
    )
    .groupBy(schema.films.id, schema.films.title)
    .orderBy(desc(sql`COUNT(*)`))
    .limit(1);

  // 2. most decorated person (total wins across all editions)
  const mostDecoratedPersonRes = await db
    .select({
      name: schema.persons.name,
      win_count: sql<number>`COUNT(*)::int`,
    })
    .from(schema.nominations)
    .innerJoin(schema.persons, eq(schema.nominations.personId, schema.persons.id))
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .where(
      and(
        eq(schema.ceremonies.slug, ceremonySlug),
        eq(schema.nominations.isWinner, true)
      )
    )
    .groupBy(schema.persons.id, schema.persons.name)
    .orderBy(desc(sql`COUNT(*)`))
    .limit(1);


  // 3. longest streak (consecutive years winning) for a person
  const personWinsByYear = await db
    .select({
      personId: schema.persons.id,
      name: schema.persons.name,
      year: schema.editions.year,
    })
    .from(schema.nominations)
    .innerJoin(schema.persons, eq(schema.nominations.personId, schema.persons.id))
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .where(
      and(
        eq(schema.ceremonies.slug, ceremonySlug),
        eq(schema.nominations.isWinner, true)
      )
    )
    .groupBy(schema.persons.id, schema.persons.name, schema.editions.year)
    .orderBy(schema.persons.id, schema.editions.year);

  let maxStreak = 0;
  let maxStreakPerson = "";
  let streakStart = 0;
  let streakEnd = 0;

  let currentPersonId = -1;
  let currentPersonName = "";
  let currentStreak = 0;
  let currentStart = 0;
  let lastYear = 0;

  for (const row of personWinsByYear) {
    if (row.personId !== currentPersonId) {
      currentPersonId = row.personId;
      currentPersonName = row.name;
      currentStreak = 1;
      currentStart = row.year;
      lastYear = row.year;
    } else {
      if (row.year === lastYear + 1) {
        currentStreak++;
        lastYear = row.year;
      } else if (row.year > lastYear + 1) {
        if (currentStreak > maxStreak) {
          maxStreak = currentStreak;
          maxStreakPerson = currentPersonName;
          streakStart = currentStart;
          streakEnd = lastYear;
        }
        currentStreak = 1;
        currentStart = row.year;
        lastYear = row.year;
      }
    }
    if (currentStreak > maxStreak) {
      maxStreak = currentStreak;
      maxStreakPerson = currentPersonName;
      streakStart = currentStart;
      streakEnd = lastYear;
    }
  }

  const longest_streak = maxStreak > 1 ? {
    name: maxStreakPerson,
    streak: maxStreak,
    start_year: streakStart,
    end_year: streakEnd,
  } : null;

  // 4. first edition winner (Best Film / Best Picture / Fallback)
  const firstEditionWinnerRes = await db
    .select({
      title: schema.films.title,
      year: schema.editions.year,
      category: schema.categories.name,
    })
    .from(schema.nominations)
    .innerJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
    .where(
      and(
        eq(schema.ceremonies.slug, ceremonySlug),
        eq(schema.nominations.isWinner, true),
        or(
          ilike(schema.categories.name, "%Best Film%"),
          ilike(schema.categories.name, "%Best Picture%")
        )
      )
    )
    .orderBy(schema.editions.year)
    .limit(1);

  let firstEditionWinner = firstEditionWinnerRes[0] || null;
  if (!firstEditionWinner) {
    const fallbackRes = await db
      .select({
        title: schema.films.title,
        year: schema.editions.year,
        category: schema.categories.name,
      })
      .from(schema.nominations)
      .leftJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
      .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
      .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
      .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
      .where(
        and(
          eq(schema.ceremonies.slug, ceremonySlug),
          eq(schema.nominations.isWinner, true)
        )
      )
      .orderBy(schema.editions.year)
      .limit(1);

    if (fallbackRes.length > 0) {
      firstEditionWinner = {
        title: fallbackRes[0].title || fallbackRes[0].category,
        year: fallbackRes[0].year,
        category: fallbackRes[0].category,
      };
    }
  }

  // 5. latest edition winner
  const latestWinnerRes = await db
    .select({
      title: schema.films.title,
      year: schema.editions.year,
      category: schema.categories.name,
    })
    .from(schema.nominations)
    .innerJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
    .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
    .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
    .where(
      and(
        eq(schema.ceremonies.slug, ceremonySlug),
        eq(schema.nominations.isWinner, true),
        or(
          ilike(schema.categories.name, "%Best Film%"),
          ilike(schema.categories.name, "%Best Picture%")
        )
      )
    )
    .orderBy(desc(schema.editions.year))
    .limit(1);

  let latestWinner = latestWinnerRes[0] || null;
  if (!latestWinner) {
    const fallbackRes = await db
      .select({
        title: schema.films.title,
        year: schema.editions.year,
        category: schema.categories.name,
      })
      .from(schema.nominations)
      .leftJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
      .innerJoin(schema.editions, eq(schema.nominations.editionId, schema.editions.id))
      .innerJoin(schema.ceremonies, eq(schema.editions.ceremonyId, schema.ceremonies.id))
      .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
      .where(
        and(
          eq(schema.ceremonies.slug, ceremonySlug),
          eq(schema.nominations.isWinner, true)
        )
      )
      .orderBy(desc(schema.editions.year))
      .limit(1);

    if (fallbackRes.length > 0) {
      latestWinner = {
        title: fallbackRes[0].title || fallbackRes[0].category,
        year: fallbackRes[0].year,
        category: fallbackRes[0].category,
      };
    }
  }

  return {
    most_decorated_film: mostDecoratedFilmRes[0] || null,
    most_total_wins_film: mostWinsFilmAllTimeRes[0] || null,
    most_decorated_person: mostDecoratedPersonRes[0] || null,
    longest_streak,
    first_edition_winner: firstEditionWinner,
    latest_winner: latestWinner,
  };
}

export const getCeremonyRecords = unstable_cache(
  async (ceremonySlug: string) => getCeremonyRecordsRaw(ceremonySlug),
  ["get-ceremony-records"],
  { revalidate: 86400 }
);

export interface BestInShowData {
  best_film: {
    id: number;
    title: string;
    slug: string;
    poster_url: string | null;
  } | null;
  most_awarded_film: {
    id: number;
    title: string;
    slug: string;
    poster_url: string | null;
    awards_count: number;
  } | null;
  most_awarded_person: {
    id: number;
    name: string;
    slug: string;
    photo_url: string | null;
    awards_count: number;
  } | null;
}

async function getEditionBestInShowRaw(editionId: number): Promise<BestInShowData> {
  const bestFilmRes = await db
    .select({
      id: schema.films.id,
      title: schema.films.title,
      slug: schema.films.slug,
      poster_url: schema.films.posterUrl,
    })
    .from(schema.nominations)
    .innerJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .innerJoin(schema.categories, eq(schema.nominations.categoryId, schema.categories.id))
    .where(
      and(
        eq(schema.nominations.editionId, editionId),
        eq(schema.nominations.isWinner, true),
        or(
          ilike(schema.categories.name, "%Best Film%"),
          ilike(schema.categories.name, "%Best Picture%")
        )
      )
    )
    .limit(1);

  const mostAwardedFilmRes = await db
    .select({
      id: schema.films.id,
      title: schema.films.title,
      slug: schema.films.slug,
      poster_url: schema.films.posterUrl,
      awards_count: sql<number>`COUNT(*)::int`,
    })
    .from(schema.nominations)
    .innerJoin(schema.films, eq(schema.nominations.filmId, schema.films.id))
    .where(
      and(
        eq(schema.nominations.editionId, editionId),
        eq(schema.nominations.isWinner, true)
      )
    )
    .groupBy(schema.films.id, schema.films.title)
    .orderBy(desc(sql`COUNT(*)`))
    .limit(1);

  const mostAwardedPersonRes = await db
    .select({
      id: schema.persons.id,
      name: schema.persons.name,
      slug: schema.persons.slug,
      photo_url: schema.persons.photoUrl,
      awards_count: sql<number>`COUNT(*)::int`,
    })
    .from(schema.nominations)
    .innerJoin(schema.persons, eq(schema.nominations.personId, schema.persons.id))
    .where(
      and(
        eq(schema.nominations.editionId, editionId),
        eq(schema.nominations.isWinner, true)
      )
    )
    .groupBy(schema.persons.id, schema.persons.name)
    .orderBy(desc(sql`COUNT(*)`))
    .limit(1);

  return {
    best_film: bestFilmRes[0] || null,
    most_awarded_film: mostAwardedFilmRes[0] || null,
    most_awarded_person: mostAwardedPersonRes[0] || null,
  };
}

export const getEditionBestInShow = unstable_cache(
  async (editionId: number) => getEditionBestInShowRaw(editionId),
  ["get-edition-best-in-show"],
  { revalidate: 86400 }
);



