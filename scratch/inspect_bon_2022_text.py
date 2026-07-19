import requests
from bs4 import BeautifulSoup
import sys

url = "https://en.wikipedia.org/wiki/2022_Best_of_Nollywood_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

content_div = soup.find(id="mw-content-text")
if content_div:
    text = content_div.get_text()
    sys.stdout.buffer.write(text[:3000].encode('utf-8'))
else:
    print("No content div found.")
