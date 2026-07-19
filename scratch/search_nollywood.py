import requests

URL = "https://en.wikipedia.org/w/api.php"

def search_wiki(query):
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "utf8": "",
        "format": "json"
    }
    headers = {"User-Agent": "AwardFilmsScraper/1.0 (educational; student_scraper@example.com)"}
    try:
        r = requests.get(URL, params=params, headers=headers)
        data = r.json()
        print(f"\n--- Search results for '{query}' ---")
        for s in data.get("query", {}).get("search", []):
            print(f"  Title: {s['title']} | snippet: {s['snippet'][:150]}")
    except Exception as e:
        print(f"Error searching for '{query}': {e}")

search_wiki("Africa International Film Festival")
search_wiki("City People Entertainment Awards")
