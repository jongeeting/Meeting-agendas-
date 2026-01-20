"""
AI-powered email classifier for RCO newsletters.

Uses Claude to determine if emails contain meeting announcements
relevant to housing, zoning, development, and transportation.
"""

import os
import json
from anthropic import Anthropic


class EmailClassifier:
    """Classifies emails using Claude AI."""

    CLASSIFICATION_PROMPT = """You are analyzing emails from Philadelphia neighborhood organizations (RCOs) to identify meeting announcements relevant to housing advocates.

You need to determine:
1. Does this email contain a meeting announcement?
2. Is the meeting relevant to housing, zoning, development, streets, bike lanes, or transit?

Respond with a JSON object with these fields:
{
  "is_meeting": true/false,
  "is_relevant": true/false,
  "confidence": "high"/"medium"/"low",
  "meeting_type": "zoning_meeting"/"general_meeting"/"community_event"/null,
  "topics": ["zoning", "development", "bike lanes", etc.],
  "reason": "Brief explanation of why this is/isn't relevant"
}

RELEVANT topics include:
- Zoning variances and applications
- New development proposals
- Building permits and construction
- Bike lanes and protected bike infrastructure
- Transit improvements (bus stops, trolley, etc.)
- Street redesigns and road diets
- Parking changes
- Housing policy
- Land use changes

NOT relevant:
- General crime updates
- Community events (festivals, cleanups)
- Fundraisers
- Social gatherings
- Non-development related news

Here's the email to analyze:

Subject: {subject}
From: {sender}

{body}

Respond ONLY with the JSON object, no other text."""

    def __init__(self, api_key=None):
        """
        Initialize classifier.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable must be set")

        self.client = Anthropic(api_key=self.api_key)

    def classify_email(self, email):
        """
        Classify a single email for relevance.

        Args:
            email: Email dictionary with 'subject', 'sender', 'body' keys

        Returns:
            dict: Classification result with is_meeting, is_relevant, topics, etc.
        """
        try:
            # Build prompt with email content
            prompt = self.CLASSIFICATION_PROMPT.format(
                subject=email.get('subject', 'No Subject'),
                sender=email.get('sender', 'Unknown'),
                body=email.get('body', email.get('snippet', ''))[:5000]  # Limit body length
            )

            # Call Claude API
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse JSON response
            response_text = message.content[0].text.strip()

            # Try to extract JSON if wrapped in markdown
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()

            # Try to find JSON object boundaries
            if '{' in response_text and '}' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                response_text = response_text[start:end]

            classification = json.loads(response_text)

            return classification

        except json.JSONDecodeError as e:
            print(f"Error parsing classification response: {e}")
            if 'response_text' in locals():
                print(f"Response was: {response_text[:500]}")
            return {
                'is_meeting': False,
                'is_relevant': False,
                'confidence': 'low',
                'reason': 'Failed to parse AI response'
            }
        except Exception as e:
            print(f"Error classifying email: {e}")
            if 'response_text' in locals():
                print(f"Response text: {response_text[:500] if isinstance(response_text, str) else 'N/A'}")
            return {
                'is_meeting': False,
                'is_relevant': False,
                'confidence': 'low',
                'reason': f'Error: {str(e)}'
            }

    def classify_batch(self, emails, callback=None):
        """
        Classify multiple emails.

        Args:
            emails: List of email dictionaries
            callback: Optional function to call after each classification
                     (useful for progress updates)

        Returns:
            list: List of (email, classification) tuples
        """
        results = []

        for i, email in enumerate(emails, 1):
            if callback:
                callback(i, len(emails), email)

            classification = self.classify_email(email)
            results.append((email, classification))

        return results

    def filter_relevant(self, classified_emails):
        """
        Filter to only relevant meeting announcements.

        Args:
            classified_emails: List of (email, classification) tuples

        Returns:
            list: Filtered list of relevant emails with classifications
        """
        relevant = []

        for email, classification in classified_emails:
            if classification.get('is_meeting') and classification.get('is_relevant'):
                relevant.append((email, classification))

        return relevant
