#!/usr/bin/env python3
"""
Weekly Meeting Digest Generator

Combines RCO meetings and official city meetings into a single markdown digest.

Usage:
    python weekly_digest.py                    # Generate digest for past 7 days
    python weekly_digest.py --days 14          # Custom time range
    python weekly_digest.py --output email.md  # Custom output file
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


class WeeklyDigestGenerator:
    """Generates weekly digest from both RCO and official meeting sources."""

    def __init__(self, days=7):
        """
        Initialize generator.

        Args:
            days: Number of days to look back
        """
        self.days = days
        self.cutoff_date = datetime.now() - timedelta(days=days)

    def find_recent_summaries(self):
        """Find all JSON summaries from the past N days."""
        summaries_dir = Path("summaries")

        rco_files = []
        official_files = []

        if summaries_dir.exists():
            # Find RCO meeting files
            rco_dir = summaries_dir / "rco"
            if rco_dir.exists():
                for json_file in rco_dir.glob("meetings_*.json"):
                    # Parse timestamp from filename: meetings_YYYYMMDD_HHMMSS.json
                    try:
                        timestamp_str = json_file.stem.split('_')[1] + json_file.stem.split('_')[2]
                        file_date = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
                        if file_date >= self.cutoff_date:
                            rco_files.append(json_file)
                    except (IndexError, ValueError):
                        continue

            # Find official meeting files
            for json_file in summaries_dir.rglob("*.json"):
                if "rco" not in str(json_file):
                    # Check file modification time
                    if json_file.stat().st_mtime >= self.cutoff_date.timestamp():
                        official_files.append(json_file)

        return rco_files, official_files

    def load_rco_meetings(self, files):
        """Load RCO meetings from JSON files and deduplicate."""
        meetings = []
        seen = set()  # Track unique meetings by email_id

        for file_path in files:
            try:
                with open(file_path) as f:
                    data = json.load(f)
                    for meeting in data:
                        # Use email_id as unique identifier
                        email_id = meeting.get('email_id')
                        if email_id and email_id not in seen:
                            meeting['source'] = 'rco'
                            meetings.append(meeting)
                            seen.add(email_id)
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")

        return meetings

    def load_official_meetings(self, files):
        """Load official meetings from JSON files."""
        meetings = []

        for file_path in files:
            try:
                with open(file_path) as f:
                    data = json.load(f)
                    # Official meetings have different structure
                    data['source'] = 'official'
                    meetings.append(data)
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")

        return meetings

    def format_rco_meeting_md(self, meeting):
        """Format a single RCO meeting as markdown."""
        md = []

        # Header
        org = meeting.get('organization_name', 'Unknown Organization')
        date = meeting.get('meeting_date', 'TBD')
        time = meeting.get('meeting_time', 'TBD')

        md.append(f"### {org}")
        md.append(f"**When:** {date} at {time}")

        # Location
        location = meeting.get('meeting_location') or meeting.get('meeting_link', 'Location TBD')
        md.append(f"**Where:** {location}")

        # Meeting link if available
        if meeting.get('meeting_link'):
            md.append(f"**Link:** {meeting['meeting_link']}")

        # Agenda items
        agenda_items = meeting.get('agenda_items', [])
        if agenda_items:
            md.append("\n**Key Agenda Items:**")
            for item in agenda_items:
                title = item.get('title', 'Untitled')
                description = item.get('description', '')
                address = item.get('address')

                md.append(f"\n**{title}**")
                if address:
                    md.append(f"*Location:* {address}")
                if description:
                    md.append(f"{description}")

        # Contact
        if meeting.get('contact_email'):
            md.append(f"\n**Contact:** {meeting['contact_email']}")

        return "\n".join(md)

    def format_official_meeting_md(self, meeting):
        """Format an official meeting as markdown."""
        md = []

        # Header
        org = meeting.get('organization', 'Official Meeting')
        date = meeting.get('date', 'TBD')

        md.append(f"### {org}")
        md.append(f"**When:** {date}")

        # Location/details
        if meeting.get('location'):
            md.append(f"**Where:** {meeting['location']}")

        # Source document
        if meeting.get('source_url'):
            md.append(f"**Source:** {meeting['source_url']}")

        # Summary
        if meeting.get('summary'):
            md.append(f"\n{meeting['summary']}")

        # Agenda items
        if meeting.get('agenda_items'):
            md.append("\n**Key Items:**")
            for item in meeting['agenda_items']:
                md.append(f"- {item}")

        return "\n".join(md)

    def generate_digest(self, output_path="weekly_digest.md"):
        """Generate the weekly digest markdown file."""
        print(f"📋 Generating weekly digest for past {self.days} days...")

        # Find all recent summaries
        rco_files, official_files = self.find_recent_summaries()

        print(f"Found {len(rco_files)} RCO meeting files")
        print(f"Found {len(official_files)} official meeting files")

        # Load meetings
        rco_meetings = self.load_rco_meetings(rco_files)
        official_meetings = self.load_official_meetings(official_files)

        print(f"Loaded {len(rco_meetings)} RCO meetings")
        print(f"Loaded {len(official_meetings)} official meetings")

        # Sort by date
        def parse_date(meeting):
            date_str = meeting.get('meeting_date') or meeting.get('date', '9999-12-31')
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except:
                return datetime.max

        rco_meetings.sort(key=parse_date)
        official_meetings.sort(key=parse_date)

        # Generate markdown
        md_lines = []

        # Header
        start_date = (datetime.now() - timedelta(days=self.days)).strftime("%B %d")
        end_date = datetime.now().strftime("%B %d, %Y")

        md_lines.append(f"# Philadelphia Housing & Development Meetings")
        md_lines.append(f"## {start_date} - {end_date}")
        md_lines.append("")
        md_lines.append("Weekly digest of upcoming meetings relevant to housing advocates, compiled from neighborhood organizations and city agencies.")
        md_lines.append("")

        # RCO Meetings Section
        if rco_meetings:
            md_lines.append("## Neighborhood Organization Meetings")
            md_lines.append("")
            md_lines.append(f"Found {len(rco_meetings)} relevant neighborhood meetings:")
            md_lines.append("")

            for meeting in rco_meetings:
                md_lines.append(self.format_rco_meeting_md(meeting))
                md_lines.append("")
                md_lines.append("---")
                md_lines.append("")

        # Official Meetings Section
        if official_meetings:
            md_lines.append("## Official City Meetings")
            md_lines.append("")
            md_lines.append(f"Found {len(official_meetings)} official meetings:")
            md_lines.append("")

            for meeting in official_meetings:
                md_lines.append(self.format_official_meeting_md(meeting))
                md_lines.append("")
                md_lines.append("---")
                md_lines.append("")

        # Footer
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("*This digest was automatically generated from email monitoring and web scraping.*")

        # Write to file
        output_file = Path(output_path)
        output_file.write_text("\n".join(md_lines))

        print(f"\n✓ Digest generated: {output_file}")
        print(f"  - {len(rco_meetings)} RCO meetings")
        print(f"  - {len(official_meetings)} official meetings")

        return output_file


def main():
    parser = argparse.ArgumentParser(description="Generate weekly meeting digest")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back (default: 7)"
    )
    parser.add_argument(
        "--output",
        default="weekly_digest.md",
        help="Output markdown file (default: weekly_digest.md)"
    )

    args = parser.parse_args()

    generator = WeeklyDigestGenerator(days=args.days)
    generator.generate_digest(output_path=args.output)


if __name__ == "__main__":
    main()
