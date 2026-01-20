# RCO Newsletter Monitor

**Automated monitoring of 200+ Philadelphia neighborhood organization newsletters**

Never miss a zoning meeting, development proposal, or bike lane discussion in your neighborhoods again!

## What It Does

1. **Monitors Gmail inbox** for RCO newsletter emails
2. **Uses Claude AI** to identify meeting announcements
3. **Filters for relevance** - only zoning, development, transit, bike lanes
4. **Extracts details** - date, time, location, agenda items
5. **Generates digest** - weekly summary of all upcoming meetings

## Quick Start

### 1. Setup (One Time - ~20 minutes)

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run setup wizard
python3 rco_monitor.py --setup
```

Follow the prompts to connect your Gmail account. See [GMAIL_SETUP.md](GMAIL_SETUP.md) for detailed instructions.

### 2. Subscribe to RCO Newsletters

Create a dedicated Gmail account and subscribe to RCO newsletters:

- Use the [Phila.gov RCO list](https://www.phila.gov/media/20190717094504/RCO-List.pdf)
- Start with 10-20 active RCOs
- Expand to 100+ over time

### 3. Monitor & Digest

```bash
# Check for new meeting announcements
python3 rco_monitor.py --check

# Generate weekly digest
python3 rco_monitor.py --digest weekly
```

## How It Works

### Email Collection
- Connects to Gmail using OAuth2 (secure, read-only)
- Fetches emails from last 7 days
- Supports filtering by sender, keyword, etc.

### AI-Powered Classification
Claude AI analyzes each email and determines:
- ✅ Is this a meeting announcement?
- ✅ Is it relevant to housing/development/transit?
- ✅ What topics are covered?

**Only keeps relevant meetings** - ignores:
- ❌ Crime alerts
- ❌ General neighborhood news
- ❌ Fundraisers
- ❌ Social events

### Smart Extraction
For relevant meetings, Claude extracts:
- 📅 Meeting date & time
- 📍 Location (address or Zoom link)
- 📋 Agenda items with addresses
- 🏠 Why each item matters for housing advocates

### Automated Digest

Weekly digest output:

```markdown
# RCO Meetings Digest - Weekly

## Monday, January 20, 2026

### Fishtown Neighbors Association
📅 Date: Monday, January 20, 2026
🕐 Time: 6:30 PM
📍 Location: [Zoom](https://zoom.us/j/...)

**Relevant Agenda Items:**

🏗️ **Zoning Variance - 1234 Frankford Ave**
  Developer seeking variance for 5-story mixed-use building
  *Why it matters:* Height precedent for commercial corridor development

🚴 **Frankford Ave Protected Bike Lane - Final Design**
  Streets Department presenting plans for parking-protected bike lanes
  *Why it matters:* Major bike infrastructure on key commercial street

...
```

## Configuration

Edit `config.yaml`:

```yaml
rco_monitoring:
  enabled: true
  gmail_credentials: "gmail-credentials.json"
  output_dir: "summaries/rco"
  max_emails: 500
  search_query: null  # Optional: filter by sender
  label_processed: true  # Tag emails in Gmail

  relevant_keywords:
    - zoning
    - variance
    - development
    - bike lane
    - transit
    # ... add more
```

## Commands

### Check for New Emails

```bash
# Last 7 days (default)
python3 rco_monitor.py --check

# Last 30 days
python3 rco_monitor.py --check --days 30

# Dry run (don't save results)
python3 rco_monitor.py --check --dry-run
```

### Generate Digest

```bash
# Weekly digest (next 7 days)
python3 rco_monitor.py --digest weekly

# Monthly digest (next 30 days)
python3 rco_monitor.py --digest monthly

# Daily digest (next 24 hours)
python3 rco_monitor.py --digest daily
```

### Setup & Troubleshooting

```bash
# Re-run setup
python3 rco_monitor.py --setup

# Check authentication
python3 rco_monitor.py --check --dry-run
```

## Automation

### Daily Monitoring (Recommended)

**Mac/Linux - Cron Job:**

```bash
# Edit crontab
crontab -e

# Add line (runs daily at 9am)
0 9 * * * cd ~/Meeting-agendas && python3 rco_monitor.py --check
```

**Windows - Task Scheduler:**
- Create task to run `rco_monitor.py --check` daily

### Weekly Digest

Run manually each Monday, or add to cron:

```bash
# Mondays at 8am
0 8 * * 1 cd ~/Meeting-agendas && python3 rco_monitor.py --digest weekly
```

## Output

### Meeting Data (JSON)

`summaries/rco/meetings_20260120_093000.json`:

```json
[
  {
    "meeting_date": "2026-01-20",
    "meeting_time": "6:30 PM",
    "meeting_location": "Zoom",
    "meeting_link": "https://zoom.us/...",
    "organization_name": "Fishtown Neighbors Association",
    "agenda_items": [
      {
        "title": "Zoning Variance - 1234 Frankford Ave",
        "address": "1234 Frankford Ave",
        "type": "zoning_variance",
        "description": "...",
        "why_relevant": "..."
      }
    ],
    "email_id": "...",
    "email_sender": "..."
  }
]
```

### Digest (Markdown)

`summaries/rco/digest_weekly_20260120.md` - formatted for easy reading and sharing

## Integration with Official Meeting Tracker

The RCO monitor is designed to complement the official meeting tracker:

```bash
# Get official meetings (PCPC, City Council, etc.)
python3 meeting_tracker.py --all

# Get RCO meetings
python3 rco_monitor.py --check
python3 rco_monitor.py --digest weekly

# Future: Combined digest
python3 generate_master_digest.py --week
```

## Advanced Usage

### Filter by Sender Pattern

Only process emails from specific domains:

```yaml
rco_monitoring:
  search_query: "from:*@phillyneighborhoods.org OR from:*@rcophilly.org"
```

### Custom Keywords

Add neighborhood-specific keywords:

```yaml
rco_monitoring:
  relevant_keywords:
    - zoning
    - "south street"
    - "washington avenue"
    # ... your keywords
```

### Programmatic Access

```python
from email_monitor import GmailClient, EmailClassifier, MeetingExtractor

# Initialize
gmail = GmailClient()
gmail.authenticate()

# Fetch emails
emails = gmail.fetch_emails(days_back=7)

# Classify
classifier = EmailClassifier()
classified = classifier.classify_batch(emails)
relevant = classifier.filter_relevant(classified)

# Extract
extractor = MeetingExtractor()
meetings = extractor.extract_batch([e for e,_ in relevant])

# Your custom processing here
for meeting in meetings:
    print(meeting)
```

## Costs

**Gmail API:** Free
- 1 billion quota units per day
- Fetching 500 emails ≈ 50,000 quota units
- You can check **thousands** of emails per day for free

**Claude API:** Pay-as-you-go
- ~$0.003 per email classification
- ~$0.006 per meeting extraction
- 100 emails/week ≈ **$0.90/week** or **~$47/year**
- 500 RCO emails/week ≈ **$4.50/week** or **~$234/year**

Very affordable for comprehensive neighborhood monitoring!

## Privacy & Security

**Your data:**
- ✅ Processed on your computer
- ✅ Sent to Claude API (Anthropic) for analysis
- ✅ Not stored by Anthropic after processing
- ✅ Not shared with anyone else

**Gmail access:**
- ✅ Read-only (can't send or delete emails)
- ✅ OAuth2 secure authentication
- ✅ You can revoke anytime at https://myaccount.google.com/permissions

**Credentials:**
- `gmail-credentials.json` - OAuth app config (safe to commit)
- `gmail-token.pickle` - Your personal token (in `.gitignore`, don't share!)
- `.env` - Your Claude API key (in `.gitignore`, don't share!)

## Recommended RCOs

Start with these active RCOs that frequently discuss development:

**Center City:**
- Center City Residents Association (CCRA)
- Rittenhouse Square Improvement District
- Washington Square West Civic Association

**South Philly:**
- Bella Vista Neighbors Association
- Point Breeze Avenue RCO
- Newbold Civic Association

**Northern Liberties / Fishtown:**
- Fishtown Neighbors Association
- Northern Liberties Neighbors Association
- Old Kensington Community Development Corporation

**West Philly:**
- Spruce Hill Community Association
- University City District

**See full list:** https://www.phila.gov/media/20190717094504/RCO-List.pdf

## Troubleshooting

See [GMAIL_SETUP.md](GMAIL_SETUP.md) for detailed troubleshooting.

**Common issues:**

- **"No emails found"** → Subscribe to more RCOs, or use `--days 30`
- **"Gmail auth failed"** → Run `python3 rco_monitor.py --setup` again
- **"API key error"** → Check `.env` file has `ANTHROPIC_API_KEY=...`
- **"No relevant meetings"** → Adjust keywords in `config.yaml`

## Roadmap

- [ ] Combined digest with official meetings
- [ ] Google Calendar integration
- [ ] Email export (forward digest to mailing list)
- [ ] Web dashboard
- [ ] Mobile notifications
- [ ] Historical analysis (track development patterns)

## Examples

**Real-world use cases:**

1. **Housing advocate** - Monitor all 200 RCOs for zoning variances
2. **Bike advocate** - Track bike lane discussions across neighborhoods
3. **Developer** - Stay informed on community meetings in target areas
4. **Journalist** - Find development stories before they hit the news
5. **City planner** - Understand community concerns citywide

---

**Questions?** See [GMAIL_SETUP.md](GMAIL_SETUP.md) or open an issue on GitHub.

**Happy tracking!** 🏘️📧
