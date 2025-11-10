"""
Final comprehensive check - ONLY flag REAL bad links
Ignore product names (they're valid)
"""

import sqlite3
import json
import re

conn = sqlite3.connect('data/articles.db')
cursor = conn.cursor()

cursor.execute('SELECT id, title, source, extracted_links FROM newsletters WHERE extracted_links IS NOT NULL')
rows = cursor.fetchall()

print(f"Final comprehensive scan of {len(rows)} newsletters...\n")

# ONLY check for ACTUAL problems, not product names
REAL_BAD_PATTERNS = {
    'promotional': [
        'subscribe', 'unsubscribe', 'sign up', 'signup', 'register',
        'advertise', 'contact us', 'learn more.', 'click here.',
        'manage your email', 'email preferences', 'forwarded to you',
        'view in browser', 'web version',
    ],
    'single_verbs': [
        'reportedly', 'pressed', 'signed', 'wrote', 'filed', 'said', 'says',
        'pulled', 'pulling', 'told', 'telling', 'working', 'developed',
        'come', 'coming', 'building', 'built', 'secured', 'raised', 'raising',
        'hired', 'hiring', 'joined', 'joining', 'opened', 'opening',
        'tested', 'testing', 'using', 'made', 'making',
    ],
    'fragments': [
        'can help', 'will help', 'controversy', 'slated to close', 'to power',
        'currently shows', 'stateside', 'the hustle',
    ],
}

bad_found = []

for row in rows:
    newsletter_id = row[0]
    links = json.loads(row[3]) if row[3] else []

    for link in links:
        link_title = link.get('title', '').strip()
        title_lower = link_title.lower()
        is_bad = False
        reason = ""

        # Check promotional (substring match)
        for pattern in REAL_BAD_PATTERNS['promotional']:
            if pattern in title_lower:
                is_bad = True
                reason = f"promotional"
                break

        # Check single verbs (EXACT match only)
        if not is_bad and title_lower in REAL_BAD_PATTERNS['single_verbs']:
            is_bad = True
            reason = "single verb"

        # Check fragments (EXACT match)
        if not is_bad and title_lower in REAL_BAD_PATTERNS['fragments']:
            is_bad = True
            reason = "fragment"

        # Check financial fragments (short only)
        if not is_bad:
            if re.search(r'(for \$\d+|^\$\d+ billion)', title_lower) and len(link_title.split()) < 4:
                is_bad = True
                reason = "financial fragment"

        if is_bad:
            bad_found.append({
                'newsletter_id': newsletter_id,
                'link_title': link_title,
                'reason': reason
            })

conn.close()

# Group by newsletter
by_newsletter = {}
for item in bad_found:
    nid = item['newsletter_id']
    if nid not in by_newsletter:
        by_newsletter[nid] = []
    by_newsletter[nid].append(item)

print("="*80)
print(f"FINAL CHECK: {len(bad_found)} BAD LINKS IN {len(by_newsletter)} NEWSLETTERS")
print("="*80)
print()

if bad_found:
    for nid in sorted(by_newsletter.keys())[:20]:  # Show first 20
        items = by_newsletter[nid]
        print(f"Newsletter {nid}:")
        for item in items[:5]:
            print(f"  - '{item['link_title']}' ({item['reason']})")
        print()

    ids = sorted(by_newsletter.keys())
    print(f"Newsletter IDs: {ids}")
else:
    print("[SUCCESS] NO BAD LINKS FOUND!")
    print("All newsletters are investor-grade quality!")

print()
print("="*80)
