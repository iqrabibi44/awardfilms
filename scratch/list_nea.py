import requests

URL = "https://en.wikipedia.org/w/api.php"
params = {
    "action": "query",
    "list": "categorymembers",
    "cmtitle": "Category:Nigeria Entertainment Awards",
    "cmlimit": "max",
    "format": "json"
}

headers = {
    "User-Agent": "AwardFilmsScraper/1.0 (educational; student_scraper@example.com)"
}

try:
    response = requests.get(URL, params=params, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    members = data.get("query", {}).get("categorymembers", [])
    
    print("Found NEA members:")
    for m in members:
        print(f"Title: {m['title']} | Type: {m['ns']}")
except Exception as e:
    print(f"Error querying Wikipedia API: {e}")
