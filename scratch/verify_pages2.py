import urllib.request
import urllib.error

pages = [
    "http://localhost:8000/",
    "http://localhost:8000/hollywood/american/oscars",
    "http://localhost:8000/hollywood/american/oscars/best-picture",
    "http://localhost:8000/persons/alia-bhatt",
    "http://localhost:8000/south-asian/lollywood/nigar-awards",
    "http://localhost:8000/search?q=alia",
    "http://localhost:8000/hollywood/american/oscars/2024"
]

for url in pages:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8', errors='ignore')
            print(f"[OK] {url} (HTTP {response.status})")
            if 'Ceremony Not Found' in content or 'No records found' in content or "Archive Not Found" in content or "Profile Not Found" in content:
                print("  => Loaded fallback gracefully")
    except urllib.error.HTTPError as e:
        content = e.read().decode('utf-8', errors='ignore')
        print(f"[HTTP ERROR {e.code}] {url}")
        if 'Ceremony Not Found' in content or 'No records found' in content or "Archive Not Found" in content or "Profile Not Found" in content:
            print("  => Returned 404 but loaded fallback gracefully")
    except Exception as e:
        print(f"[ERROR] {url} - {str(e)}")
