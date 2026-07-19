import { NAV_DATA } from "@/lib/data/navigation";

/**
 * Returns the correct visual route for a given ceremony slug.
 * Caters to normal dynamic routes (/[supercategory]/[industry]/[ceremony])
 * as well as the special custom Lollywood routes (/south-asian-cinema/lollywood/[ceremony]).
 */
export function getCeremonyPath(ceremonySlug: string): string {
  for (const cat of NAV_DATA) {
    for (const ind of cat.industries) {
      const found = ind.ceremonies.find((c) => c.slug === ceremonySlug);
      if (found) {
        if (ind.slug === "lollywood") {
          return `/south-asian-cinema/lollywood/${ceremonySlug}`;
        }
        return `/${cat.slug}/${ind.slug}/${ceremonySlug}`;
      }
    }
  }
  return `/${ceremonySlug}`; // fallback
}

/**
 * Returns the correct visual route for a ceremony edition page.
 * Caters to normal dynamic routes (/[supercategory]/[industry]/[ceremony]/[year])
 * and falls back to ceremony page for Lollywood (which does not have dynamic year pages).
 */
export function getCeremonyEditionPath(ceremonySlug: string, year: number | string): string {
  for (const cat of NAV_DATA) {
    for (const ind of cat.industries) {
      const found = ind.ceremonies.find((c) => c.slug === ceremonySlug);
      if (found) {
        if (ind.slug === "lollywood") {
          return `/south-asian-cinema/lollywood/${ceremonySlug}?year=${year}`;
        }
        return `/${cat.slug}/${ind.slug}/${ceremonySlug}/${year}`;
      }
    }
  }
  return `/${ceremonySlug}/${year}`; // fallback
}
