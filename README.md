# AwardFilms — Global Film Awards Database (PHP & MySQL)

This repository contains the database and PHP frontend of the **AwardFilms** web platform. All Next.js and React components have been completely migrated to a lightweight, standard PHP architecture suitable for hosting on any standard Apache/PHP/MySQL web server (like XAMPP or cheap shared hosting).

## Project Structure

- **`/` (Root)**: Core PHP page templates that serve as the frontend views.
  - `index.php`: The homepage featuring global statistics, particle effects, and recent award winners.
  - `browse.php`: Browse page for categories, genres, and countries.
  - `ceremony.php`: List and detail views of specific award ceremonies.
  - `edition.php`: Detailed view of specific editions (years) of ceremonies and nominations.
  - `film-details.php`: Details and award history for individual films.
  - `person-details.php`: Detailed nomination/winner information for actors, directors, and crew.
  - `search-results.php`: Universal search results page.
  - `.htaccess`: Apache URL rewriting configuration that translates SEO-friendly URLs (e.g., `/films/life-is-beautiful-1998`) into PHP script queries.
- **`assets/`**: Static CSS files (including global theme variables and Tailwind CSS styles) and client-side JS assets.
- **`config/`**: Database configuration classes.
  - `DB.php`: Shared PDO MySQL connection configuration.
- **`layouts/`**: Reusable header, footer, and HTML head blocks.
- **`lib/`**: Business logic, helpers, and SQL queries.
  - `queries.php`: Dynamic database fetch functions mapped directly to the local MySQL schema.
- **`images/`**: Static media assets and images for award ceremonies.
- **`african_cinema/`**, **`hollywood/`**: Python-based web scrapers that fetch and ingest award data from various film sites and Wikipedia into the local MySQL database.
- **`scripts/`**, **`scratch/`**: Ingestion workflows, schema updates, and inspection utilities.

## Local Development (XAMPP Setup)

1. **Deploy to Document Root**: Copy all frontend PHP files and directories (`assets`, `config`, `layouts`, `lib`, `images`, `.htaccess` and all `.php` page templates) directly into the XAMPP directory:
   `C:\xampp\htdocs\`
2. **Database Import**: Set up a local MySQL database named `awardfilms_db` on port `3306` with username `root` and no password. Import your SQL schema and records.
3. **Apache Module**: Make sure the Apache `mod_rewrite` module is enabled in `httpd.conf` to process route redirects in `.htaccess`.
4. **Access the Site**: Navigate to `http://localhost/` or `http://localhost/index.php` in your browser.
