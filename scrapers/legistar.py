"""
Scraper for Legistar-based meeting calendars.

Handles: Philadelphia City Council committees (Rules, Streets, etc.)
"""

import re
import requests
from bs4 import BeautifulSoup
from .base import BaseScraper


class LegistarScraper(BaseScraper):
    """Scraper for Legistar calendar pages."""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    def fetch_latest_agenda(self):
        """
        Fetch the latest agenda PDF link from Legistar calendar.

        This is a simplified version that looks for recent meetings.
        Legistar calendars can be complex - this may need refinement.

        Returns:
            tuple: (pdf_url, meeting_date_str) or (None, None) if not found
        """
        print(f"Fetching {self.name} meeting page: {self.url}")

        # Legistar often has committee-specific URLs or requires filtering
        # For now, try to fetch the main calendar and look for the committee name

        try:
            response = requests.get(self.url, headers=self.HEADERS, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching webpage: {e}")
            return None, None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for links that contain both the committee name and "agenda"
        committee_keywords = self.config.get('committee_keywords', [self.pdf_pattern])

        agenda_links = []

        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True).lower()

            # Check if this looks like an agenda PDF for our committee
            is_pdf = '.pdf' in href.lower() or 'agenda' in text
            is_our_committee = any(keyword.lower() in text or keyword.lower() in href.lower()
                                  for keyword in committee_keywords)

            if is_pdf and is_our_committee:
                # Convert to full URL if needed
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    base = self.url.split('/')[0] + '//' + self.url.split('/')[2]
                    full_url = base + href
                else:
                    # Relative path
                    base = '/'.join(self.url.split('/')[:-1])
                    full_url = base + '/' + href

                agenda_links.append((full_url, text))

        if not agenda_links:
            print(f"No agenda PDFs found for {self.name}")
            print(f"Looked for keywords: {committee_keywords}")
            return None, None

        # Return the first (hopefully most recent) agenda
        pdf_url, link_text = agenda_links[0]
        print(f"Found agenda: {link_text[:80]}...")
        print(f"PDF URL: {pdf_url}")

        # Extract date from URL or link text
        # Legistar often uses format like: MeetingDetail.aspx?ID=123456
        # Or direct PDF links with dates
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
