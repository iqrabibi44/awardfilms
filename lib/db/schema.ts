import {
  pgTable,
  serial,
  varchar,
  integer,
  text,
  timestamp,
  date,
  boolean,
  bigint,
  uniqueIndex,
  index,
  unique,
} from "drizzle-orm/pg-core";

// TABLE 1 — ceremonies
export const ceremonies = pgTable("ceremonies", {
  id: serial("id").primaryKey(),
  slug: varchar("slug", { length: 100 }).unique().notNull(),
  name: varchar("name", { length: 200 }).notNull(),
  shortName: varchar("short_name", { length: 100 }),
  country: varchar("country", { length: 100 }),
  foundedYear: integer("founded_year"),
  frequency: varchar("frequency", { length: 50 }).default("annual"),
  description: text("description"),
  websiteUrl: varchar("website_url", { length: 500 }),
  createdAt: timestamp("created_at", { mode: "date" }).defaultNow(),
});

// TABLE 2 — editions
export const editions = pgTable(
  "editions",
  {
    id: serial("id").primaryKey(),
    ceremonyId: integer("ceremony_id")
      .references(() => ceremonies.id, { onDelete: "cascade" }),
    editionNumber: integer("edition_number"),
    year: integer("year").notNull(),
    dateHeld: date("date_held"),
    venue: varchar("venue", { length: 300 }),
    host: varchar("host", { length: 300 }),
    broadcastNetwork: varchar("broadcast_network", { length: 200 }),
    slug: varchar("slug", { length: 100 }),
  },
  (table) => [
    unique("editions_ceremony_id_year_unique").on(table.ceremonyId, table.year),
  ]
);

// TABLE 3 — categories
export const categories = pgTable(
  "categories",
  {
    id: serial("id").primaryKey(),
    ceremonyId: integer("ceremony_id")
      .references(() => ceremonies.id, { onDelete: "cascade" }),
    slug: varchar("slug", { length: 200 }).notNull(),
    name: varchar("name", { length: 300 }).notNull(),
    department: varchar("department", { length: 100 }),
    isCraft: boolean("is_craft").default(false),
    description: text("description"),
  },
  (table) => [
    unique("categories_ceremony_id_slug_unique").on(table.ceremonyId, table.slug),
  ]
);

// TABLE 4 — films
export const films = pgTable(
  "films",
  {
    id: serial("id").primaryKey(),
    slug: varchar("slug", { length: 300 }).unique().notNull(),
    title: varchar("title", { length: 500 }).notNull(),
    year: integer("year"),
    country: varchar("country", { length: 100 }),
    language: varchar("language", { length: 100 }),
    genre: varchar("genre", { length: 500 }),
    runtime: integer("runtime"),
    synopsis: text("synopsis"),
    posterUrl: varchar("poster_url", { length: 1000 }),
    trailerYoutubeId: varchar("trailer_youtube_id", { length: 50 }),
    boxOfficeUsd: bigint("box_office_usd", { mode: "number" }),
    budgetUsd: bigint("budget_usd", { mode: "number" }),
    imdbId: varchar("imdb_id", { length: 20 }),
    tmdbId: integer("tmdb_id"),
    wikidataId: varchar("wikidata_id", { length: 30 }),
    createdAt: timestamp("created_at", { mode: "date" }).defaultNow(),
  },
  (table) => [
    index("films_imdb_id_idx").on(table.imdbId),
    index("films_year_idx").on(table.year),
  ]
);

// TABLE 5 — persons
export const persons = pgTable(
  "persons",
  {
    id: serial("id").primaryKey(),
    slug: varchar("slug", { length: 300 }).unique().notNull(),
    name: varchar("name", { length: 300 }).notNull(),
    birthYear: integer("birth_year"),
    nationality: varchar("nationality", { length: 100 }),
    biography: text("biography"),
    photoUrl: varchar("photo_url", { length: 1000 }),
    imdbId: varchar("imdb_id", { length: 20 }),
    tmdbId: integer("tmdb_id"),
    wikidataId: varchar("wikidata_id", { length: 30 }),
    createdAt: timestamp("created_at", { mode: "date" }).defaultNow(),
  },
  (table) => [
    index("persons_imdb_id_idx").on(table.imdbId),
  ]
);

// TABLE 6 — nominations
export const nominations = pgTable(
  "nominations",
  {
    id: serial("id").primaryKey(),
    editionId: integer("edition_id")
      .references(() => editions.id, { onDelete: "cascade" }),
    categoryId: integer("category_id")
      .references(() => categories.id, { onDelete: "cascade" }),
    filmId: integer("film_id")
      .references(() => films.id, { onDelete: "set null" }),
    personId: integer("person_id")
      .references(() => persons.id, { onDelete: "set null" }),
    nomineeText: varchar("nominee_text", { length: 500 }).notNull(),
    note: varchar("note", { length: 500 }),
    isWinner: boolean("is_winner").default(false),
    sourceRef: varchar("source_ref", { length: 200 }),
  },
  (table) => [
    index("nominations_edition_id_idx").on(table.editionId),
    index("nominations_category_id_idx").on(table.categoryId),
    index("nominations_film_id_idx").on(table.filmId),
    index("nominations_person_id_idx").on(table.personId),
    index("nominations_is_winner_idx").on(table.isWinner),
  ]
);

// TABLE 7 — streaming_links
export const streamingLinks = pgTable(
  "streaming_links",
  {
    id: serial("id").primaryKey(),
    filmId: integer("film_id")
      .references(() => films.id, { onDelete: "cascade" })
      .notNull(),
    platformName: varchar("platform_name", { length: 100 }).notNull(),
    platformSlug: varchar("platform_slug", { length: 100 }).notNull(),
    url: varchar("url", { length: 1000 }).notNull(),
    affiliateTag: varchar("affiliate_tag", { length: 200 }),
    countryCode: varchar("country_code", { length: 10 }).default("US"),
    linkType: varchar("link_type", { length: 50 }).default("stream"), // stream|rent|buy|free
    region: varchar("region", { length: 10 }).default("global"),
    logoUrl: varchar("logo_url", { length: 500 }),
    updatedAt: timestamp("updated_at", { mode: "date" }).defaultNow(),
  },
  (table) => [
    index("streaming_links_film_id_idx").on(table.filmId),
    unique("streaming_links_film_platform_region_type").on(table.filmId, table.platformSlug, table.region, table.linkType),
  ]
);

// TABLE 8 — sponsor_placements
export const sponsorPlacements = pgTable(
  "sponsor_placements",
  {
    id: serial("id").primaryKey(),
    placementKey: varchar("placement_key", { length: 200 }).unique().notNull(), // e.g. 'bollywood-sidebar'
    advertiser: varchar("advertiser", { length: 200 }),
    creativeUrl: varchar("creative_url", { length: 1000 }),
    clickUrl: varchar("click_url", { length: 1000 }),
    isActive: boolean("is_active").default(true),
    cinemaVertical: varchar("cinema_vertical", { length: 100 }), // null = all verticals
    startDate: date("start_date"),
    endDate: date("end_date"),
  }
);

// TABLE 9 — click_log
export const clickLog = pgTable(
  "click_log",
  {
    id: serial("id").primaryKey(),
    linkId: integer("link_id")
      .references(() => streamingLinks.id, { onDelete: "cascade" }),
    clickedAt: timestamp("clicked_at", { mode: "date" }).defaultNow(),
    referrerPath: varchar("referrer_path", { length: 500 }),
  }
);

// TABLE 10 — newsletter_subscribers
export const newsletterSubscribers = pgTable(
  "newsletter_subscribers",
  {
    id: serial("id").primaryKey(),
    email: varchar("email", { length: 300 }).unique().notNull(),
    vertical: varchar("vertical", { length: 100 }),
    subscribedAt: timestamp("subscribed_at", { mode: "date" }).defaultNow(),
    isConfirmed: boolean("is_confirmed").default(false),
  }
);

// TABLE 11 — film_alternate_titles
export const filmAlternateTitles = pgTable(
  "film_alternate_titles",
  {
    id: serial("id").primaryKey(),
    filmId: integer("film_id")
      .references(() => films.id, { onDelete: "cascade" })
      .notNull(),
    title: varchar("title", { length: 500 }).notNull(),
    languageCode: varchar("language_code", { length: 10 }).notNull(),
    script: varchar("script", { length: 50 }),
    titleType: varchar("title_type", { length: 50 }).default("original"),
  },
  (table) => [
    index("film_alternate_titles_film_id_idx").on(table.filmId),
    index("film_alternate_titles_lang_idx").on(table.languageCode),
    unique("film_alternate_titles_unique").on(table.filmId, table.languageCode, table.titleType),
  ]
);

// TABLE 12 — person_alternate_names
export const personAlternateNames = pgTable(
  "person_alternate_names",
  {
    id: serial("id").primaryKey(),
    personId: integer("person_id")
      .references(() => persons.id, { onDelete: "cascade" })
      .notNull(),
    name: varchar("name", { length: 300 }).notNull(),
    languageCode: varchar("language_code", { length: 10 }).notNull(),
    script: varchar("script", { length: 50 }),
  },
  (table) => [
    index("person_alternate_names_person_id_idx").on(table.personId),
  ]
);
