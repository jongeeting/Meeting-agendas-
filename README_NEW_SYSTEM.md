# Philadelphia Meeting Agenda Tracker - Multi-Meeting System

**🎉 NEW: Unified system for tracking 12+ Philadelphia government meetings!**

This is a modular, config-driven system that can track and summarize agendas from multiple Philadelphia government meetings, all from one tool.

## What's New?

### Before (v1):
- ✅ Single script for PCPC only
- ✅ Manual process for each meeting

### Now (v2):
- ✅ **One system for 12+ meetings**
- ✅ **Config-driven** - easy to add new meetings
- ✅ **Modular architecture** - shared code, meeting-specific scrapers
- ✅ **Batch processing** - run all meetings at once
- ✅ **Custom summarization** - housing, design, historic preservation focus
- ✅ **Backward compatible** - original `pcpc_agenda_tracker.py` still works

## Quick Start

### List all available meetings:
```bash
python meeting_tracker.py --list
```

### Process a specific meeting:
```bash
python meeting_tracker.py --meeting pcpc
```

### Process all enabled meetings:
```bash
python meeting_tracker.py --all
```

## Currently Supported Meetings

**✓ Ready to use** (phila.gov scraper):
- Philadelphia City Planning Commission (PCPC)
- Civic Design Review (CDR)
- Historical Commission
- Historical Commission - Architecture Committee
- Art Commission
- Zoning Board of Adjustment (ZBA)
- Philadelphia Housing Advisory Commission

**⏳ Coming soon** (need custom scrapers):
- City Council Rules Committee (Legistar)
- City Council Streets Committee (Legistar)
- SEPTA Board
- Philadelphia Land Bank (PHDC)
- Philadelphia Housing Redevelopment Corp (PHDC)

## System Architecture

```
Meeting-agendas/
├── meeting_tracker.py       # Main orchestrator (NEW!)
├── config.yaml              # Meeting configurations (NEW!)
├── shared/                  # Shared utilities (NEW!)
│   ├── pdf_utils.py         # PDF download & extraction
│   ├── summarizer.py        # Claude AI summarization
│   └── google_docs.py       # Google Docs (coming soon)
├── scrapers/                # Meeting-specific scrapers (NEW!)
│   ├── base.py              # Base scraper class
│   ├── phila_gov.py         # phila.gov meetings
│   └── [more scrapers...]
├── summaries/               # Generated summaries
│   ├── pcpc/
│   ├── cdr/
│   ├── historical_commission/
│   └── ...
└── pcpc_agenda_tracker.py  # Original standalone script (still works!)
```

## Configuration

Edit `config.yaml` to customize meetings:

```yaml
meetings:
  pcpc:
    name: "Philadelphia City Planning Commission"
    url: "https://www.phila.gov/..."
    scraper: "phila_gov"
    pdf_pattern: "PCPC-Agenda"
    focus: "housing"
    enabled: true
```

### Focus Types:
- **housing** - Emphasizes zoning, development, affordability
- **design** - Focuses on architecture, public space, aesthetics
- **historic** - Highlights preservation, demolition, heritage
- **transportation** - Transit, infrastructure, accessibility
- **general** - Balanced overview

## Usage Examples

### Example 1: Weekly PCPC Summary
```bash
# Just like before, but now using the new system
python meeting_tracker.py --meeting pcpc
```

Output: `summaries/pcpc/PCPC_Summary_January_15_2026.md`

### Example 2: Batch Process All Meetings
```bash
# Process all enabled meetings at once
python meeting_tracker.py --all
```

This will:
1. Fetch latest agendas for PCPC, CDR, Historical Commission, etc.
2. Generate housing/design/historic-focused summaries
3. Save to organized folders
4. Print a summary report

### Example 3: Check What's Available
```bash
# See all configured meetings and their status
python meeting_tracker.py --list
```

## Adding New Meetings

### For phila.gov meetings (easy!):

1. Add to `config.yaml`:
```yaml
  new_meeting:
    name: "New Meeting Body"
    url: "https://www.phila.gov/..."
    scraper: "phila_gov"
    pdf_pattern: "agenda"
    focus: "housing"
    enabled: true
```

2. Run it:
```bash
python meeting_tracker.py --meeting new_meeting
```

### For other websites (need custom scraper):

1. Create new scraper in `scrapers/`:
```python
from .base import BaseScraper

class NewScraper(BaseScraper):
    def fetch_latest_agenda(self):
        # Custom scraping logic
        pass
```

2. Register in `meeting_tracker.py`:
```python
SCRAPERS = {
    'phila_gov': PhilaGovScraper,
    'new_site': NewScraper,  # Add this
}
```

3. Use in config:
```yaml
  meeting:
    scraper: "new_site"
```

## Customizing Summaries

Edit `shared/summarizer.py` to customize the AI prompts for each focus type:

```python
PROMPTS = {
    "housing": """Your custom housing-focused prompt...""",
    "design": """Your custom design-focused prompt...""",
    # etc.
}
```

## Migration from v1

**Good news: Nothing breaks!**

- `pcpc_agenda_tracker.py` still works exactly as before
- New system is completely separate
- Use whichever you prefer
- Eventually you can delete the old script

## Roadmap

- [x] Modular architecture
- [x] Config-driven meetings
- [x] Batch processing
- [x] Custom summarization prompts
- [x] phila.gov scraper (7 meetings)
- [ ] Google Docs auto-creation
- [ ] Legistar scraper (City Council)
- [ ] SEPTA scraper
- [ ] PHDC scraper (Land Bank, PHRC)
- [ ] Email notifications
- [ ] Calendar integration
- [ ] Webhook support

## Troubleshooting

**"Scraper not yet implemented"**
- Some meetings need custom scrapers
- Check `--list` to see which scrapers are ready
- You can add to config but keep `enabled: false` until scraper is ready

**"No agenda PDFs found"**
- Website structure may have changed
- Check the URL in config.yaml
- Adjust `pdf_pattern` to match the actual PDF names

**API key errors**
- Make sure `.env` file has your ANTHROPIC_API_KEY
- The `--list` command doesn't need an API key
- Processing meetings requires API key for summarization

## Contributing

Want to add support for more meetings?

1. **Easy**: Add phila.gov meetings to config (no coding needed!)
2. **Medium**: Create scrapers for Legistar, SEPTA, PHDC sites
3. **Advanced**: Add Google Calendar integration, webhook notifications

## Original Documentation

See `README.md` for the original PCPC-only documentation and setup instructions.

## Questions?

- **For general setup**: See main README.md
- **For adding meetings**: Check config.yaml examples
- **For custom scrapers**: Look at `scrapers/phila_gov.py`
- **For API/summarization**: See `shared/summarizer.py`

---

**Happy tracking!** 🏘️📋🏛️
