"""
Scraper for SEPTA Board meeting pages.

Handles: SEPTA Board meetings
"""

import re
import requests
from bs4 import BeautifulSoup
from .base import BaseScraper


class SeptaScraper(BaseScraper):
    """Scraper for SEPTA board meeting pages."""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    def fetch_latest_agenda(self):
        """
        Fetch the latest agenda PDF link from SEPTA board meetings page.

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

        # Look for PDF links that contain "agenda"
        pdf_links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)

            # Check if this looks like an agenda PDF
            if '.pdf' in href.lower() and 'agenda' in (href.lower() + text.lower()):
                # Convert to full URL if needed
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    full_url = 'https://www.septa.org' + href
                else:
                    # Relative path
                    full_url = 'https://www.septa.org/board/' + href

                pdf_links.append((full_url, text))

        if not pdf_links:
            print(f"No agenda PDFs found on SEPTA board page")
            return None, None

        # Return the first (most recent) agenda
        pdf_url, link_text = pdf_links[0]
        print(f"Found latest agenda: {link_text}")
        print(f"PDF URL: {pdf_url}")

        # Extract date from URL or filename
        # SEPTA often uses formats like: agenda_01_24_2026.pdf or 2026-01-24-agenda.pdf
        date_match = re.search(r'(\d{1,2})[_-](\d{1,2})[_-](\d{4})', pdf_url)
        if date_match:
            month, day, year = date_match.groups()
            meeting_date = f"{year}_{month.zfill(2)}_{day.zfill(2)}"
        else:
            # Try YYYY-MM-DD format
            date_match = re.search(r'(\d{4})[_-](\d{2})[_-](\d{2})', pdf_url)
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
