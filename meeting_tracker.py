#!/usr/bin/env python3
"""
Philadelphia Meeting Agenda Tracker

Unified system for tracking and summarizing multiple Philadelphia government
meeting agendas.

Usage:
    python meeting_tracker.py --all           # Process all enabled meetings
    python meeting_tracker.py --meeting pcpc  # Process specific meeting
    python meeting_tracker.py --list          # List all configured meetings
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

import yaml
from dotenv import load_dotenv

from shared import extract_text_from_pdf, download_pdf, AgendaSummarizer
from scrapers import PhilaGovScraper, PHDCScraper, LegistarScraper, SeptaScraper, LandBankScraper

# Load environment variables
load_dotenv()


class MeetingTracker:
    """Orchestrates meeting agenda tracking across multiple meetings."""

    # Map scraper names to classes
    SCRAPERS = {
        'phila_gov': PhilaGovScraper,
        'phdc': PHDCScraper,
        'legistar': LegistarScraper,
        'septa': SeptaScraper,
        'land_bank': LandBankScraper,
    }

    def __init__(self, config_path="config.yaml"):
        """
        Initialize the tracker.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._summarizer = None  # Lazy-loaded when needed

    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Error loading config file {self.config_path}: {e}")
            sys.exit(1)

    @property
    def summarizer(self):
        """Lazy-load the summarizer (requires API key)."""
        if self._summarizer is None:
            self._summarizer = AgendaSummarizer()
        return self._summarizer

    def list_meetings(self):
        """List all configured meetings."""
        print("=" * 60)
        print("Configured Meetings")
        print("=" * 60)

        for meeting_id, meeting_config in self.config['meetings'].items():
            status = "✓ ENABLED" if meeting_config.get('enabled', False) else "✗ DISABLED"
            scraper_type = meeting_config.get('scraper', 'unknown')
            implemented = "✓" if scraper_type in self.SCRAPERS else "✗ (not implemented)"

            print(f"\n{meeting_id}:")
            print(f"  Name:    {meeting_config['name']}")
            print(f"  Status:  {status}")
            print(f"  Scraper: {scraper_type} {implemented}")
            print(f"  Focus:   {meeting_config.get('focus', 'general')}")

    def process_meeting(self, meeting_id):
        """
        Process a single meeting.

        Args:
            meeting_id: ID of the meeting from config (e.g., 'pcpc')

        Returns:
            bool: True if successful, False otherwise
        """
        # Get meeting config
        meeting_config = self.config['meetings'].get(meeting_id)
        if not meeting_config:
            print(f"Error: Meeting '{meeting_id}' not found in config")
            return False

        # Check if scraper is implemented
        scraper_type = meeting_config.get('scraper')
        if scraper_type not in self.SCRAPERS:
            print(f"Error: Scraper '{scraper_type}' not yet implemented")
            print(f"Available scrapers: {', '.join(self.SCRAPERS.keys())}")
            return False

        print("=" * 60)
        print(f"Processing: {meeting_config['name']}")
        print("=" * 60)

        # Initialize scraper
        scraper_class = self.SCRAPERS[scraper_type]
        scraper = scraper_class(meeting_config)

        # Fetch latest agenda
        pdf_url, meeting_date = scraper.fetch_latest_agenda()
        if not pdf_url:
            print(f"Failed to find agenda for {meeting_id}")
            return False

        # Download PDF
        pdf_path = download_pdf(pdf_url, f"{meeting_id}_agenda.pdf")
        if not pdf_path:
            return False

        # Extract text
        agenda_text = extract_text_from_pdf(pdf_path)
        if not agenda_text:
            return False

        # Generate summary
        focus = meeting_config.get('focus', 'general')
        summary = self.summarizer.summarize(
            agenda_text,
            meeting_date,
            focus=focus,
            meeting_name=meeting_config['name']
        )
        if not summary:
            return False

        # Save summary
        output_dir = self.config.get('settings', {}).get('output_dir', 'summaries')
        output_path = self.summarizer.save_summary(
            summary,
            meeting_date,
            meeting_type=meeting_id,
            output_dir=output_dir
        )

        # Save JSON metadata for weekly digest
        if output_path:
            json_data = {
                'meeting_type': meeting_id,
                'meeting_name': meeting_config['name'],
                'meeting_date': meeting_date,
                'pdf_url': pdf_url,
                'summary': summary,
                'focus': focus,
                'timestamp': datetime.now().isoformat(),
                'source': 'web_scraper'
            }

            # Save JSON file in same directory as markdown
            json_path = output_path.with_suffix('.json')
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2)
                print(f"Metadata saved to {json_path}")
            except Exception as e:
                print(f"Warning: Failed to save JSON metadata: {e}")

        # Cleanup PDF if configured
        if not self.config.get('settings', {}).get('save_pdfs', False):
            if pdf_path.exists():
                pdf_path.unlink()
                print(f"Cleaned up temporary PDF file")

        if output_path:
            print("=" * 60)
            print(f"SUCCESS! Summary available at: {output_path}")
            print("=" * 60)
            return True

        return False

    def process_all(self):
        """Process all enabled meetings."""
        enabled_meetings = [
            meeting_id for meeting_id, config in self.config['meetings'].items()
            if config.get('enabled', False) and config.get('scraper') in self.SCRAPERS
        ]

        if not enabled_meetings:
            print("No enabled meetings with implemented scrapers found")
            return

        print(f"\nProcessing {len(enabled_meetings)} enabled meetings...")
        print(f"Meetings: {', '.join(enabled_meetings)}\n")

        results = {}
        for meeting_id in enabled_meetings:
            try:
                success = self.process_meeting(meeting_id)
                results[meeting_id] = success
                print()  # Blank line between meetings
            except Exception as e:
                print(f"Error processing {meeting_id}: {e}")
                results[meeting_id] = False

        # Print summary
        print("=" * 60)
        print("Batch Processing Summary")
        print("=" * 60)
        for meeting_id, success in results.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"{meeting_id:20} {status}")

        success_count = sum(1 for s in results.values() if s)
        print(f"\nCompleted: {success_count}/{len(results)} successful")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Track and summarize Philadelphia government meeting agendas"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Process all enabled meetings"
    )
    group.add_argument(
        "--meeting",
        help="Process specific meeting (e.g., pcpc, cdr)"
    )
    group.add_argument(
        "--list",
        action="store_true",
        help="List all configured meetings"
    )

    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )

    args = parser.parse_args()

    try:
        tracker = MeetingTracker(config_path=args.config)

        if args.list:
            tracker.list_meetings()
        elif args.all:
            tracker.process_all()
        elif args.meeting:
            success = tracker.process_meeting(args.meeting)
            sys.exit(0 if success else 1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
