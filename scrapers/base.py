"""
Base scraper class that all meeting scrapers inherit from.
"""

from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Abstract base class for meeting agenda scrapers."""

    def __init__(self, config):
        """
        Initialize scraper with configuration.

        Args:
            config: Dictionary containing scraper configuration
                   (url, pdf_pattern, etc.)
        """
        self.config = config
        self.url = config.get('url')
        self.pdf_pattern = config.get('pdf_pattern', '')
        self.name = config.get('name', 'Unknown Meeting')

    @abstractmethod
    def fetch_latest_agenda(self):
        """
        Fetch the latest agenda PDF link from the website.

        Must be implemented by subclasses.

        Returns:
            tuple: (pdf_url, meeting_date_str) or (None, None) if not found
        """
        pass

    def __str__(self):
        return f"{self.__class__.__name__}({self.name})"

    def __repr__(self):
        return self.__str__()
