#!/usr/bin/env python3
"""
RCO Newsletter Monitor

Monitors Gmail inbox for RCO (Registered Community Organization) newsletters,
identifies relevant meeting announcements, and generates a digest.

Usage:
    python rco_monitor.py --check          # Check for new emails
    python rco_monitor.py --digest weekly  # Generate weekly digest
    python rco_monitor.py --setup          # Interactive setup
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yaml
from dotenv import load_dotenv

from email_monitor import GmailClient, EmailClassifier, MeetingExtractor

# Load environment variables
load_dotenv()


class RCOMonitor:
    """Monitors RCO newsletters and generates meeting digests."""

    def __init__(self, config_path="config.yaml"):
        """
        Initialize monitor.

        Args:
            config_path: Path to config file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

        # Get RCO config
        self.rco_config = self.config.get('rco_monitoring', {})

        # Initialize components
        self.gmail = None
        self.classifier = None
        self.extractor = None

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
        print("RCO Newsletter Monitor - Setup")
        print("=" * 60)
        print()

        print("This tool monitors a Gmail inbox for RCO newsletters")
        print("and generates digests of relevant meetings.")
        print()

        # Check for Gmail credentials
        gmail_creds = self.rco_config.get('gmail_credentials', 'gmail-credentials.json')
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
            self.classifier = EmailClassifier()
            self.extractor = MeetingExtractor()
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
        print("1. Subscribe to RCO newsletters with your Gmail account")
        print("2. Run: python rco_monitor.py --check")
        print("3. Generate digest: python rco_monitor.py --digest weekly")
        print()

        return True

    def check_emails(self, days_back=7, dry_run=False):
        """
        Check Gmail for new RCO newsletters.

        Args:
            days_back: How many days to look back
            dry_run: If True, don't save results

        Returns:
            list: List of relevant meetings found
        """
        print("=" * 60)
        print(f"Checking emails from last {days_back} days")
        print("=" * 60)
        print()

        # Initialize if needed
        if not self.gmail:
            gmail_creds = self.rco_config.get('gmail_credentials', 'gmail-credentials.json')
            self.gmail = GmailClient(credentials_path=gmail_creds)
            if not self.gmail.authenticate():
                print("✗ Gmail authentication failed")
                return []

        if not self.classifier:
            self.classifier = EmailClassifier()

        if not self.extractor:
            self.extractor = MeetingExtractor()

        # Fetch emails
        print("📥 Fetching emails...")
        search_query = self.rco_config.get('search_query', None)
        emails = self.gmail.fetch_emails(
            days_back=days_back,
            max_results=self.rco_config.get('max_emails', 500),
            query=search_query
        )

        if not emails:
            print("No emails found")
            return []

        print(f"Found {len(emails)} emails")
        print()

        # Classify emails
        print("🤖 Classifying emails with Claude AI...")

        def progress_callback(i, total, email):
            if i % 10 == 0 or i == total:
                print(f"  Processed {i}/{total} emails...")

        classified = self.classifier.classify_batch(emails, callback=progress_callback)
        relevant = self.classifier.filter_relevant(classified)

        print(f"Found {len(relevant)} relevant meeting announcements")
        print()

        if not relevant:
            return []

        # Extract meeting details
        print("📋 Extracting meeting details...")
        relevant_emails = [email for email, _ in relevant]
        meetings = self.extractor.extract_batch(relevant_emails, callback=progress_callback)

        print(f"Extracted {len(meetings)} meetings")
        print()

        # Save results if not dry run
        if not dry_run:
            self._save_meetings(meetings)

            # Optionally label emails in Gmail
            if self.rco_config.get('label_processed', False):
                print("🏷️  Labeling processed emails...")
                for email, _ in relevant:
                    self.gmail.add_label(email['id'], 'RCO-Meeting')

        return meetings

    def _save_meetings(self, meetings):
        """
        Save extracted meetings to file.

        Args:
            meetings: List of meeting dictionaries
        """
        output_dir = Path(self.rco_config.get('output_dir', 'summaries/rco'))
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save as JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = output_dir / f'meetings_{timestamp}.json'

        import json
        with open(json_file, 'w') as f:
            json.dump(meetings, f, indent=2)

        print(f"💾 Saved {len(meetings)} meetings to {json_file}")

    def generate_digest(self, period='weekly'):
        """
        Generate meeting digest.

        Args:
            period: 'daily', 'weekly', or 'monthly'

        Returns:
            Path: Path to generated digest
        """
        print("=" * 60)
        print(f"Generating {period} RCO meeting digest")
        print("=" * 60)
        print()

        # Load recent meetings
        output_dir = Path(self.rco_config.get('output_dir', 'summaries/rco'))
        if not output_dir.exists():
            print("No meetings data found. Run --check first.")
            return None

        # Find all meeting JSON files
        import json
        all_meetings = []

        for json_file in output_dir.glob('meetings_*.json'):
            with open(json_file) as f:
                meetings = json.load(f)
                all_meetings.extend(meetings)

        if not all_meetings:
            print("No meetings found")
            return None

        # Filter by date range
        if period == 'weekly':
            cutoff = datetime.now() + timedelta(days=7)
        elif period == 'monthly':
            cutoff = datetime.now() + timedelta(days=30)
        else:  # daily
            cutoff = datetime.now() + timedelta(days=1)

        # Sort by date
        upcoming = []
        for meeting in all_meetings:
            meeting_date = meeting.get('meeting_date')
            if meeting_date:
                try:
                    dt = datetime.strptime(meeting_date, '%Y-%m-%d')
                    if dt <= cutoff:
                        upcoming.append((dt, meeting))
                except:
                    pass

        upcoming.sort(key=lambda x: x[0])

        # Generate markdown
        if not self.extractor:
            self.extractor = MeetingExtractor()

        md_lines = [
            f"# RCO Meetings Digest - {period.title()}",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Period:** Next {period}",
            "",
            "---",
            ""
        ]

        # Group by date
        current_date = None
        for dt, meeting in upcoming:
            date_str = dt.strftime('%A, %B %d, %Y')

            if date_str != current_date:
                current_date = date_str
                md_lines.append(f"\n## {date_str}\n")

            # Format meeting
            meeting_md = self.extractor.format_as_markdown(meeting)
            md_lines.append(meeting_md)
            md_lines.append("")

        md_lines.append("---")
        md_lines.append("*Generated by RCO Newsletter Monitor*")

        # Save digest
        digest_file = output_dir / f'digest_{period}_{datetime.now().strftime("%Y%m%d")}.md'
        digest_file.write_text('\n'.join(md_lines))

        print(f"✓ Digest generated: {digest_file}")
        print(f"  {len(upcoming)} meetings included")

        return digest_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor RCO newsletters and generate meeting digests"
    )

    parser.add_argument(
        '--setup',
        action='store_true',
        help="Run interactive setup"
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help="Check for new emails and extract meetings"
    )

    parser.add_argument(
        '--digest',
        choices=['daily', 'weekly', 'monthly'],
        help="Generate meeting digest"
    )

    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help="Days to look back when checking emails (default: 7)"
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Don't save results (for testing)"
    )

    args = parser.parse_args()

    if not (args.setup or args.check or args.digest):
        parser.print_help()
        sys.exit(1)

    try:
        monitor = RCOMonitor()

        if args.setup:
            success = monitor.setup()
            sys.exit(0 if success else 1)

        if args.check:
            meetings = monitor.check_emails(days_back=args.days, dry_run=args.dry_run)
            print(f"\n✓ Found {len(meetings)} relevant meetings")

        if args.digest:
            digest_file = monitor.generate_digest(period=args.digest)
            if digest_file:
                print(f"\n✓ Digest saved to: {digest_file}")

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
