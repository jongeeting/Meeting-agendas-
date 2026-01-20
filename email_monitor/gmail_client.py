"""
Gmail API client for fetching RCO newsletter emails.
"""

import os
import base64
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GmailClient:
    """Client for interacting with Gmail API."""

    # If modifying these scopes, delete the token.pickle file
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, credentials_path='gmail-credentials.json'):
        """
        Initialize Gmail client.

        Args:
            credentials_path: Path to Gmail API credentials JSON file
        """
        self.credentials_path = Path(credentials_path)
        self.token_path = Path('gmail-token.pickle')
        self.service = None

    def authenticate(self):
        """
        Authenticate with Gmail API using OAuth2.

        Returns:
            bool: True if authentication successful
        """
        creds = None

        # Load existing token if available
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    print(f"Error: Gmail credentials file not found at {self.credentials_path}")
                    print("Please download credentials from Google Cloud Console")
                    return False

                print("Starting OAuth2 flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for next time
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        try:
            self.service = build('gmail', 'v1', credentials=creds)
            print("✓ Successfully authenticated with Gmail")
            return True
        except Exception as e:
            print(f"Error building Gmail service: {e}")
            return False

    def fetch_emails(self, days_back=7, max_results=500, query=None):
        """
        Fetch emails from the last N days.

        Args:
            days_back: Number of days to look back
            max_results: Maximum number of emails to fetch
            query: Optional Gmail search query (e.g., "from:example@gmail.com")

        Returns:
            list: List of email dictionaries with id, sender, subject, date, body
        """
        if not self.service:
            print("Error: Not authenticated. Call authenticate() first.")
            return []

        try:
            # Calculate date range
            after_date = datetime.now() - timedelta(days=days_back)
            after_str = after_date.strftime('%Y/%m/%d')

            # Build search query
            search_query = f'after:{after_str}'
            if query:
                search_query = f'{query} {search_query}'

            print(f"Fetching emails with query: {search_query}")

            # Get list of message IDs
            results = self.service.users().messages().list(
                userId='me',
                q=search_query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            print(f"Found {len(messages)} emails")

            # Fetch full message details
            emails = []
            for i, msg in enumerate(messages, 1):
                if i % 50 == 0:
                    print(f"Processing email {i}/{len(messages)}...")

                email_data = self._get_email_details(msg['id'])
                if email_data:
                    emails.append(email_data)

            print(f"Successfully fetched {len(emails)} emails")
            return emails

        except HttpError as error:
            print(f'Gmail API error: {error}')
            return []

    def _get_email_details(self, msg_id):
        """
        Get full details of a single email.

        Args:
            msg_id: Gmail message ID

        Returns:
            dict: Email data or None if error
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()

            # Extract headers
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

            # Extract body
            body = self._get_email_body(message['payload'])

            return {
                'id': msg_id,
                'sender': sender,
                'subject': subject,
                'date': date,
                'body': body,
                'snippet': message.get('snippet', ''),
            }

        except Exception as e:
            print(f"Error fetching email {msg_id}: {e}")
            return None

    def _get_email_body(self, payload):
        """
        Recursively extract email body from payload.

        Args:
            payload: Gmail message payload

        Returns:
            str: Email body text
        """
        body = ""

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body += base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8', errors='ignore')
                elif 'parts' in part:
                    body += self._get_email_body(part)
        elif 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8', errors='ignore')

        return body

    def mark_as_read(self, msg_id):
        """
        Mark an email as read.

        Args:
            msg_id: Gmail message ID
        """
        try:
            self.service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except Exception as e:
            print(f"Error marking email as read: {e}")

    def add_label(self, msg_id, label_name):
        """
        Add a label to an email.

        Args:
            msg_id: Gmail message ID
            label_name: Name of label to add
        """
        try:
            # Get or create label
            label_id = self._get_or_create_label(label_name)

            # Add label to message
            self.service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'addLabelIds': [label_id]}
            ).execute()
        except Exception as e:
            print(f"Error adding label: {e}")

    def _get_or_create_label(self, label_name):
        """
        Get label ID or create if doesn't exist.

        Args:
            label_name: Name of label

        Returns:
            str: Label ID
        """
        # List existing labels
        results = self.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        # Check if label exists
        for label in labels:
            if label['name'] == label_name:
                return label['id']

        # Create new label
        label_object = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }

        created_label = self.service.users().labels().create(
            userId='me',
            body=label_object
        ).execute()

        return created_label['id']
