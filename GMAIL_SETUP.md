# Gmail API Setup for RCO Monitor

This guide will help you set up Gmail API access for the RCO newsletter monitoring system.

## Overview

The RCO monitor needs to read emails from a Gmail account to find meeting announcements from neighborhood organizations. This requires:

1. A dedicated Gmail account (recommended)
2. Google Cloud Project with Gmail API enabled
3. OAuth2 credentials downloaded
4. One-time authentication

**Time required:** ~15 minutes

---

## Step 1: Create Dedicated Gmail Account (Recommended)

**Why?** Keep RCO newsletters separate from your personal email.

1. Go to https://accounts.google.com/signup
2. Create account like: `philly-rco-tracker@gmail.com`
3. Complete setup
4. **Save credentials** - you'll use this to subscribe to newsletters

---

## Step 2: Set Up Google Cloud Project

### 2.1 Create Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Gmail account
3. Click project dropdown at top → **"NEW PROJECT"**
4. Project name: `RCO Newsletter Tracker`
5. Click **CREATE**
6. Wait ~10 seconds, then select your new project

### 2.2 Enable Gmail API

1. In search bar at top, type: **Gmail API**
2. Click **"Gmail API"** in results
3. Click blue **"ENABLE"** button
4. Wait for it to enable

### 2.3 Configure OAuth Consent Screen

1. In left sidebar, click **"OAuth consent screen"**
2. Select **"External"** (unless you have a Google Workspace)
3. Click **"CREATE"**

4. **Fill out App Information:**
   - App name: `RCO Newsletter Tracker`
   - User support email: Your email
   - Developer contact: Your email
   - Leave other fields blank

5. Click **"SAVE AND CONTINUE"**

6. **Scopes page:**
   - Click **"ADD OR REMOVE SCOPES"**
   - Search for: `gmail.readonly`
   - Check the box for `https://www.googleapis.com/auth/gmail.readonly`
   - Click **"UPDATE"**
   - Click **"SAVE AND CONTINUE"**

7. **Test users page:**
   - Click **"+ ADD USERS"**
   - Enter your RCO tracker Gmail address (e.g., `philly-rco-tracker@gmail.com`)
   - Click **"ADD"**
   - Click **"SAVE AND CONTINUE"**

8. Click **"BACK TO DASHBOARD"**

### 2.4 Create OAuth2 Credentials

1. In left sidebar, click **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** at top
3. Select **"OAuth client ID"**
4. Application type: **"Desktop app"**
5. Name: `RCO Monitor Desktop Client`
6. Click **"CREATE"**

7. **Download credentials:**
   - A popup will show your client ID and secret
   - Click **"DOWNLOAD JSON"**
   - The file will download (name like `client_secret_xxx.json`)

8. **Rename and move the file:**
   - Rename it to: `gmail-credentials.json`
   - Move it to your `Meeting-agendas` folder

---

## Step 3: Install Dependencies

On your Mac Terminal:

```bash
cd ~/Downloads/Meeting-agendas
pip3 install -r requirements.txt
```

This installs the Google API Python libraries.

---

## Step 4: Test Authentication

Run the setup wizard:

```bash
python3 rco_monitor.py --setup
```

**What will happen:**

1. A browser window will open
2. Google will ask you to sign in
3. Google will warn "App isn't verified" - click **"Advanced"** → **"Go to RCO Newsletter Tracker (unsafe)"**
4. Click **"Allow"** to grant read access to Gmail
5. You can close the browser window

**Result:** A file called `gmail-token.pickle` will be created. This stores your authentication so you don't have to sign in every time.

---

## Step 5: Subscribe to RCO Newsletters

Now use your dedicated Gmail account to subscribe to RCO newsletters:

### Finding RCO Newsletters

**Option 1: Philly RCO Directory**
- Go to https://www.phila.gov/media/20190717094504/RCO-List.pdf
- Find RCOs in neighborhoods you care about
- Google them to find their websites
- Look for "Newsletter" or "Join our mailing list"

**Option 2: Common platforms:**
- Mailchimp signup forms
- Google Groups
- Direct email signup

**Tip:** Create a spreadsheet to track which RCOs you've subscribed to.

### Recommended RCOs to Start

High-activity RCOs that frequently discuss development:
- Center City Residents Association (CCRA)
- Fishtown Neighbors Association (FNA)
- Bella Vista Neighbors Association (BVNA)
- Society Hill Civic Association
- Point Breeze Avenue RCO
- Washington Square West Civic Association

---

## Step 6: Test the System

After subscribing to a few newsletters, wait for emails to arrive, then:

```bash
# Check for emails from last 7 days
python3 rco_monitor.py --check

# Generate weekly digest
python3 rco_monitor.py --digest weekly
```

---

## Troubleshooting

### "Gmail credentials file not found"

- Make sure `gmail-credentials.json` is in the `Meeting-agendas` folder
- Check the filename is exactly right (no extra `.txt` or numbers)

### "App isn't verified" warning

- This is normal for personal projects
- Click "Advanced" → "Go to... (unsafe)"
- Your app only has access to YOUR Gmail, so it's safe

### "Access denied"

- Make sure you added yourself as a test user in OAuth consent screen
- Try creating a new OAuth client ID

### "Token has been expired or revoked"

- Delete `gmail-token.pickle`
- Run `python3 rco_monitor.py --setup` again

### No emails found

- Make sure you've actually subscribed to some RCO newsletters
- Wait for newsletters to arrive (they're often weekly/monthly)
- Try with `--days 30` to look back further

---

## Daily/Weekly Workflow

### Daily Check (Automated)

Create a cron job or scheduled task:

```bash
# Add to crontab (run at 9am daily)
0 9 * * * cd ~/Meeting-agendas && python3 rco_monitor.py --check
```

### Weekly Digest (Manual)

Every Monday morning:

```bash
python3 rco_monitor.py --digest weekly
```

This creates a file like `summaries/rco/digest_weekly_20260120.md` with all upcoming meetings.

---

## Security & Privacy

**Is this secure?**
- ✅ Yes - OAuth2 is industry standard
- ✅ You control the credentials
- ✅ Read-only access (can't send emails or delete)
- ✅ Token stored locally on your computer

**What data is accessed?**
- Only emails in your RCO tracker Gmail account
- Only metadata (sender, subject, date) and body text
- Nothing is shared with third parties

**Can I revoke access?**
- Yes, go to https://myaccount.google.com/permissions
- Find "RCO Newsletter Tracker"
- Click "Remove access"

---

## Advanced Configuration

### Filter by sender

Edit `config.yaml`:

```yaml
rco_monitoring:
  search_query: "from:*@phillyneighborhoods.org OR from:*@rcophilly.org"
```

### Change output directory

```yaml
rco_monitoring:
  output_dir: "summaries/rco"  # Change this
```

### Disable email labeling

```yaml
rco_monitoring:
  label_processed: false  # Don't add labels in Gmail
```

---

## What's Next?

1. Subscribe to 10-20 RCOs to start
2. Run `--check` daily or weekly
3. Review the generated digests
4. Adjust configuration based on what you find
5. Gradually add more RCOs

Eventually you'll have automated monitoring of 100+ neighborhood organizations with zero manual work!

---

## Questions?

- **Can't figure out a step?** Re-read carefully, most issues are from skipping steps
- **Still stuck?** Check Google Cloud Console documentation
- **Want to add features?** Edit the code in `email_monitor/` and `rco_monitor.py`
