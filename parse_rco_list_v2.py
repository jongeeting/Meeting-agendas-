#!/usr/bin/env python3
"""
Parse RCO list from PDF text and create spreadsheet.

Filters out ward organizations without websites.
"""

import csv
import re


def extract_rcos(text):
    """
    Extract RCO information from PDF text.

    Strategy:
    - Find all email addresses
    - Work backwards from email to extract: year, website, contact name
    - Work forwards to extract organization name
    """
    rcos = []

    # Remove page headers
    text = re.sub(r'--- Page \d+ ---', '', text)
    text = re.sub(r'Page \d+ of \d+', '', text)

    # Find all email addresses with some context
    # Pattern: capture text before and after email
    email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'

    # Split text into chunks, keeping emails
    parts = re.split(f'({email_pattern})', text)

    # Process in groups of 3: [text_before, email, text_after]
    i = 0
    while i < len(parts):
        if i + 1 < len(parts) and '@' in parts[i + 1]:
            text_before = parts[i]
            email = parts[i + 1]

            # Skip if this looks like a header
            if 'Organization Name' in text_before or 'Primary Email' in text_before:
                i += 2
                continue

            # Extract from text_before (going backwards from email)
            lines_before = [l.strip() for l in text_before.split('\n') if l.strip()]

            if not lines_before:
                i += 2
                continue

            # Last line before email is usually year
            year = ''
            if lines_before:
                last_line = lines_before[-1]
                year_match = re.search(r'\b(202[5-9])\b', last_line)
                if year_match:
                    year = year_match.group(1)
                    lines_before = lines_before[:-1]  # Remove year line

            # Next line backwards is website
            website = 'No website provided'
            if lines_before:
                last_line = lines_before[-1]
                if 'http' in last_line or 'www.' in last_line:
                    website_match = re.search(r'(https?://[^\s]+|www\.[^\s]+)', last_line)
                    if website_match:
                        website = website_match.group(1)
                        # Remove website from line
                        last_line = last_line.replace(website, '').strip()
                        lines_before[-1] = last_line
                elif 'No website provided' in last_line:
                    website = 'No website provided'
                    # Remove this text
                    last_line = last_line.replace('No website provided', '').strip()
                    lines_before[-1] = last_line

            # Next line backwards is primary contact name
            contact_name = ''
            if lines_before:
                last_line = lines_before[-1]
                # Clean up any remaining year or website text
                last_line = re.sub(r'\b202[5-9]\b', '', last_line).strip()
                if last_line:
                    contact_name = last_line
                    lines_before = lines_before[:-1]

            # Organization name is the first substantive line
            org_name = ''
            for line in lines_before:
                # Skip meeting location lines (usually have addresses or "ZOOM")
                if ('ZOOM' in line.upper() or
                    'Zoom' in line or
                    re.search(r'\d{4,5}\s+[A-Z]', line) or  # Address pattern
                    re.search(r'PA\s+\d{5}', line) or  # PA zip code
                    'Meeting' in line or
                    'Philadelphia' in line and len(line) < 50):
                    continue

                # This should be the org name
                if len(line) > 5:
                    org_name = line
                    break

            if org_name and email:
                rcos.append({
                    'name': org_name.strip(),
                    'contact_name': contact_name.strip(),
                    'email': email.strip(),
                    'website': website.strip(),
                    'expiration_year': year
                })

            i += 2
        else:
            i += 1

    return rcos


# Read the extracted text
with open('rco_list.txt', 'r') as f:
    text = f.read()

# Extract RCOs
rcos = extract_rcos(text)

print(f"Extracted {len(rcos)} RCOs")

# Filter: remove ward organizations without websites
filtered_rcos = []

for rco in rcos:
    name_lower = rco['name'].lower()
    has_website = rco['website'] not in ['No website provided', '']

    # Check if it's a ward org
    is_ward = 'ward' in name_lower and ('democratic' in name_lower or 'republican' in name_lower)

    # Keep if: (not a ward org) OR (is ward org BUT has website)
    if not is_ward or has_website:
        filtered_rcos.append(rco)

print(f"After filtering: {len(filtered_rcos)} RCOs (removed {len(rcos) - len(filtered_rcos)} ward orgs without websites)")

# Save to CSV
output_file = 'RCO_Newsletter_Subscriptions.csv'

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['Organization Name', 'Contact Name', 'Email', 'Website', 'Expiration Year']
    writer = csv.DictWriter(f, fieldnames=fieldnames)

    writer.writeheader()
    for rco in sorted(filtered_rcos, key=lambda x: x['name']):
        writer.writerow({
            'Organization Name': rco['name'],
            'Contact Name': rco['contact_name'],
            'Email': rco['email'],
            'Website': rco['website'],
            'Expiration Year': rco['expiration_year']
        })

print(f"\nSaved to {output_file}")
print(f"\nSample entries:")
for i, rco in enumerate(sorted(filtered_rcos, key=lambda x: x['name'])[:5]):
    print(f"\n{i+1}. {rco['name']}")
    print(f"   Contact: {rco['contact_name']}")
    print(f"   Email: {rco['email']}")
    print(f"   Website: {rco['website']}")
