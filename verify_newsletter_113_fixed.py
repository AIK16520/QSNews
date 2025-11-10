"""
Verify Newsletter 113 and others are properly fixed
"""

import sqlite3
import json

# The problematic ones the user mentioned
CHECK_IDS = [113, 114]

conn = sqlite3.connect('data/articles.db')
cursor = conn.cursor()

print("Verifying cleaned newsletters:\n")

for nid in CHECK_IDS:
    cursor.execute('SELECT id, title, source, extracted_links FROM newsletters WHERE id = ?', (nid,))
    row = cursor.fetchone()

    if not row:
        print(f"Newsletter {nid} not found")
        continue

    newsletter_id = row[0]
    title = row[1]
    source = row[2]
    links = json.loads(row[3]) if row[3] else []

    print(f"Newsletter {newsletter_id}: {title[:60]}")
    print(f"Source: {source}")
    print(f"Total links: {len(links)}")
    print()

    # Look for any suspicious titles
    BAD_PATTERNS = ['can help', 'controversy', 'slated to close', 'to power',
                    'pulling', 'told', 'reports', 'said']

    suspicious_found = False
    for link in links:
        link_title = link.get('title', '')

        # Check for exact bad patterns
        if link_title.lower() in BAD_PATTERNS:
            print(f"  [BAD] {link_title}")
            suspicious_found = True

        # Check for very short titles that might be bad
        elif len(link_title.split()) <= 2 and len(link_title) < 12:
            # Skip known good ones
            if link_title.lower() not in ['ai', 'ml', 'gpt', 'openai', 'google']:
                print(f"  [SHORT] {link_title}")
                suspicious_found = True

    if not suspicious_found:
        print("  All titles look good!")

    print()
    print("-" * 80)
    print()

conn.close()

# Now check all newsletters for the specific bad patterns the user reported
print("\nScanning ALL newsletters for the specific bad patterns user reported...")
print()

conn = sqlite3.connect('data/articles.db')
cursor = conn.cursor()

cursor.execute('SELECT id, title, source, extracted_links FROM newsletters WHERE extracted_links IS NOT NULL')
rows = cursor.fetchall()

bad_found = []
for row in rows:
    newsletter_id = row[0]
    links = json.loads(row[3]) if row[3] else []

    for link in links:
        link_title = link.get('title', '')
        if link_title.lower() in ['can help', 'controversy', 'slated to close', 'pulling', 'told']:
            bad_found.append({
                'newsletter_id': newsletter_id,
                'title': link_title
            })

if bad_found:
    print(f"Found {len(bad_found)} instances of the bad patterns:")
    for item in bad_found:
        print(f"  Newsletter {item['newsletter_id']}: '{item['title']}'")
else:
    print("SUCCESS! No instances of 'can help', 'controversy', 'slated to close', 'pulling', 'told' found!")

conn.close()
