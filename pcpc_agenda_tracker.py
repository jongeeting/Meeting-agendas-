#!/usr/bin/env python3
"""
Philadelphia Planning Commission Meeting Agenda Tracker and Summarizer

This script automates the process of:
1. Fetching the latest PCPC meeting agenda from phila.gov
2. Extracting text from the PDF
3. Using Claude API to create housing-focused summaries
4. Saving the summary as a markdown file
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from anthropic import Anthropic


class PCPCAgendaTracker:
    """Tracks and summarizes Philadelphia Planning Commission agendas."""

    PCPC_URL = "https://www.phila.gov/departments/philadelphia-city-planning-commission/public-meetings/"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    def __init__(self, api_key=None):
        """Initialize the tracker with optional Claude API key."""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable must be set or passed to constructor"
            )
        self.client = Anthropic(api_key=self.api_key)
        self.output_dir = Path("summaries")
        self.output_dir.mkdir(exist_ok=True)

    def fetch_latest_agenda(self):
        """
        Fetch the latest agenda PDF link from the PCPC website.

        Returns:
            tuple: (pdf_url, meeting_date_str) or (None, None) if not found
        """
        print(f"Fetching PCPC public meetings page: {self.PCPC_URL}")

        try:
            response = requests.get(self.PCPC_URL, headers=self.HEADERS, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching webpage: {e}")
            return None, None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for PDF links in the agendas section
        # PDFs typically have pattern: /media/.../Month-Day-Year-PCPC-Agenda.pdf
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'PCPC-Agenda.pdf' in href or 'pcpc-agenda.pdf' in href.lower():
                # Extract date from filename or link text
                full_url = href if href.startswith('http') else f"https://www.phila.gov{href}"
                pdf_links.append((full_url, link.get_text(strip=True)))

        if not pdf_links:
            print("No agenda PDFs found on the page")
            return None, None

        # Return the first (most recent) agenda
        pdf_url, link_text = pdf_links[0]
        print(f"Found latest agenda: {link_text}")
        print(f"PDF URL: {pdf_url}")

        # Extract date from URL or link text
        date_match = re.search(r'(\w+)-(\d+)-(\d+)', pdf_url)
        meeting_date = date_match.group(0).replace('-', '_') if date_match else "unknown_date"

        return pdf_url, meeting_date

    def download_pdf(self, pdf_url, output_filename="agenda.pdf"):
        """
        Download PDF from URL.

        Args:
            pdf_url: URL of the PDF to download
            output_filename: Local filename to save PDF

        Returns:
            Path: Path to downloaded PDF or None if failed
        """
        print(f"Downloading PDF from {pdf_url}...")

        try:
            response = requests.get(pdf_url, headers=self.HEADERS, timeout=30)
            response.raise_for_status()

            pdf_path = Path(output_filename)
            pdf_path.write_bytes(response.content)
            print(f"PDF saved to {pdf_path}")
            return pdf_path

        except requests.RequestException as e:
            print(f"Error downloading PDF: {e}")
            return None

    def extract_text_from_pdf(self, pdf_path):
        """
        Extract text content from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            str: Extracted text content
        """
        print(f"Extracting text from {pdf_path}...")

        try:
            text_content = []
            reader = PdfReader(str(pdf_path))
            print(f"PDF has {len(reader.pages)} pages")

            for i, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text:
                    text_content.append(f"--- Page {i} ---\n{text}")

            full_text = "\n\n".join(text_content)
            print(f"Extracted {len(full_text)} characters of text")
            return full_text

        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return None

    def summarize_agenda(self, agenda_text, meeting_date):
        """
        Use Claude API to create housing-focused summary of agenda.

        Args:
            agenda_text: Full text of the agenda
            meeting_date: Date string for the meeting

        Returns:
            str: Markdown-formatted summary
        """
        print("Generating summary using Claude API...")

        prompt = f"""You are a housing advocate analyzing a Philadelphia Planning Commission meeting agenda.

Your task is to create a summary that helps housing advocates understand what's on the agenda and why it matters for housing production and affordability.

Please analyze this agenda and create a summary with the following format:

1. **Brief intro line** - One sentence about the meeting date and overall theme
2. **Major items** - For each significant item, include:
   - An emoji flag (🏗️ for development, 📋 for zoning, 🏘️ for housing policy, ⚖️ for legal/admin)
   - Item title and brief description
   - Why it matters for housing advocates (impact on housing production, affordability, development process, etc.)
3. **Bottom Line** - 2-3 sentence summary of key takeaways

Use a conversational, advocacy-focused tone. Be specific about addresses, zoning changes, and policy implications.

Focus on:
- Zoning bills and overlay districts
- Development proposals and land deals
- Policy changes affecting housing production
- Administrative items relevant to development process

Here's the agenda text:

{agenda_text}
"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            summary = message.content[0].text
            print("Summary generated successfully")
            return summary

        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return None

    def save_summary(self, summary, meeting_date):
        """
        Save summary to markdown file.

        Args:
            summary: Summary text to save
            meeting_date: Date string for filename

        Returns:
            Path: Path to saved file
        """
        filename = f"PCPC_Summary_{meeting_date}.md"
        output_path = self.output_dir / filename

        # Add header with metadata
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_content = f"""# Philadelphia Planning Commission Meeting Summary
**Generated:** {timestamp}
**Meeting Date:** {meeting_date.replace('_', ' ')}

---

{summary}

---

*This summary was automatically generated using Claude AI. Please review and edit as needed before sharing.*
"""

        output_path.write_text(full_content, encoding='utf-8')
        print(f"Summary saved to {output_path}")
        return output_path

    def run(self, pdf_url=None, meeting_date=None):
        """
        Run the full agenda tracking and summarization workflow.

        Args:
            pdf_url: Optional specific PDF URL (if None, fetches latest)
            meeting_date: Optional meeting date string (if None, extracts from URL)

        Returns:
            Path: Path to generated summary file or None if failed
        """
        print("=" * 60)
        print("PCPC Agenda Tracker & Summarizer")
        print("=" * 60)

        # Step 1: Get PDF URL
        if pdf_url is None:
            pdf_url, meeting_date = self.fetch_latest_agenda()
            if pdf_url is None:
                print("Failed to find latest agenda")
                return None

        # Step 2: Download PDF
        pdf_path = self.download_pdf(pdf_url)
        if pdf_path is None:
            return None

        # Step 3: Extract text
        agenda_text = self.extract_text_from_pdf(pdf_path)
        if agenda_text is None:
            return None

        # Step 4: Generate summary
        summary = self.summarize_agenda(agenda_text, meeting_date)
        if summary is None:
            return None

        # Step 5: Save summary
        output_path = self.save_summary(summary, meeting_date)

        # Cleanup
        if pdf_path.exists():
            pdf_path.unlink()
            print(f"Cleaned up temporary PDF file")

        print("=" * 60)
        print(f"SUCCESS! Summary available at: {output_path}")
        print("=" * 60)

        return output_path


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Track and summarize Philadelphia Planning Commission meeting agendas"
    )
    parser.add_argument(
        "--pdf-url",
        help="Specific PDF URL to process (if not provided, fetches latest)",
        default=None
    )
    parser.add_argument(
        "--meeting-date",
        help="Meeting date string for filename (e.g., January_15_2026)",
        default=None
    )
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (can also use ANTHROPIC_API_KEY env var)",
        default=None
    )

    args = parser.parse_args()

    try:
        tracker = PCPCAgendaTracker(api_key=args.api_key)
        result = tracker.run(pdf_url=args.pdf_url, meeting_date=args.meeting_date)

        if result:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
