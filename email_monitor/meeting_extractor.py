"""
Extract structured meeting information from emails using Claude.
"""

import os
import json
from datetime import datetime
from anthropic import Anthropic


class MeetingExtractor:
    """Extracts meeting details from emails using Claude AI."""

    EXTRACTION_PROMPT = """You are extracting meeting details from an RCO (neighborhood organization) email.

Extract the following information and return as JSON:
{
  "meeting_date": "YYYY-MM-DD" or null,
  "meeting_time": "HH:MM AM/PM" or null,
  "meeting_location": "Address or 'Zoom' or 'Virtual'" or null,
  "meeting_link": "Zoom/meeting URL" or null,
  "organization_name": "Name of RCO/organization",
  "agenda_items": [
    {
      "title": "Brief title of agenda item",
      "address": "Street address if mentioned",
      "type": "zoning_variance"/"development"/"bike_lane"/"transit"/"other",
      "description": "1-2 sentence description",
      "why_relevant": "Why this matters for housing advocates"
    }
  ],
  "contact_email": "Contact email if mentioned",
  "rsvp_required": true/false
}

Tips:
- For dates: Look for patterns like "January 23", "1/23", "Tuesday, Jan 23"
- For times: Look for "7pm", "7:00 PM", "6:30 p.m."
- For locations: Could be address, church name, library, or "Zoom"
- Extract ALL agenda items that relate to zoning, development, or infrastructure
- If address mentioned like "1234 Main St" - include it
- For "why_relevant": Explain impact on housing production, affordability, or development

Here's the email:

Subject: {subject}

{body}

Respond ONLY with the JSON object."""

    def __init__(self, api_key=None):
        """
        Initialize extractor.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable must be set")

        self.client = Anthropic(api_key=self.api_key)

    def extract_meeting_info(self, email):
        """
        Extract structured meeting information from email.

        Args:
            email: Email dictionary with 'subject' and 'body' keys

        Returns:
            dict: Extracted meeting information
        """
        try:
            # Build prompt
            prompt = self.EXTRACTION_PROMPT.format(
                subject=email.get('subject', ''),
                body=email.get('body', email.get('snippet', ''))[:8000]  # Limit length
            )

            # Call Claude
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            response_text = message.content[0].text.strip()

            # Extract JSON
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()

            meeting_info = json.loads(response_text)

            # Add metadata
            meeting_info['email_id'] = email.get('id')
            meeting_info['email_sender'] = email.get('sender')
            meeting_info['email_date'] = email.get('date')

            return meeting_info

        except json.JSONDecodeError as e:
            print(f"Error parsing extraction response: {e}")
            print(f"Response was: {response_text[:200]}")
            return None
        except Exception as e:
            print(f"Error extracting meeting info: {e}")
            return None

    def extract_batch(self, emails, callback=None):
        """
        Extract meeting info from multiple emails.

        Args:
            emails: List of email dictionaries
            callback: Optional progress callback

        Returns:
            list: List of extracted meeting dictionaries
        """
        meetings = []

        for i, email in enumerate(emails, 1):
            if callback:
                callback(i, len(emails), email)

            meeting_info = self.extract_meeting_info(email)
            if meeting_info:
                meetings.append(meeting_info)

        return meetings

    def format_as_markdown(self, meeting):
        """
        Format extracted meeting as markdown.

        Args:
            meeting: Meeting dictionary from extract_meeting_info

        Returns:
            str: Markdown formatted meeting announcement
        """
        md = []

        # Header
        org_name = meeting.get('organization_name', 'RCO Meeting')
        md.append(f"### {org_name}")

        # Date/Time/Location
        details = []
        if meeting.get('meeting_date'):
            date_str = meeting['meeting_date']
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                date_str = dt.strftime('%A, %B %d, %Y')
            except:
                pass
            details.append(f"📅 **Date:** {date_str}")

        if meeting.get('meeting_time'):
            details.append(f"🕐 **Time:** {meeting['meeting_time']}")

        if meeting.get('meeting_location'):
            location = meeting['meeting_location']
            if meeting.get('meeting_link'):
                location = f"[{location}]({meeting['meeting_link']})"
            details.append(f"📍 **Location:** {location}")

        md.append('\n'.join(details))

        # Agenda items
        agenda_items = meeting.get('agenda_items', [])
        if agenda_items:
            md.append("\n**Relevant Agenda Items:**")
            for item in agenda_items:
                emoji = {
                    'zoning_variance': '📋',
                    'development': '🏗️',
                    'bike_lane': '🚴',
                    'transit': '🚌',
                    'other': '•'
                }.get(item.get('type'), '•')

                title = item.get('title', 'Agenda item')
                if item.get('address'):
                    title = f"{title} - {item['address']}"

                md.append(f"\n{emoji} **{title}**")

                if item.get('description'):
                    md.append(f"  {item['description']}")

                if item.get('why_relevant'):
                    md.append(f"  *Why it matters:* {item['why_relevant']}")

        # Contact/RSVP
        footer = []
        if meeting.get('contact_email'):
            footer.append(f"**Contact:** {meeting['contact_email']}")
        if meeting.get('rsvp_required'):
            footer.append("⚠️ RSVP required")

        if footer:
            md.append('\n' + ' | '.join(footer))

        return '\n'.join(md)
