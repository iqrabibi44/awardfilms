import sys
import os
sys.path.append(os.path.abspath("hollywood/golden_globe_awards"))
from scrape_golden_globes import scrape_ceremony

records = scrape_ceremony("https://en.wikipedia.org/wiki/81st_Golden_Globe_Awards", 2023, "81st Golden Globe Awards")
print(f"Records found: {len(records)}")
for r in records[:5]:
    print(r)
