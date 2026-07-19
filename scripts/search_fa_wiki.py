import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://fa.wikipedia.org/w/api.php"
params = {
    "action": "query",
    "list": "search",
    "srsearch": "جشن سینمای ایران",
    "srlimit": 50,
    "utf8": "",
    "format": "json"
}
headers = {'User-Agent': 'Mozilla/5.0'}

r = requests.get(url, params=params, headers=headers)
data = r.json()
search_results = data['query']['search']
print(f"Total search results: {len(search_results)}")
for r in search_results:
    print(r['title'])
