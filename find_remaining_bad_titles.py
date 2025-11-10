"""
Find newsletters that still have bad link titles
"""

import sqlite3
import json

# Extended list of bad verb titles
BAD_VERBS = [
    'reportedly', 'pressed', 'signed', 'wrote', 'filed', 'said', 'reports',
    'pulled', 'pulling', 'backlash', 'became', 'signing', 'relaunching',
    'announced', 'released', 'launched', 'unveiled', 'revealed', 'confirmed',
    'denied', 'claims', 'suggests', 'shows', 'finds', 'told', 'telling',
    'added', 'noted', 'stated', 'mentioned', 'explained', 'described',
    'shared', 'posted', 'published', 'discussed', 'highlighted', 'emphasized'
]

conn = sqlite3.connect('data/articles.db')
cursor = conn.cursor()

cursor.execute('SELECT id, title, source, extracted_links FROM newsletters WHERE extracted_links IS NOT NULL')
rows = cursor.fetchall()

bad_found = []

for row in rows:
    newsletter_id = row[0]
    newsletter_title = row[1]
    source = row[2]
    links = json.loads(row[3]) if row[3] else []

    for link in links:
        link_title = link.get('title', '').strip()
        url = link.get('url', '')

        # Check if it's a bad verb title
        if link_title.lower() in BAD_VERBS:
            bad_found.append({
                'newsletter_id': newsletter_id,
                'newsletter_title': newsletter_title,
                'source': source,
                'link_title': link_title,
                'url': url[:100]
            })

conn.close()

print(f"Found {len(bad_found)} links with bad verb titles")
print()

# Group by newsletter
by_newsletter = {}
for item in bad_found:
    nid = item['newsletter_id']
    if nid not in by_newsletter:
        by_newsletter[nid] = []
    by_newsletter[nid].append(item)

print(f"Affected newsletters: {len(by_newsletter)}")
print()

# Show details
for nid in sorted(by_newsletter.keys())[:10]:
    items = by_newsletter[nid]
    first = items[0]
    print(f"Newsletter {nid}: {first['newsletter_title'][:60]}")
    print(f"  Source: {first['source']}")
    print(f"  Bad links: {len(items)}")
    for item in items[:3]:
        print(f"    - '{item['link_title']}' -> {item['url']}")
    print()
