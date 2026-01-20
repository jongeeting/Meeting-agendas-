"""
Email monitoring module for RCO newsletters.

This module handles fetching emails from Gmail, classifying them for relevance,
and extracting meeting information.
"""

from .gmail_client import GmailClient
from .email_classifier import EmailClassifier
from .meeting_extractor import MeetingExtractor

__all__ = ['GmailClient', 'EmailClassifier', 'MeetingExtractor']
