"""
Scraper for Philadelphia Housing Development Corporation (PHDC) websites.

Handles: Philadelphia Redevelopment Authority, Land Bank, PHRC
"""

import re
import requests
from bs4 import BeautifulSoup
from .base import BaseScraper


class PHDCScraper(BaseScraper):
    """Scraper for PHDC-hosted meeting pages."""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    def fetch_latest_agenda(self):
        """
        Fetch the latest agenda PDF link from PHDC meeting page.

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

        # Look for PDF links matching the pattern
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']

            # Check if this looks like an agenda PDF
            if self.pdf_pattern.lower() in href.lower() and '.pdf' in href.lower():
                # Convert to full URL if needed
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    # Get base URL
                    base = self.url.split('/')[0] + '//' + self.url.split('/')[2]
                    full_url = base + href
                else:
                    # Relative path
                    base = '/'.join(self.url.split('/')[:-1])
                    full_url = base + '/' + href

                pdf_links.append((full_url, link.get_text(strip=True)))

        if not pdf_links:
            print(f"No agenda PDFs found matching pattern: {self.pdf_pattern}")
            return None, None

        # Return the first (most recent) agenda
        pdf_url, link_text = pdf_links[0]
        print(f"Found latest agenda: {link_text}")
        print(f"PDF URL: {pdf_url}")

        # Extract date from URL (format: YYYY-MM-DD or similar)
        date_match = re.search(r'(\d{4})[_-]?(\d{2})[_-]?(\d{2})', pdf_url)
        if date_match:
            year, month, day = date_match.groups()
            meeting_date = f"{year}_{month}_{day}"
        else:
            # Try to extract from link text
            date_match = re.search(r'(\w+)\s+(\d+)[,\s]+(\d+)', link_text)
            if date_match:
                meeting_date = f"{date_match.group(1)}_{date_match.group(2)}_{date_match.group(3)}"
            else:
                meeting_date = "unknown_date"

        return pdf_url, meeting_date
