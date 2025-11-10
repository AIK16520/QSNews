"""
Find the Axios newsletters with terrible promotional/navigation links
"""

import sqlite3
import json

conn = sqlite3.connect('data/articles.db')
cursor = conn.cursor()

cursor.execute('SELECT id, title, source, extracted_links FROM newsletters WHERE source LIKE "%Axios%" AND extracted_links IS NOT NULL')
rows = cursor.fetchall()

print(f'Found {len(rows)} Axios newsletters\n')

bad_patterns = [
    'contact us', 'subscribe', 'advertise', 'manage your email',
    'sign up now', 'currently shows', 'its facebook page',
    'lucinda shen', 'stateside', 'get axios', 'view in browser',
    'unsubscribe', 'email preferences', 'forwarded to you',
    'for $', 'valuation in', 'acquired', 'bought'
]

bad_newsletters = []

for row in rows:
    nid = row[0]
    title = row[1]
    links = json.loads(row[3]) if row[3] else []

    bad_links = []
    for link in links:
        link_title = link.get('title', '')
        title_lower = link_title.lower()

        # Check for bad patterns
        for pattern in bad_patterns:
            if pattern in title_lower:
                bad_links.append(link_title)
                break

    if bad_links:
        bad_newsletters.append({
            'id': nid,
            'title': title[:60],
            'bad_count': len(bad_links),
            'examples': bad_links[:5]
        })

if bad_newsletters:
    print(f'Found {len(bad_newsletters)} Axios newsletters with bad links:\n')
    for item in bad_newsletters:
        print(f"Newsletter {item['id']}: {item['title']}")
        print(f"  Bad links: {item['bad_count']}")
        for example in item['examples']:
            print(f"    - {example}")
        print()

    # Print IDs for re-cleaning
    ids = [item['id'] for item in bad_newsletters]
    print(f"Newsletter IDs to clean: {ids}")
else:
    print("No bad links found in Axios newsletters")

conn.close()
