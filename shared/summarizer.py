"""
AI-powered agenda summarization using Claude API.
"""

import os
from datetime import datetime
from pathlib import Path
from anthropic import Anthropic


class AgendaSummarizer:
    """Summarizes meeting agendas using Claude AI."""

    # Summarization prompts for different meeting types
    PROMPTS = {
        "housing": """You are a housing advocate analyzing a meeting agenda.

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
- Administrative items relevant to development process""",

        "design": """You are an urban design professional analyzing a design review agenda.

Create a summary focused on:
- Major development projects under review
- Design guidelines and standards being discussed
- Public space and streetscape improvements
- Architectural significance and context
- Community impact of proposed designs

Format:
1. Brief intro about the meeting
2. Project-by-project summary with design highlights
3. Overall themes and notable items""",

        "historic": """You are a preservation advocate analyzing a historical commission agenda.

Create a summary focused on:
- Properties seeking historical designation
- Demolition requests and their implications
- Renovation proposals for historic buildings
- Policy changes affecting historic preservation
- Community heritage considerations

Format:
1. Brief intro
2. Item-by-item analysis with preservation context
3. Key preservation issues at stake""",

        "transportation": """You are a transit advocate analyzing transportation meeting minutes.

Create a summary focused on:
- Service changes and route modifications
- Capital projects and infrastructure
- Fare and policy changes
- Accessibility improvements
- Budget and funding allocations

Format:
1. Brief overview
2. Major items with transit impact analysis
3. Key takeaways for riders and advocates""",

        "general": """Analyze this meeting agenda and create a clear, concise summary.

Format:
1. Brief intro about the meeting
2. Major agenda items with context
3. Key takeaways and action items"""
    }

    def __init__(self, api_key=None):
        """
        Initialize the summarizer.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable must be set or passed to constructor"
            )
        self.client = Anthropic(api_key=self.api_key)

    def summarize(self, agenda_text, meeting_date, focus="general", meeting_name="Meeting"):
        """
        Generate AI summary of agenda.

        Args:
            agenda_text: Full text of the agenda
            meeting_date: Date string for the meeting
            focus: Type of focus ("housing", "design", "historic", "transportation", "general")
            meeting_name: Name of the meeting body

        Returns:
            str: Markdown-formatted summary or None if failed
        """
        print(f"Generating summary using Claude API (focus: {focus})...")

        # Get the appropriate prompt
        prompt_template = self.PROMPTS.get(focus, self.PROMPTS["general"])

        full_prompt = f"""{prompt_template}

Meeting: {meeting_name}
Date: {meeting_date}

Here's the agenda text:

{agenda_text}
"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )

            summary = message.content[0].text
            print("Summary generated successfully")
            return summary

        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return None

    def save_summary(self, summary, meeting_date, meeting_type="meeting", output_dir="summaries"):
        """
        Save summary to markdown file.

        Args:
            summary: Summary text to save
            meeting_date: Date string for the meeting
            meeting_type: Type/name of meeting (for folder organization)
            output_dir: Base directory for summaries

        Returns:
            Path: Path to saved file or None if failed
        """
        # Create output directory structure
        base_dir = Path(output_dir)
        meeting_dir = base_dir / meeting_type
        meeting_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"{meeting_type.upper()}_Summary_{meeting_date}.md"
        output_path = meeting_dir / filename

        # Add header with metadata
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_content = f"""# {meeting_type.upper()} Meeting Summary
**Generated:** {timestamp}
**Meeting Date:** {meeting_date.replace('_', ' ')}

---

{summary}

---

*This summary was automatically generated using Claude AI. Please review and edit as needed before sharing.*
"""

        try:
            output_path.write_text(full_content, encoding='utf-8')
            print(f"Summary saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Error saving summary: {e}")
            return None
