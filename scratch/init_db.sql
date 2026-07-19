CREATE DATABASE IF NOT EXISTS awardfilms_db;
USE awardfilms_db;

-- 1. ceremonies
CREATE TABLE IF NOT EXISTS ceremonies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    short_name VARCHAR(100),
    country VARCHAR(100),
    founded_year INT,
    frequency VARCHAR(50) DEFAULT 'annual',
    description TEXT,
    website_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. editions
CREATE TABLE IF NOT EXISTS editions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ceremony_id INT,
    edition_number INT,
    year INT NOT NULL,
    date_held DATE,
    venue VARCHAR(300),
    host VARCHAR(300),
    broadcast_network VARCHAR(200),
    slug VARCHAR(100),
    CONSTRAINT fk_editions_ceremony FOREIGN KEY (ceremony_id) REFERENCES ceremonies(id) ON DELETE CASCADE,
    UNIQUE KEY uq_editions_ceremony_year (ceremony_id, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. categories
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ceremony_id INT,
    slug VARCHAR(200) NOT NULL,
    name VARCHAR(300) NOT NULL,
    department VARCHAR(100),
    is_craft BOOLEAN DEFAULT FALSE,
    description TEXT,
    CONSTRAINT fk_categories_ceremony FOREIGN KEY (ceremony_id) REFERENCES ceremonies(id) ON DELETE CASCADE,
    UNIQUE KEY uq_categories_ceremony_slug (ceremony_id, slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. films
CREATE TABLE IF NOT EXISTS films (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(300) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    year INT,
    country VARCHAR(100),
    language VARCHAR(100),
    genre VARCHAR(500),
    runtime INT,
    synopsis TEXT,
    poster_url VARCHAR(1000),
    trailer_youtube_id VARCHAR(50),
    box_office_usd BIGINT,
    budget_usd BIGINT,
    imdb_id VARCHAR(20),
    tmdb_id INT,
    wikidata_id VARCHAR(30),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_films_imdb_id (imdb_id),
    INDEX idx_films_year (year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. persons
CREATE TABLE IF NOT EXISTS persons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(300) UNIQUE NOT NULL,
    name VARCHAR(300) NOT NULL,
    birth_year INT,
    nationality VARCHAR(100),
    biography TEXT,
    photo_url VARCHAR(1000),
    imdb_id VARCHAR(20),
    tmdb_id INT,
    wikidata_id VARCHAR(30),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_persons_imdb_id (imdb_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. nominations
CREATE TABLE IF NOT EXISTS nominations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    edition_id INT,
    category_id INT,
    film_id INT,
    person_id INT,
    nominee_text VARCHAR(500) NOT NULL,
    note VARCHAR(500),
    is_winner BOOLEAN DEFAULT FALSE,
    source_ref VARCHAR(200),
    CONSTRAINT fk_nominations_edition FOREIGN KEY (edition_id) REFERENCES editions(id) ON DELETE CASCADE,
    CONSTRAINT fk_nominations_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    CONSTRAINT fk_nominations_film FOREIGN KEY (film_id) REFERENCES films(id) ON DELETE SET NULL,
    CONSTRAINT fk_nominations_person FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE SET NULL,
    INDEX idx_nominations_edition (edition_id),
    INDEX idx_nominations_category (category_id),
    INDEX idx_nominations_film (film_id),
    INDEX idx_nominations_person (person_id),
    INDEX idx_nominations_is_winner (is_winner),
    UNIQUE KEY uq_nominations_edition_category_film_person (edition_id, category_id, film_id, person_id, nominee_text(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. streaming_links
CREATE TABLE IF NOT EXISTS streaming_links (
    id INT AUTO_INCREMENT PRIMARY KEY,
    film_id INT NOT NULL,
    platform_name VARCHAR(100) NOT NULL,
    platform_slug VARCHAR(100) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    affiliate_tag VARCHAR(200),
    country_code VARCHAR(10) DEFAULT 'US',
    link_type VARCHAR(50) DEFAULT 'stream',
    region VARCHAR(10) DEFAULT 'global',
    logo_url VARCHAR(500),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_streaming_links_film FOREIGN KEY (film_id) REFERENCES films(id) ON DELETE CASCADE,
    INDEX idx_streaming_links_film (film_id),
    UNIQUE KEY uq_streaming_links_film_platform_region_type (film_id, platform_slug, region, link_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. sponsor_placements
CREATE TABLE IF NOT EXISTS sponsor_placements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    placement_key VARCHAR(200) UNIQUE NOT NULL,
    advertiser VARCHAR(200),
    creative_url VARCHAR(1000),
    click_url VARCHAR(1000),
    is_active BOOLEAN DEFAULT TRUE,
    cinema_vertical VARCHAR(100),
    start_date DATE,
    end_date DATE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. click_log
CREATE TABLE IF NOT EXISTS click_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    link_id INT,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    referrer_path VARCHAR(500),
    CONSTRAINT fk_click_log_link FOREIGN KEY (link_id) REFERENCES streaming_links(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. newsletter_subscribers
CREATE TABLE IF NOT EXISTS newsletter_subscribers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(300) UNIQUE NOT NULL,
    vertical VARCHAR(100),
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_confirmed BOOLEAN DEFAULT FALSE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. film_alternate_titles
CREATE TABLE IF NOT EXISTS film_alternate_titles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    film_id INT NOT NULL,
    title VARCHAR(500) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    script VARCHAR(50),
    title_type VARCHAR(50) DEFAULT 'original',
    CONSTRAINT fk_film_alt_titles_film FOREIGN KEY (film_id) REFERENCES films(id) ON DELETE CASCADE,
    INDEX idx_film_alt_titles_film (film_id),
    INDEX idx_film_alt_titles_lang (language_code),
    UNIQUE KEY uq_film_alt_titles (film_id, language_code, title_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. person_alternate_names
CREATE TABLE IF NOT EXISTS person_alternate_names (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT NOT NULL,
    name VARCHAR(300) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    script VARCHAR(50),
    CONSTRAINT fk_person_alt_names_person FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    INDEX idx_person_alt_names_person (person_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
