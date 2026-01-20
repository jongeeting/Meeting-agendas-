"""
Web scrapers for different meeting websites.
"""

from .base import BaseScraper
from .phila_gov import PhilaGovScraper

__all__ = ['BaseScraper', 'PhilaGovScraper']
