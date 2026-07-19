import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://fa.wikipedia.org/w/api.php"
params = {
    "action": "parse",
    "page": "الگو:جشن سینمای ایران",
    "prop": "links",
    "utf8": "",
    "format": "json"
}
headers = {'User-Agent': 'Mozilla/5.0'}

r = requests.get(url, params=params, headers=headers)
data = r.json()
links = data['parse']['links']

print("Links in template:")
for l in links:
    title = l['*']
    print(title)
