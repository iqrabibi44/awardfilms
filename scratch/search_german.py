import requests

def search_wiki(query):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json"
    }
    try:
        data = requests.get(url, params=params).json()
        results = data.get("query", {}).get("search", [])
        if results:
            print(f"[{query}] -> {results[0]['title'].replace(' ', '_')}")
        else:
            print(f"[{query}] -> Not found")
    except Exception as e:
        print(f"[{query}] -> Error: {e}")

queries = [
    "German Film Award for Best Actor",
    "German Film Award for Best Actress",
    "German Film Award for Best Supporting Actor",
    "German Film Award for Best Supporting Actress",
    "Bavarian Film Award for Best Actor",
    "Bavarian Film Award for Best Director",
    "Bavarian Film Awards"
]

for q in queries:
    search_wiki(q)
