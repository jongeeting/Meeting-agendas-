"""
Scraper for Philadelphia Land Bank website.

Handles: Philadelphia Land Bank board meetings
"""

import re
import requests
from bs4 import BeautifulSoup
from .base import BaseScraper


class LandBankScraper(BaseScraper):
    """Scraper for Philadelphia Land Bank website."""

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

    def fetch_latest_agenda(self):
        """
        Fetch the latest agenda PDF link from Land Bank board page.

        Returns:
            tuple: (pdf_url, meeting_date_str) or (None, None) if not found
        """
        print(f"Fetching {self.name} meeting page: {self.url}")

        try:
            response = requests.get(self.url, headers=self.HEADERS, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching webpage: {e}")
            return None, None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for PDF links from landbank-media.s3.amazonaws.com
        pdf_links = []
        all_pdf_links = []  # For debugging

        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            text_lower = text.lower()

            # Debug: collect all PDF links for inspection
            if '.pdf' in href.lower():
                all_pdf_links.append((href, text))

            # Check if this is a board agenda/package PDF
            is_s3_pdf = 'landbank-media.s3.amazonaws.com' in href and '.pdf' in href.lower()
            is_agenda = any(keyword in text_lower for keyword in ['agenda', 'board package', 'board packet'])

            # Exclude minutes (we want agendas, not post-meeting minutes)
            is_minutes = 'minute' in text_lower

            if is_s3_pdf and is_agenda and not is_minutes:
                pdf_links.append((href, text))

        # Debug output
        if all_pdf_links and not pdf_links:
            print(f"\nDEBUG: Found {len(all_pdf_links)} PDF links total, but none matched our criteria:")
            for pdf_url, pdf_text in all_pdf_links[:5]:  # Show first 5
                print(f"  - Text: '{pdf_text}'")
                print(f"    URL: {pdf_url}")
                is_s3 = 'landbank-media.s3.amazonaws.com' in pdf_url
                print(f"    Is S3: {is_s3}, Has 'agenda' keyword: {'agenda' in pdf_text.lower()}\n")

        if not pdf_links:
            print(f"No agenda PDFs found on Land Bank board page")
            return None, None

        # Return the first (most recent) agenda
        pdf_url, link_text = pdf_links[0]
        print(f"Found latest agenda: {link_text}")
        print(f"PDF URL: {pdf_url}")

        # Extract date from URL path: /media/YYYY/MM/
        date_match = re.search(r'/media/(\d{4})/(\d{2})/', pdf_url)
        if date_match:
            year, month = date_match.groups()
            meeting_date = f"{year}_{month}_unknown"
        else:
            # Try to extract from link text
            date_match = re.search(r'(\w+)\s+(\d+)[,\s]+(\d+)', link_text)
            if date_match:
                meeting_date = f"{date_match.group(3)}_{date_match.group(1)}_{date_match.group(2)}"
            else:
                meeting_date = "unknown_date"

        return pdf_url, meeting_date
