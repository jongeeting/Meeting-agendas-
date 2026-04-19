"""
AI-powered agenda summarization using Claude API.
"""

import os
from datetime import datetime
from pathlib import Path
from anthropic import Anthropic


class AgendaSummarizer:
    """Summarizes meeting agendas using Claude AI."""

    # Shared formatting rules appended to every prompt. Keeps outputs tight
    # and scannable — earlier versions produced walls of text because no
    # length constraints were specified and max_tokens was 4000.
    LENGTH_RULES = """
STRICT FORMATTING RULES (follow these exactly):
- Maximum 5 items in the summary. Pick the MOST consequential ones. If there
  are more, end the list with "+ N other routine items" where N is the count
  of items you excluded.
- Each item: 1-2 sentences. Be specific (address, zoning code, dollar amount)
  but cut adjectives and recap language.
- Skip items that are routine administrative business (minutes approval,
  officer reports, procedural votes) unless they are genuinely newsworthy.
- No "in summary" preamble. No closing pep talk. Bottom Line is 1-2 sentences
  MAX and only if it adds signal beyond the item list.
- Output goes directly into a reader's email. Every sentence must earn its
  place."""

    # Summarization prompts for different meeting types
    PROMPTS = {
        "housing": """You are writing a weekly email briefing for Philadelphia housing advocates, developers, and civic leaders. Readers are time-constrained professionals who pay for this content — they want the signal, not the whole agenda.

Format:
1. **One-sentence intro** — meeting body + date + the single most important thing on the agenda.
2. **Top items** (max 5), each one:
   - Emoji: 🏗️ development/construction, 📋 zoning, 🏘️ housing policy, ⚖️ legal/admin
   - **Title in bold**, then 1-2 sentences on (a) what it is and (b) why it matters. Include address, zoning code, unit count, or dollar amount when present.
3. **Bottom Line** (optional, 1-2 sentences max) — only if there's a cross-cutting theme. Skip if not.

Priority signal: zoning overlays, development proposals with substantial unit counts, policy changes affecting housing production, land deals.
Low priority (skip unless unusual): administrative reports, minor text amendments, routine approvals.""",

        "design": """You are writing a weekly email briefing on Philadelphia design review for architects, planners, and civic leaders.

Format:
1. **One-sentence intro** — meeting date + overall theme of the review.
2. **Top projects** (max 5), each:
   - **Address / project name in bold**, then 1-2 sentences on the design (scale, use, notable features) and any flagged issues (massing, setbacks, materials).
3. **Bottom Line** (optional, 1-2 sentences) — only if a design pattern repeats.

Priority: large-scale projects, prominent locations, contested designs, projects creating significant public space. Skip routine facade updates unless unusual.""",

        "historic": """You are writing a weekly email briefing on Philadelphia historic preservation for preservation advocates and property owners.

Format:
1. **One-sentence intro** — meeting date + biggest preservation call on the agenda.
2. **Top items** (max 5), each:
   - **Property address / item title in bold**, then 1-2 sentences on the preservation question (designation, demolition, alteration) and stakes.
3. **Bottom Line** (optional) — only if multiple items point to a trend.

Priority: demolition proposals, designation hearings for significant properties, denial/approval of historic-district alterations.""",

        "transportation": """You are writing a weekly email briefing on Philadelphia transit for riders, advocates, and planners.

Format:
1. **One-sentence intro** — meeting date + headline decision.
2. **Top items** (max 5), each:
   - **Item in bold**, then 1-2 sentences on the service / infrastructure / fare change and rider impact.
3. **Bottom Line** (optional) — only if a service pattern emerges.

Priority: service changes, fare policy, capital project go/no-go, accessibility. Skip budget line-items unless politically significant.""",

        "general": """Write a weekly email briefing on this Philadelphia government meeting for civic-minded readers.

Format:
1. **One-sentence intro** — meeting body + date + headline item.
2. **Top items** (max 5), each: **item title in bold**, 1-2 sentences of substance.
3. **Bottom Line** (optional, 1-2 sentences) — only if there's a through-line.""",
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

        # Get the appropriate focus-specific prompt and append shared
        # length/format rules. The rules are where verbosity gets constrained;
        # the focus prompt is where the editorial voice is set.
        prompt_template = self.PROMPTS.get(focus, self.PROMPTS["general"])

        full_prompt = f"""{prompt_template}

{self.LENGTH_RULES}

Meeting: {meeting_name}
Date: {meeting_date}

Here's the agenda text:

{agenda_text}
"""

        try:
            message = self.client.messages.create(
                # Sonnet 4.6 — tighter, faster, cheaper than 4.5 for structured
                # summarization work like this.
                model="claude-sonnet-4-6",
                # Was 4000 — way too generous for a tight weekly digest.
                # 1200 forces real editing and prevents wall-of-text output.
                max_tokens=1200,
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
