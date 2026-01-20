"""
Debug script to inspect Land Bank page structure
"""
import requests
from bs4 import BeautifulSoup

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

print(f"Fetching: {url}\n")
response = requests.get(url, headers=HEADERS, timeout=30)
print(f"Status code: {response.status_code}")
print(f"Content length: {len(response.content)} bytes\n")

soup = BeautifulSoup(response.content, 'html.parser')

# Find all links
all_links = soup.find_all('a', href=True)
print(f"Total links found: {len(all_links)}\n")

# Look for any links containing 'pdf', 'agenda', 'board', or 'meeting'
relevant_links = []
for link in all_links:
    href = link['href'].lower()
    text = link.get_text(strip=True).lower()

    if any(keyword in href or keyword in text for keyword in ['pdf', 'agenda', 'board', 'meeting', 'document']):
        relevant_links.append({
            'text': link.get_text(strip=True),
            'href': link['href']
        })

print(f"Found {len(relevant_links)} potentially relevant links:\n")
for i, link in enumerate(relevant_links[:15], 1):  # Show first 15
    print(f"{i}. Text: '{link['text']}'")
    print(f"   URL: {link['href']}\n")

# Also check for any S3 links
s3_links = [link for link in all_links if 's3.amazonaws.com' in link['href']]
print(f"\nFound {len(s3_links)} S3 links:")
for link in s3_links[:10]:
    print(f"  - {link.get_text(strip=True)}: {link['href']}")
