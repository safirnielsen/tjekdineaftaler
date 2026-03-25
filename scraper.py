#!/usr/bin/env python3
"""
Scraper til TjekDineAftaler.dk — kører dagligt via GitHub Actions
Henter priser fra udbydernes sider og opdaterer prices.json
"""
import json, re, urllib.request, urllib.error, ssl

# Disable SSL verification for simple scraping
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*',
    'Accept-Language': 'da-DK,da;q=0.9',
}

def fetch(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  FAIL {url[:60]}: {e}")
        return None

def find_price(html, patterns):
    """Try multiple regex patterns, return first match as int"""
    if not html:
        return None
    for p in patterns:
        m = re.search(p, html, re.IGNORECASE)
        if m:
            try:
                return int(re.sub(r'[^\d]', '', m.group(1)))
            except:
                continue
    return None

# ── Provider definitions ──
PROVIDERS = {
    "mobil": [
        {
            "name": "OiSTER",
            "url": "https://www.oister.dk/mobilabonnementer/",
            "patterns": [r'fra\s*(?:kun\s*)?(\d+)\s*kr', r'(\d+)\s*kr\.?/md', r'pris.*?(\d+)\s*kr'],
            "affiliate": "https://go.adt284.net/t/t?a=1666103641&as=2056923302&t=2&tk=1",
            "tags": ["Fri tale", "5G", "Ingen binding"],
            "tp": 4.3
        },
        {
            "name": "Flexii",
            "url": "https://flexii.dk/",
            "patterns": [r'fra\s*(?:kun\s*)?(\d+)\s*kr', r'(\d+)\s*kr\.?/m[ao]', r'abonnement.*?(\d+)\s*kr'],
            "affiliate": "https://go.adt284.net/t/t?a=2025040027&as=2056923302&t=2&tk=1",
            "tags": ["Fri data", "5G", "Ingen binding"],
            "tp": 4.5
        },
        {
            "name": "eesy",
            "url": "https://eesy.dk/",
            "patterns": [r'fra\s*(?:kun\s*)?(\d+)\s*kr', r'(\d+)\s*kr\.?/md'],
            "affiliate": "https://go.adt256.com/t/t?a=1751759538&as=2056923302&t=2&tk=1",
            "tags": ["5G", "Landsdækkende", "Ingen binding"],
            "tp": 4.1
        },
    ],
    "strom": [
        {
            "name": "EWII",
            "url": "https://www.ewii.dk/privat/el/",
            "patterns": [r'(\d+[.,]\d+)\s*øre/kWh', r'spotpris\s*\+\s*(\d+)', r'tillæg.*?(\d+)'],
            "affiliate": "https://go.ewii.dk/t/t?a=1897559994&as=2056923302&t=2&tk=1",
            "tags": ["Variabel", "Grøn strøm", "Ingen binding"],
            "tp": 4.2
        },
        {
            "name": "Norlys",
            "url": "https://norlys.dk/el/",
            "patterns": [r'(\d+[.,]\d+)\s*øre/kWh', r'spotpris\s*\+\s*(\d+)'],
            "affiliate": "https://to.norlys.dk/t/t?a=1737170062&as=2056923302&t=2&tk=1",
            "tags": ["Variabel", "Fast pris", "Grøn strøm"],
            "tp": 3.6
        },
    ],
    "internet": [
        {
            "name": "Hiper",
            "url": "https://www.hiper.dk/bredbånd/",
            "patterns": [r'fra\s*(?:kun\s*)?(\d+)\s*kr', r'(\d+)\s*kr\.?/md'],
            "affiliate": "https://go.adt284.net/t/t?a=1666103641&as=2056923302&t=2&tk=1",
            "tags": ["Fiber", "1000 Mbit", "Ingen binding"],
            "tp": 4.5
        },
        {
            "name": "Norlys",
            "url": "https://norlys.dk/internet/",
            "patterns": [r'fra\s*(?:kun\s*)?(\d+)\s*kr', r'(\d+)\s*kr\.?/md'],
            "affiliate": "https://to.norlys.dk/t/t?a=1737170062&as=2056923302&t=2&tk=1",
            "tags": ["Fiber", "Kabelnet", "5G/Mobilt"],
            "tp": 3.6
        },
    ]
}

# ── Scrape all providers ──
results = {"updated": "", "providers": {}}
import datetime
results["updated"] = datetime.datetime.utcnow().strftime("%Y-%m-%d")

for category, providers in PROVIDERS.items():
    results["providers"][category] = []
    for p in providers:
        print(f"Scraping {p['name']}...")
        html = fetch(p['url'])
        price = find_price(html, p['patterns'])
        
        entry = {
            "name": p["name"],
            "price": price,
            "affiliate": p["affiliate"],
            "tags": p["tags"],
            "tp": p["tp"],
            "scraped": price is not None
        }
        results["providers"][category].append(entry)
        print(f"  {p['name']}: {price} kr/md" if price else f"  {p['name']}: pris ikke fundet")

# Save
with open('prices.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n✓ prices.json saved ({len(results['providers'])} kategorier)")
