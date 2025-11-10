"""
Final comprehensive quality check - INVESTOR GRADE
"""

import sqlite3
import json

conn = sqlite3.connect('data/articles.db')
cursor = conn.cursor()

cursor.execute('SELECT id, title, source, extracted_links FROM newsletters WHERE extracted_links IS NOT NULL')
rows = cursor.fetchall()

# Comprehensive bad patterns
BAD_VERBS = [
    'reportedly', 'pressed', 'signed', 'wrote', 'filed', 'said', 'says', 'reports',
    'pulled', 'pulling', 'backlash', 'became', 'signing', 'relaunching', 'announced',
    'released', 'launched', 'unveiled', 'revealed', 'confirmed', 'denied',
    'claims', 'suggests', 'shows', 'finds', 'told', 'telling', 'added', 'noted',
    'stated', 'mentioned', 'explained', 'described', 'shared', 'posted', 'publishing',
    'published', 'discussed', 'highlighted', 'emphasized', 'focusing', 'targeting',
    'working', 'developed', 'developing', 'come', 'coming', 'building', 'built',
    'secured', 'raised', 'raising', 'funded', 'funding', 'acquired', 'acquiring',
]

BAD_FRAGMENTS = [
    'can help', 'will help', 'controversy', 'slated to close', 'to power',
    'learn more', 'learn more.', 'read more', 'click here', 'axios hq', 'the hustle',
]

bad_count = 0
bad_details = []

for row in rows:
    newsletter_id = row[0]
    links = json.loads(row[3]) if row[3] else []

    for link in links:
        link_title = link.get('title', '').strip()
        title_lower = link_title.lower()

        # Check for bad patterns
        if title_lower in BAD_VERBS or title_lower in BAD_FRAGMENTS:
            bad_count += 1
            bad_details.append({
                'newsletter_id': newsletter_id,
                'title': link_title
            })

conn.close()

print("="*80)
print("FINAL QUALITY CHECK - INVESTOR GRADE")
print("="*80)
print()

if bad_count == 0:
    print("[SUCCESS] No bad link titles found!")
    print("All newsletters pass investor-grade quality standards.")
else:
    print(f"[WARNING] Found {bad_count} potentially bad link titles:")
    print()
    for item in bad_details[:20]:  # Show first 20
        print(f"  Newsletter {item['newsletter_id']}: '{item['title']}'")

print()
print("="*80)
