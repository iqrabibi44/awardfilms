Write-Host "AwardFilms Wikipedia Data Pipeline"
Write-Host "==================================="

Write-Host "PHASE 1: South Asian Cinema"
python scripts/wiki_scraper/south_asian/bollywood.py
python scripts/wiki_scraper/south_asian/lollywood.py
python scripts/wiki_scraper/south_asian/tollywood.py
python scripts/wiki_scraper/south_asian/kollywood.py
python scripts/wiki_scraper/south_asian/mollywood.py
python scripts/wiki_scraper/south_asian/sandalwood.py
python scripts/wiki_scraper/south_asian/bangladeshi.py

Write-Host "PHASE 2: East Asian Cinema"
python scripts/wiki_scraper/east_asian/korean.py
python scripts/wiki_scraper/east_asian/japanese.py
python scripts/wiki_scraper/east_asian/chinese.py
python scripts/wiki_scraper/east_asian/taiwanese.py
python scripts/wiki_scraper/east_asian/hongkong.py

Write-Host "PHASE 3: African Cinema"
python scripts/wiki_scraper/african/nollywood.py
python scripts/wiki_scraper/african/pan_african.py
python scripts/wiki_scraper/african/south_african.py

Write-Host "PHASE 4: Western & European Cinema"
python scripts/wiki_scraper/western/hollywood.py
python scripts/wiki_scraper/western/british.py
python scripts/wiki_scraper/western/french.py
python scripts/wiki_scraper/western/italian.py
python scripts/wiki_scraper/western/german.py
python scripts/wiki_scraper/western/spanish.py
python scripts/wiki_scraper/western/scandinavian.py

Write-Host "PHASE 5: Latin American & Middle Eastern Cinema"
python scripts/wiki_scraper/latin_me/mexican.py
python scripts/wiki_scraper/latin_me/brazilian.py
python scripts/wiki_scraper/latin_me/argentine.py
python scripts/wiki_scraper/latin_me/iranian.py
python scripts/wiki_scraper/latin_me/turkish.py
python scripts/wiki_scraper/latin_me/arabic.py
python scripts/wiki_scraper/latin_me/israeli.py

Write-Host "PIPELINE COMPLETE"
python scripts/wiki_scraper/stats.py
