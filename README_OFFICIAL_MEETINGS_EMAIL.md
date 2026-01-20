# Official Meetings Email Monitor

Monitors Gmail for official city meeting notifications (Land Bank, SEPTA, etc.) and generates summaries in the same format as scraped meetings.

## What's the Difference?

Your system has **TWO separate email monitors**:

### 1. RCO Monitor (`rco_monitor.py`)
- **Purpose**: Neighborhood organization newsletters
- **Source**: 200+ Registered Community Organizations
- **Output**: `summaries/rco/` - community meeting digests
- **Gmail Label**: "RCO" (or custom)

### 2. Official Meetings Monitor (`official_meetings_monitor.py`)
- **Purpose**: Official city government meetings
- **Source**: Land Bank, SEPTA, ZBA notices
- **Output**: `summaries/land_bank/`, `summaries/septa/` - same as scraped meetings
- **Gmail Label**: "Official-Meetings"

**Why separate?** RCO emails are community newsletters that get grouped into weekly digests. Official meeting emails contain agendas that should be processed individually and saved alongside your scraped meeting summaries.

## Setup

### 1. Gmail API Setup

Follow the same Gmail API setup as the RCO monitor (see `GMAIL_SETUP.md`). You can use the same `gmail-credentials.json` file for both monitors.

### 2. Create Gmail Filter

Create a Gmail filter to automatically label official meeting emails:

**Filter settings:**
- **From**: Contains any of: `landbank`, `septa.org`, `phila.gov`
- **Subject**: Contains any of: `meeting`, `agenda`, `board`
- **Apply label**: `Official-Meetings` (create this label if it doesn't exist)

**To create the filter:**
1. In Gmail, click the search box dropdown (⌄)
2. Enter the filter criteria above
3. Click "Create filter"
4. Check "Apply the label" → Select or create "Official-Meetings"
5. Check "Also apply filter to matching conversations" (optional)
6. Click "Create filter"

### 3. Subscribe to Meeting Notifications

Subscribe to email notifications from:

- **Philadelphia Land Bank**:
  - Visit: https://phillylandbank.org/contact/
  - Sign up for board meeting notifications

- **SEPTA Board**:
  - Visit: https://www.septa.org/
  - Look for board meeting notification signup

- **Zoning Board of Adjustment** (if available):
  - Check phila.gov for ZBA email notifications

### 4. Run Setup

```bash
python3 official_meetings_monitor.py --setup
```

This will verify:
- Gmail API credentials are working
- Claude API key is configured
- System is ready to process emails

## Usage

### Check for New Meetings

Run this command to check your Gmail for new meeting notifications:

```bash
python3 official_meetings_monitor.py --check
```

This will:
1. Fetch all emails with "Official-Meetings" label from the last 30 days
2. Identify meeting type (Land Bank, SEPTA, etc.)
3. Extract PDF links from email body
4. Download and process the PDFs
5. Generate AI summaries using Claude
6. Save to `summaries/land_bank/`, `summaries/septa/`, etc.

### Check Specific Time Period

```bash
# Check last 7 days
python3 official_meetings_monitor.py --check --days 7

# Check last 60 days
python3 official_meetings_monitor.py --check --days 60
```

### Test Without Saving

```bash
python3 official_meetings_monitor.py --check --dry-run
```

## How It Works

1. **Email Detection**: Script looks for emails with the "Official-Meetings" label
2. **Meeting Identification**: Analyzes sender and subject to identify meeting type
   - `landbank` → Philadelphia Land Bank
   - `septa` → SEPTA Board
   - `zba` or `zoning board` → Zoning Board of Adjustment
3. **PDF Extraction**: Finds PDF links in email body (URLs ending in `.pdf`)
4. **Text Extraction**: Downloads PDF and extracts text
5. **AI Summarization**: Uses Claude API with meeting-specific prompts
6. **Save**: Saves to `summaries/{meeting_type}/` using same format as scraped meetings

## Output

Summaries are saved in the same format and location as scraped meetings:

```
summaries/
├── land_bank/
│   └── LAND_BANK_Summary_2024_January_15.md
├── septa/
│   └── SEPTA_Summary_2024_January_20.md
├── pcpc/              # From web scraper
│   └── PCPC_Summary_2024_January_10.md
└── rco/               # From RCO monitor (separate)
    └── digest_weekly_20240115.md
```

This means your regular meeting tracker (`meeting_tracker.py --all`) and email monitor work together seamlessly - all official meetings end up in the same place!

## Automation

You can run this on a schedule using cron:

```bash
# Add to crontab (run `crontab -e`)
# Check for new meetings every Monday at 9 AM
0 9 * * 1 cd /path/to/Meeting-agendas && python3 official_meetings_monitor.py --check
```

## Troubleshooting

### "No emails found with 'Official-Meetings' label"

1. Check that you created the Gmail label
2. Verify your Gmail filter is working (send yourself a test email)
3. Make sure you've subscribed to meeting notifications

### "Could not identify meeting type"

The script couldn't determine which meeting this email is for. Check:
- Email sender contains keywords like `landbank`, `septa`, etc.
- Email subject contains meeting-related terms

You can add more patterns by editing `_identify_meeting()` in `official_meetings_monitor.py`

### "No PDF links found in email"

The email doesn't contain PDF URLs. Some emails might:
- Have PDFs as attachments (not yet supported - would need enhancement)
- Link to a webpage instead of direct PDF (would need manual handling)
- Use a different format

## Next Steps

1. Complete Gmail API setup if you haven't already
2. Create the "Official-Meetings" Gmail filter
3. Subscribe to Land Bank and SEPTA notifications
4. Run `--setup` to verify everything works
5. Run `--check` to process existing emails
6. Set up cron job for automatic checking (optional)

## Need Help?

See `GMAIL_SETUP.md` for detailed Gmail API setup instructions.
