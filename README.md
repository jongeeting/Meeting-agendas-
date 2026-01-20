# Philadelphia Planning Commission Agenda Tracker

Automated tool for tracking and summarizing Philadelphia City Planning Commission (PCPC) meeting agendas with a focus on housing advocacy.

## What It Does

This Python script automates the weekly task of:

1. **Fetching** the latest PCPC meeting agenda from [phila.gov](https://www.phila.gov/departments/philadelphia-city-planning-commission/public-meetings/)
2. **Extracting** text content from the PDF agenda
3. **Analyzing** the agenda using Claude AI to identify housing-relevant items
4. **Generating** a housing-focused summary in markdown format

The summary highlights:
- Zoning bills and overlay districts
- Development proposals and land deals
- Policy changes affecting housing production
- Administrative items relevant to the development process

## Setup

### Prerequisites

- Python 3.8 or higher
- Anthropic API key (get one at [console.anthropic.com](https://console.anthropic.com/))

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd Meeting-agendas-
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your API key:
```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

Alternatively, you can export the API key:
```bash
export ANTHROPIC_API_KEY='your_api_key_here'
```

## Usage

### Basic Usage (Fetch Latest Agenda)

Simply run the script to automatically fetch and summarize the most recent agenda:

```bash
python pcpc_agenda_tracker.py
```

This will:
- Fetch the latest agenda from the PCPC website
- Download and process the PDF
- Generate a summary in `summaries/PCPC_Summary_[DATE].md`

### Advanced Usage

**Process a specific PDF:**
```bash
python pcpc_agenda_tracker.py --pdf-url "https://www.phila.gov/media/.../agenda.pdf"
```

**Specify meeting date for filename:**
```bash
python pcpc_agenda_tracker.py --meeting-date "January_15_2026"
```

**Provide API key via command line:**
```bash
python pcpc_agenda_tracker.py --api-key "your_api_key_here"
```

### Weekly Workflow

For regular weekly tracking:

1. Run the script each week after the new agenda is posted (typically a few days before the meeting)
2. Find the summary in the `summaries/` directory
3. Review and edit the markdown file as needed
4. Share with your advocacy network

You can also set up a cron job or scheduled task to run this automatically.

## Output Format

The generated summary includes:

```markdown
# Philadelphia Planning Commission Meeting Summary
**Generated:** [timestamp]
**Meeting Date:** [date]

---

[Brief intro line about the meeting]

🏗️ **[Item Title]**
[Description and housing advocacy relevance]

📋 **[Item Title]**
[Description and housing advocacy relevance]

...

**Bottom Line**
[2-3 sentence summary of key takeaways]

---

*This summary was automatically generated using Claude AI. Please review and edit as needed before sharing.*
```

## Example

Testing with the January 15, 2026 agenda:

```bash
python pcpc_agenda_tracker.py
```

Output:
```
============================================================
PCPC Agenda Tracker & Summarizer
============================================================
Fetching PCPC public meetings page...
Found latest agenda: January 15, 2026
PDF URL: https://www.phila.gov/media/20260113085654/January-15-2026-PCPC-Agenda.pdf
Downloading PDF...
PDF saved to agenda.pdf
Extracting text from PDF...
PDF has 12 pages
Extracted 8,432 characters of text
Generating summary using Claude API...
Summary generated successfully
Summary saved to summaries/PCPC_Summary_January_15_2026.md
Cleaned up temporary PDF file
============================================================
SUCCESS! Summary available at: summaries/PCPC_Summary_January_15_2026.md
============================================================
```

## Troubleshooting

**"ANTHROPIC_API_KEY environment variable must be set"**
- Make sure you've created a `.env` file with your API key, or export it in your shell

**"No agenda PDFs found on the page"**
- The PCPC website structure may have changed. Check the URL and update the scraping logic if needed

**PDF extraction issues**
- Some PDFs may have images or unusual formatting. The script uses `PyPDF2` which handles most cases well

**API rate limits**
- If you're processing many agendas, be aware of Anthropic's rate limits. The script processes one agenda at a time.

## Development

### Project Structure

```
Meeting-agendas-/
├── pcpc_agenda_tracker.py  # Main script
├── requirements.txt         # Python dependencies
├── .env.example            # Example environment file
├── .gitignore             # Git ignore patterns
├── README.md              # This file
└── summaries/             # Generated summaries (created on first run)
```

### Making Changes

The script is designed to be modular:
- `PCPCAgendaTracker` class handles all functionality
- Each step (fetch, download, extract, summarize, save) is a separate method
- Easy to extend or modify for different use cases

## Contributing

Feel free to submit issues or pull requests for:
- Bug fixes
- Feature enhancements
- Support for other planning commissions
- Improved summary prompts

## License

MIT License - feel free to use and modify as needed.

## Acknowledgments

- Built with [Anthropic's Claude API](https://www.anthropic.com/)
- Uses [PyPDF2](https://pypdf2.readthedocs.io/) for PDF processing
- Targets [Philadelphia City Planning Commission](https://www.phila.gov/departments/philadelphia-city-planning-commission/)
