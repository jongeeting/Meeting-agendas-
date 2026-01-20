# Quick Start Guide

Get up and running with the PCPC Agenda Tracker in 5 minutes.

## 1. Get Your API Key

Sign up for an Anthropic API key at [console.anthropic.com](https://console.anthropic.com/)

## 2. Set Up Your Environment

```bash
# Create .env file
echo "ANTHROPIC_API_KEY=your_actual_api_key_here" > .env

# Install dependencies
pip install -r requirements.txt
```

Or use the provided helper script:

```bash
# On Linux/Mac
chmod +x run_tracker.sh
./run_tracker.sh
```

## 3. Run the Tracker

```bash
python pcpc_agenda_tracker.py
```

That's it! The script will:
- Fetch the latest PCPC meeting agenda
- Download and extract text from the PDF
- Generate a housing-focused summary using Claude AI
- Save the result to `summaries/PCPC_Summary_[DATE].md`

## Example Output

```
============================================================
PCPC Agenda Tracker & Summarizer
============================================================
Fetching PCPC public meetings page...
Found latest agenda: January 15, 2026
PDF URL: https://www.phila.gov/media/.../January-15-2026-PCPC-Agenda.pdf
Downloading PDF...
Extracting text from PDF...
PDF has 12 pages
Generating summary using Claude API...
Summary saved to summaries/PCPC_Summary_January_15_2026.md
============================================================
SUCCESS! Summary available at: summaries/PCPC_Summary_January_15_2026.md
============================================================
```

## Weekly Workflow

1. **Wednesday/Thursday**: New agenda typically posted
2. **Run the tracker**: `python pcpc_agenda_tracker.py`
3. **Review the summary**: Open the markdown file in `summaries/`
4. **Edit as needed**: Add your insights, adjust emphasis
5. **Share with your network**: Email, Slack, social media, etc.

## Troubleshooting

**Script can't find API key?**
```bash
export ANTHROPIC_API_KEY='your_key_here'
```

**Dependencies missing?**
```bash
pip install -r requirements.txt
```

**Test your setup:**
```bash
python test_installation.py
```

## Next Steps

- Check out the full [README.md](README.md) for advanced usage
- Customize the summary prompt in `pcpc_agenda_tracker.py` (line 141)
- Set up a cron job to run automatically each week
- Add this to your housing advocacy toolkit

Happy tracking! 🏘️
