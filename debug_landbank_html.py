"""
Check raw HTML from Land Bank page
"""
import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
}

url = "https://phillylandbank.org/philadelphia-land-bank-board/"
response = requests.get(url, headers=HEADERS, timeout=30)

# Save raw HTML to file
with open('landbank_raw.html', 'w', encoding='utf-8', errors='replace') as f:
    f.write(response.text)

print(f"Saved raw HTML to landbank_raw.html ({len(response.text)} characters)")
print("\nSearching for key terms in HTML:")
print(f"  'landbank-media' found: {'landbank-media' in response.text}")
print(f"  's3.amazonaws' found: {'s3.amazonaws' in response.text}")
print(f"  '.pdf' found: {'.pdf' in response.text.lower()}")
print(f"  'agenda' found: {'agenda' in response.text.lower()}")
print(f"  '<a href' found: {'<a href' in response.text.lower()}")

# Look for any WordPress shortcodes or dynamic loaders
print(f"\n  '[' shortcode bracket found: {'[' in response.text}")
print(f"  'wp-content' found: {'wp-content' in response.text}")
print(f"  'javascript' found: {'javascript' in response.text.lower()}")
