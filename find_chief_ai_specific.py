"""
Find ONLY the specific Chief AI Office bad links
"""

import sqlite3
import json

conn = sqlite3.connect('data/articles.db')
cursor = conn.cursor()

cursor.execute('SELECT id, title, source, extracted_links FROM newsletters WHERE source LIKE "%Chief AI%" AND extracted_links IS NOT NULL')
rows = cursor.fetchall()

print(f'Found {len(rows)} Chief AI Office newsletters\n')

bad_found = []

for row in rows:
    nid, title, source, links_json = row
    links = json.loads(links_json) if links_json else []

    for link in links:
        link_title = link.get('title', '')
        title_lower = link_title.lower()

        # Check for "Why X invested" patterns
        if title_lower.startswith('why ') and 'invest' in title_lower:
            bad_found.append({
                'nid': nid,
                'title': link_title,
                'type': 'investment fragment'
            })

        # Check for specific company names without context
        # These are the ones the user showed
        company_names_only = ['Periodic Labs', 'Axiom', 'Madrona', 'Felicis', 'B Capital',
                            'Andreessen Horowitz']

        if link_title in company_names_only:
            bad_found.append({
                'nid': nid,
                'title': link_title,
                'type': 'company name only'
            })

conn.close()

if bad_found:
    print(f'Found {len(bad_found)} bad links in Chief AI Office newsletters:\n')
    for item in bad_found:
        print(f"  Newsletter {item['nid']}: '{item['title']}' ({item['type']})")

    # Get unique newsletter IDs
    nids = sorted(set(item['nid'] for item in bad_found))
    print(f"\nNewsletter IDs to clean: {nids}")
else:
    print("No bad links found in Chief AI Office newsletters")
