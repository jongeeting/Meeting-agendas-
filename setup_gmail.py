#!/usr/bin/env python3
"""
Simple script to set up Gmail authentication.
This will create the gmail-token.pickle file needed for API access.
"""

import sys
from pathlib import Path

# Add the email_monitor directory to path
sys.path.insert(0, str(Path(__file__).parent))

from email_monitor.gmail_client import GmailClient


def main():
    print("=" * 60)
    print("Gmail API Authentication Setup")
    print("=" * 60)
    print()

    # Check if credentials file exists
    creds_path = Path('gmail-credentials.json')
    if not creds_path.exists():
        print("❌ Error: gmail-credentials.json not found!")
        print()
        print("Please ensure you have downloaded your OAuth 2.0 credentials")
        print("from Google Cloud Console and saved them as 'gmail-credentials.json'")
        print("in this directory.")
        return 1

    print(f"✓ Found credentials file: {creds_path}")
    print()

    # Initialize Gmail client
    client = GmailClient(credentials_path='gmail-credentials.json')

    # Authenticate (this will open browser for OAuth)
    print("Starting authentication...")
    print("A browser window will open for you to authorize access.")
    print()

    if client.authenticate():
        print()
        print("=" * 60)
        print("✓ Setup complete!")
        print("=" * 60)
        print()
        print("Your authentication token has been saved to 'gmail-token.pickle'")
        print("You can now run the RCO monitor and other Gmail-based tools.")
        return 0
    else:
        print()
        print("❌ Authentication failed!")
        print("Please check the error messages above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
