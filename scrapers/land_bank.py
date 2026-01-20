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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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

        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True).lower()

            # Check if this is a board agenda/package PDF
            is_s3_pdf = 'landbank-media.s3.amazonaws.com' in href and '.pdf' in href.lower()
            is_agenda = any(keyword in text for keyword in ['agenda', 'board package', 'board packet'])

            # Exclude minutes (we want agendas, not post-meeting minutes)
            is_minutes = 'minute' in text

            if is_s3_pdf and is_agenda and not is_minutes:
                pdf_links.append((href, link.get_text(strip=True)))

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
