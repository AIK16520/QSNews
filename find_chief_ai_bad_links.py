"""
Find ALL bad links in Chief AI Office and similar patterns
"""

import sqlite3
import json

conn = sqlite3.connect('data/articles.db')
cursor = conn.cursor()

cursor.execute('SELECT id, title, source, extracted_links FROM newsletters WHERE extracted_links IS NOT NULL')
rows = cursor.fetchall()

bad_patterns = [
    'why .* invested',
    'why .* partnered',
    'periodic labs',
    'axiom',
    'madrona',
    'felicis',
]

bad_found = []

for row in rows:
    newsletter_id = row[0]
    source = row[2]
    links = json.loads(row[3]) if row[3] else []

    for link in links:
        link_title = link.get('title', '').strip()
        title_lower = link_title.lower()

        # Check for "Why X invested" patterns
        if title_lower.startswith('why ') and 'invest' in title_lower:
            if len(link_title.split()) <= 4:  # Short fragment
                bad_found.append({
                    'newsletter_id': newsletter_id,
                    'source': source,
                    'title': link_title,
                    'reason': 'investment fragment'
                })

        # Check for single company names (very short, no context)
        elif len(link_title.split()) <= 2 and len(link_title) < 20:
            # Skip if it has tech keywords (product names)
            tech_keywords = ['ai', 'code', 'studio', 'gpt', 'claude', 'gemini']
            if not any(kw in title_lower for kw in tech_keywords):
                # Check if it looks like just a company name
                if link_title[0].isupper() and not any(c in link_title for c in [':', '-', '|']):
                    bad_found.append({
                        'newsletter_id': newsletter_id,
                        'source': source,
                        'title': link_title,
                        'reason': 'company name only'
                    })

conn.close()

# Group by newsletter
by_newsletter = {}
for item in bad_found:
    nid = item['newsletter_id']
    if nid not in by_newsletter:
        by_newsletter[nid] = []
    by_newsletter[nid].append(item)

print(f"Found {len(bad_found)} bad links in {len(by_newsletter)} newsletters\n")

for nid in sorted(by_newsletter.keys()):
    items = by_newsletter[nid]
    first = items[0]
    print(f"Newsletter {nid} ({first['source']}):")
    for item in items[:10]:
        print(f"  - '{item['title']}' ({item['reason']})")
    print()

if by_newsletter:
    ids = sorted(by_newsletter.keys())
    print(f"Newsletter IDs to clean: {ids}")
