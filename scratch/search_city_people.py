import requests

headers = {"User-Agent": "AwardFilmsScraper/1.0"}
search_url = "https://en.wikipedia.org/w/api.php"
params = {
    "action": "query",
    "list": "search",
    "srsearch": "City People Movie Awards",
    "format": "json"
}

response = requests.get(search_url, params=params, headers=headers)
data = response.json()

print("--- Wikipedia Search Results ---")
for result in data.get("query", {}).get("search", []):
    print(f"Title: {result['title']}")
    print(f"Snippet: {result['snippet']}")
    print("-" * 50)
