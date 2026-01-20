#!/usr/bin/env python3
"""
Official Meetings Email Monitor

Monitors Gmail for official city meeting notifications (Land Bank, SEPTA, etc.),
extracts PDFs from emails, and generates summaries in the same format as scraped meetings.

This is separate from the RCO monitor - this tracks official city government meetings
while RCO monitor tracks neighborhood organization newsletters.

Usage:
    python official_meetings_monitor.py --setup          # Interactive setup
    python official_meetings_monitor.py --check          # Check for new meeting emails
    python official_meetings_monitor.py --process        # Process all pending emails
"""

import argparse
import sys
import re
import tempfile
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

from email_monitor import GmailClient
from shared.pdf_utils import download_pdf, extract_text_from_pdf
from shared.summarizer import AgendaSummarizer

# Load environment variables
load_dotenv()


class OfficialMeetingsMonitor:
    """Monitors official city meeting notifications via email."""

    def __init__(self, config_path="config.yaml"):
        """
        Initialize monitor.

        Args:
            config_path: Path to config file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

        # Get official meetings config
        self.meetings_config = self.config.get('official_meetings_email', {})

        # Initialize components
        self.gmail = None
        self.summarizer = None

    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def setup(self):
        """Interactive setup wizard."""
        print("=" * 60)
        print("Official Meetings Email Monitor - Setup")
        print("=" * 60)
        print()

        print("This tool monitors Gmail for official city meeting notifications")
        print("(Land Bank, SEPTA, etc.) and generates summaries.")
        print()
        print("NOTE: This is separate from the RCO monitor.")
        print("  - RCO monitor: Neighborhood organization newsletters")
        print("  - This monitor: Official city government meetings")
        print()

        # Check for Gmail credentials
        gmail_creds = self.meetings_config.get('gmail_credentials', 'gmail-credentials.json')
        if not Path(gmail_creds).exists():
            print("⚠️  Gmail credentials not found!")
            print()
            print("You need to:")
            print("1. Go to Google Cloud Console")
            print("2. Create OAuth2 credentials for Gmail API")
            print("3. Download as 'gmail-credentials.json'")
            print("4. Place in this directory")
            print()
            print("See GMAIL_SETUP.md for detailed instructions")
            return False

        # Try to authenticate
        print("Testing Gmail authentication...")
        self.gmail = GmailClient(credentials_path=gmail_creds)
        if not self.gmail.authenticate():
            print("✗ Gmail authentication failed")
            return False

        print("✓ Gmail authentication successful")
        print()

        # Check API key
        try:
            self.summarizer = AgendaSummarizer()
            print("✓ Claude API key found")
        except ValueError:
            print("✗ ANTHROPIC_API_KEY not set in .env file")
            return False

        print()
        print("=" * 60)
        print("✓ Setup complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Create a Gmail filter to label meeting emails as 'Official-Meetings'")
        print("2. Subscribe to meeting notifications (Land Bank, SEPTA, etc.)")
        print("3. Run: python official_meetings_monitor.py --check")
        print()
        print("Gmail filter example:")
        print("  From: (landbank OR septa OR phila.gov)")
        print("  Has the words: (meeting OR agenda OR board)")
        print("  -> Apply label: Official-Meetings")
        print()

        return True

    def check_emails(self, days_back=30, dry_run=False):
        """
        Check Gmail for new official meeting notifications.

        Args:
            days_back: How many days to look back
            dry_run: If True, don't save results

        Returns:
            list: List of processed meetings
        """
        print("=" * 60)
        print(f"Checking for official meeting emails (last {days_back} days)")
        print("=" * 60)
        print()

        # Initialize if needed
        if not self.gmail:
            gmail_creds = self.meetings_config.get('gmail_credentials', 'gmail-credentials.json')
            self.gmail = GmailClient(credentials_path=gmail_creds)
            if not self.gmail.authenticate():
                print("✗ Gmail authentication failed")
                return []

        if not self.summarizer:
            self.summarizer = AgendaSummarizer()

        # Fetch emails with Official-Meetings label
        print("📥 Fetching emails with 'Official-Meetings' label...")

        # Use label in query
        label_name = self.meetings_config.get('gmail_label', 'Official-Meetings')
        search_query = f'label:{label_name}'

        emails = self.gmail.fetch_emails(
            days_back=days_back,
            max_results=self.meetings_config.get('max_emails', 100),
            query=search_query
        )

        if not emails:
            print("No emails found with 'Official-Meetings' label")
            print()
            print("Make sure you:")
            print("1. Created a Gmail filter to label meeting emails")
            print("2. Have subscribed to meeting notifications")
            return []

        print(f"Found {len(emails)} emails")
        print()

        # Process each email
        processed = []
        for i, email in enumerate(emails, 1):
            print(f"\n[{i}/{len(emails)}] Processing: {email['subject']}")
            print(f"  From: {email['sender']}")

            result = self._process_email(email, dry_run=dry_run)
            if result:
                processed.append(result)

        print()
        print(f"✓ Successfully processed {len(processed)} meetings")

        return processed

    def _process_email(self, email, dry_run=False):
        """
        Process a single meeting email.

        Args:
            email: Email dict from Gmail
            dry_run: If True, don't save results

        Returns:
            dict: Processed meeting info or None
        """
        # Try to identify meeting type from sender/subject
        meeting_info = self._identify_meeting(email)
        if not meeting_info:
            print("  ⚠️  Could not identify meeting type")
            return None

        meeting_type = meeting_info['type']
        meeting_name = meeting_info['name']
        focus = meeting_info.get('focus', 'general')

        print(f"  📋 Identified as: {meeting_name}")

        # Extract PDF links from email body
        pdf_links = self._extract_pdf_links(email['body'])

        if not pdf_links:
            print("  ⚠️  No PDF links found in email")
            return None

        print(f"  📎 Found {len(pdf_links)} PDF link(s)")

        # Download and process first PDF (usually the agenda)
        pdf_url = pdf_links[0]
        print(f"  ⬇️  Downloading PDF...")

        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            download_pdf(pdf_url, tmp_path)

            # Extract text
            print("  📄 Extracting text from PDF...")
            agenda_text = extract_text_from_pdf(tmp_path)

            if not agenda_text or len(agenda_text) < 100:
                print("  ⚠️  PDF text extraction failed or too short")
                Path(tmp_path).unlink(missing_ok=True)
                return None

            # Extract or infer meeting date
            meeting_date = self._extract_date(email, agenda_text)

            if not dry_run:
                # Generate summary
                print(f"  🤖 Generating summary with Claude AI...")
                summary = self.summarizer.summarize(
                    agenda_text,
                    meeting_date,
                    focus=focus,
                    meeting_name=meeting_name
                )

                if summary:
                    # Save summary
                    output_path = self.summarizer.save_summary(
                        summary,
                        meeting_date,
                        meeting_type=meeting_type,
                        output_dir="summaries"
                    )
                    print(f"  ✓ Saved summary to: {output_path}")
                else:
                    print("  ✗ Failed to generate summary")
                    Path(tmp_path).unlink(missing_ok=True)
                    return None

            # Clean up
            Path(tmp_path).unlink(missing_ok=True)

            return {
                'meeting_type': meeting_type,
                'meeting_name': meeting_name,
                'meeting_date': meeting_date,
                'pdf_url': pdf_url,
                'email_subject': email['subject']
            }

        except Exception as e:
            print(f"  ✗ Error processing email: {e}")
            if 'tmp_path' in locals():
                Path(tmp_path).unlink(missing_ok=True)
            return None

    def _identify_meeting(self, email):
        """
        Identify meeting type from email sender/subject.

        Args:
            email: Email dict

        Returns:
            dict: Meeting info with type, name, focus or None
        """
        sender = email['sender'].lower()
        subject = email['subject'].lower()
        combined = f"{sender} {subject}"

        # Define meeting patterns
        patterns = {
            'land_bank': {
                'keywords': ['land bank', 'landbank', 'phillylandbank'],
                'name': 'Philadelphia Land Bank',
                'focus': 'housing'
            },
            'septa': {
                'keywords': ['septa', 'southeastern pennsylvania transportation'],
                'name': 'SEPTA Board',
                'focus': 'transportation'
            },
            'zba': {
                'keywords': ['zoning board', 'zba', 'board of adjustment'],
                'name': 'Zoning Board of Adjustment',
                'focus': 'housing'
            }
        }

        for meeting_type, info in patterns.items():
            if any(keyword in combined for keyword in info['keywords']):
                return {
                    'type': meeting_type,
                    'name': info['name'],
                    'focus': info['focus']
                }

        return None

    def _extract_pdf_links(self, email_body):
        """
        Extract PDF URLs from email body.

        Args:
            email_body: Email body text

        Returns:
            list: List of PDF URLs
        """
        # Look for URLs ending in .pdf
        pdf_pattern = r'https?://[^\s<>"]+?\.pdf'
        matches = re.findall(pdf_pattern, email_body, re.IGNORECASE)

        # Remove duplicates while preserving order
        seen = set()
        unique_matches = []
        for match in matches:
            if match not in seen:
                seen.add(match)
                unique_matches.append(match)

        return unique_matches

    def _extract_date(self, email, agenda_text):
        """
        Extract meeting date from email or agenda text.

        Args:
            email: Email dict
            agenda_text: Text extracted from PDF

        Returns:
            str: Date string in format YYYY_MM_DD or YYYY_Month_DD
        """
        # Try to find date in subject
        subject = email['subject']

        # Pattern: Month DD, YYYY or MM/DD/YYYY
        date_patterns = [
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',  # January 15, 2024
            r'(\d{1,2})/(\d{1,2})/(\d{4})',     # 1/15/2024
            r'(\d{4})-(\d{1,2})-(\d{1,2})',     # 2024-01-15
        ]

        for pattern in date_patterns:
            match = re.search(pattern, subject)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    # Try to format as YYYY_MM_DD
                    try:
                        if groups[0].isalpha():  # Month name
                            return f"{groups[2]}_{groups[0]}_{groups[1]}"
                        else:  # Numeric date
                            return f"{groups[0]}_{groups[1]}_{groups[2]}"
                    except:
                        pass

        # Fallback: use email date
        email_date = email.get('date', '')
        if email_date:
            try:
                # Parse email date and format
                dt = datetime.strptime(email_date.split(',')[1].strip()[:20], '%d %b %Y %H:%M:%S')
                return dt.strftime('%Y_%m_%d')
            except:
                pass

        # Last resort: use current date
        return datetime.now().strftime('%Y_%m_%d')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor official city meeting email notifications"
    )

    parser.add_argument(
        '--setup',
        action='store_true',
        help="Run interactive setup"
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help="Check for new meeting emails and process them"
    )

    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help="Days to look back when checking emails (default: 30)"
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Don't save results (for testing)"
    )

    args = parser.parse_args()

    if not (args.setup or args.check):
        parser.print_help()
        sys.exit(1)

    try:
        monitor = OfficialMeetingsMonitor()

        if args.setup:
            success = monitor.setup()
            sys.exit(0 if success else 1)

        if args.check:
            meetings = monitor.check_emails(days_back=args.days, dry_run=args.dry_run)
            print(f"\n✓ Processed {len(meetings)} meetings")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
