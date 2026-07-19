export const AFFILIATE_CONFIG = {
  amazon_prime: { tag: "awardfilms-20", baseUrl: "https://amazon.com/dp/" },
  mubi: { tag: "awardfilms", baseUrl: "https://mubi.com/films/" },
  shudder: { tag: "awardfilms", baseUrl: "https://shudder.com/movies/" },
  criterion: { tag: "awardfilms", baseUrl: "https://criterion.com/films/" },
  justwatch: { baseUrl: "https://justwatch.com/us/movie/" }, // no tag, deep links
  netflix: { tag: "shareasale_awardfilms", baseUrl: "https://netflix.com/title/" },
  disney_plus: { tag: "awardfilms", baseUrl: "https://disneyplus.com/movies/" },
};

export type AffiliatePlatform = keyof typeof AFFILIATE_CONFIG;

export function getAffiliateUrl(platformSlug: string, originalUrl: string, dbTag?: string | null): string {
  const config = AFFILIATE_CONFIG[platformSlug as AffiliatePlatform];
  
  if (!config) {
    // If not a configured affiliate platform, return original URL (fallback)
    return originalUrl;
  }

  // Prefer DB-provided tag, then fallback to config tag
  const tag = dbTag || ('tag' in config ? config.tag : null);

  // If there's no tag mechanism, just return the base URL / original URL
  if (!tag) {
    return originalUrl;
  }

  // Construct URL based on platform rules.
  // This is a naive implementation: many platforms use different query param keys for tags.
  // Amazon uses ?tag=...
  try {
    const urlObj = new URL(originalUrl);
    
    if (platformSlug === 'amazon_prime') {
      urlObj.searchParams.set('tag', tag);
    } else {
      urlObj.searchParams.set('affiliate', tag);
    }
    
    return urlObj.toString();
  } catch (e) {
    // If originalUrl isn't a valid full URL, fallback
    return originalUrl;
  }
}
