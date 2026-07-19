import pandas as pd
import requests

urls = [
    ("ary_1", "https://en.wikipedia.org/wiki/1st_ARY_Film_Awards"),
    ("ary_2", "https://en.wikipedia.org/wiki/2nd_ARY_Film_Awards"),
    ("hum_9", "https://en.wikipedia.org/wiki/9th_Hum_Awards"),
    ("hum_10", "https://en.wikipedia.org/wiki/10th_Hum_Awards")
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

for name, url in urls:
    print(f"Fetching {name}...")
    try:
        response = requests.get(url, headers=headers)
        dfs = pd.read_html(response.text)
        with open(f"scripts/lollywood/{name}_tables.txt", "w", encoding="utf-8") as f:
            for i, df in enumerate(dfs):
                f.write(f"--- Table {i} ---\n")
                f.write(df.to_string())
                f.write("\n\n")
    except Exception as e:
        print(f"Failed for {name}: {e}")
