"""
Comprehensive scan of ALL newsletters for ANY bad link patterns
INVESTOR GRADE - be extremely thorough
"""

import sqlite3
import json
import re

conn = sqlite3.connect('data/articles.db')
cursor = conn.cursor()

cursor.execute('SELECT id, title, source, extracted_links FROM newsletters WHERE extracted_links IS NOT NULL')
rows = cursor.fetchall()

print(f"Scanning {len(rows)} newsletters for bad links...\n")

# COMPREHENSIVE bad patterns
BAD_PATTERNS = {
    'promotional': [
        'subscribe', 'unsubscribe', 'sign up', 'signup',
        'advertise', 'contact us', 'learn more.', 'read more.',
        'manage your email', 'email preferences', 'forwarded to you',
        'get axios', 'axios pro', 'axios hq',
    ],
    'verbs': [
        'reportedly', 'pressed', 'signed', 'wrote', 'filed', 'said', 'says',
        'pulled', 'pulling', 'told', 'telling', 'working', 'developed',
        'come', 'coming', 'building', 'built', 'secured', 'raised', 'raising',
        'hired', 'joining', 'opened', 'opening', 'acquired', 'acquiring',
    ],
    'fragments': [
        'can help', 'controversy', 'slated to close', 'to power',
        'currently shows', 'its facebook page', 'its .* page',
        'stateside', 'a new advocacy', 'the hustle',
    ],
    'financial': [
        r'for \$\d+', r'^\$\d+ (billion|million)', r'\d+ (billion|million) valuation',
    ],
}

bad_found = []

for row in rows:
    newsletter_id = row[0]
    title = row[1]
    source = row[2]
    links = json.loads(row[3]) if row[3] else []

    for link in links:
        link_title = link.get('title', '').strip()
        title_lower = link_title.lower()
        is_bad = False
        reason = ""

        # Check promotional
        for pattern in BAD_PATTERNS['promotional']:
            if pattern in title_lower:
                is_bad = True
                reason = f"promotional: {pattern}"
                break

        # Check verbs (single word only)
        if not is_bad and link_title.lower() in BAD_PATTERNS['verbs']:
            is_bad = True
            reason = f"single verb"

        # Check fragments
        if not is_bad:
            for pattern in BAD_PATTERNS['fragments']:
                if re.search(pattern, title_lower):
                    is_bad = True
                    reason = f"fragment: {pattern}"
                    break

        # Check financial fragments
        if not is_bad:
            for pattern in BAD_PATTERNS['financial']:
                if re.search(pattern, title_lower) and len(link_title.split()) < 5:
                    is_bad = True
                    reason = "financial fragment"
                    break

        # Check person names (2 capitalized words, short)
        if not is_bad and len(link_title.split()) == 2 and len(link_title) < 20:
            words = link_title.split()
            if all(w[0].isupper() for w in words if w):
                # Probably a name
                known_ok = ['steve jobs', 'bill gates', 'elon musk', 'sam altman', 'ai boom']
                if title_lower not in known_ok:
                    is_bad = True
                    reason = "person name"

        if is_bad:
            bad_found.append({
                'newsletter_id': newsletter_id,
                'newsletter_title': title[:50],
                'source': source,
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
print(f"FOUND {len(bad_found)} BAD LINKS IN {len(by_newsletter)} NEWSLETTERS")
print("="*80)
print()

if bad_found:
    # Show all problematic newsletters
    for nid in sorted(by_newsletter.keys()):
        items = by_newsletter[nid]
        first = items[0]
        print(f"Newsletter {nid}: {first['newsletter_title']}")
        print(f"  Source: {first['source']}")
        print(f"  Bad links: {len(items)}")
        for item in items[:10]:  # Show up to 10
            print(f"    - '{item['link_title']}' ({item['reason']})")
        if len(items) > 10:
            print(f"    ... and {len(items) - 10} more")
        print()

    # Print IDs for batch cleaning
    ids = sorted(by_newsletter.keys())
    print(f"Newsletter IDs to clean: {ids}")
else:
    print("[SUCCESS] No bad links found across all newsletters!")

print()
print("="*80)
