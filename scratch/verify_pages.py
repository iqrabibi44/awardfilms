import urllib.request
import urllib.error

pages = [
    "http://localhost:8000/",
    "http://localhost:8000/search?q=alia",
    "http://localhost:8000/hollywood/american/oscars",
    "http://localhost:8000/hollywood/american/oscars/2024",
    "http://localhost:8000/persons/alia-bhatt"
]

for url in pages:
    print(f"Testing {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8', errors='ignore')
            if 'Fatal error' in content or 'Parse error' in content:
                print(f"  [ERROR] Found PHP error in content for {url}")
            else:
                print(f"  [OK] Loaded successfully (HTTP {response.status})")
    except urllib.error.HTTPError as e:
        content = e.read().decode('utf-8', errors='ignore')
        print(f"  [HTTP ERROR {e.code}]")
        if 'Fatal error' in content or 'Parse error' in content:
             print(f"  [FATAL ERROR DETECTED in response body]")
    except urllib.error.URLError as e:
        print(f"  [CONNECTION ERROR] {e.reason} - Is the PHP server running?")
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
