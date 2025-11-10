"""
Comprehensive scan for ALL bad link titles
Be VERY strict - investor-grade quality required
"""

import sqlite3
import json
import re

conn = sqlite3.connect('data/articles.db')
cursor = conn.cursor()

cursor.execute('SELECT id, title, source, extracted_links FROM newsletters WHERE extracted_links IS NOT NULL')
rows = cursor.fetchall()

bad_found = []

# COMPREHENSIVE bad title patterns
BAD_PATTERNS = {
    'single_verbs': [
        'reportedly', 'pressed', 'signed', 'wrote', 'filed', 'said', 'reports',
        'pulled', 'pulling', 'backlash', 'became', 'signing', 'relaunching',
        'announced', 'released', 'launched', 'unveiled', 'revealed', 'confirmed',
        'denied', 'claims', 'suggests', 'shows', 'finds', 'told', 'telling',
        'added', 'noted', 'stated', 'mentioned', 'explained', 'described',
        'shared', 'posted', 'publishing', 'published', 'discussed', 'highlighted',
        'emphasized', 'focusing', 'targeting', 'planning', 'considering',
    ],
    'sentence_fragments': [
        'can help', 'will help', 'could help', 'may help',
        'driving the news', 'why it matters', 'what they\'re saying',
        'yes, but', 'the big picture', 'go deeper', 'between the lines',
        'the bottom line', 'what to watch', 'what\'s next',
        'slated to close', 'set to launch', 'expected to',
        'controversy', 'model', 'initiative', 'program', 'project',
    ],
    'generic_phrases': [
        'announced', 'news', 'update', 'report', 'article',
        'link', 'here', 'click here', 'read more', 'see more', 'learn more',
    ]
}

for row in rows:
    newsletter_id = row[0]
    newsletter_title = row[1]
    source = row[2]
    links = json.loads(row[3]) if row[3] else []

    for link in links:
        link_title = link.get('title', '').strip()
        url = link.get('url', '')

        if not link_title:
            continue

        title_lower = link_title.lower()
        is_bad = False
        reason = ""

        # Check single verbs
        if title_lower in BAD_PATTERNS['single_verbs']:
            is_bad = True
            reason = "single verb"

        # Check sentence fragments
        elif title_lower in BAD_PATTERNS['sentence_fragments']:
            is_bad = True
            reason = "sentence fragment"

        # Check if it's a common structural phrase (starts with these)
        elif any(title_lower.startswith(frag) for frag in ['why it matters', 'driving the news', 'what they\'re', 'yes, but']):
            is_bad = True
            reason = "structural phrase"

        # Check very short titles (2 words or less) that are likely fragments
        elif len(link_title.split()) <= 2 and len(link_title) < 15:
            # Exceptions for valid short titles
            exceptions = ['ai', 'ml', 'gpt', 'llm', 'nlp', 'openai', 'google', 'meta', 'apple']
            if title_lower not in exceptions and not any(exc in title_lower for exc in exceptions):
                # If it's just two common words, likely bad
                words = title_lower.split()
                common_words = ['the', 'a', 'an', 'to', 'for', 'of', 'in', 'on', 'at', 'by', 'with']
                if len(words) <= 2 and (words[0] in common_words or (len(words) > 1 and words[1] in common_words)):
                    is_bad = True
                    reason = "short fragment with common words"

        # Check if title is clearly incomplete (ends with preposition or conjunction)
        elif re.search(r'\b(and|or|but|with|for|to|in|on|at|by|of)$', title_lower):
            is_bad = True
            reason = "ends with preposition/conjunction"

        if is_bad:
            bad_found.append({
                'newsletter_id': newsletter_id,
                'newsletter_title': newsletter_title,
                'source': source,
                'link_title': link_title,
                'reason': reason,
                'url': url[:100]
            })

conn.close()

print(f"Found {len(bad_found)} links with bad titles")
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

# Show all bad titles grouped by newsletter
for nid in sorted(by_newsletter.keys()):
    items = by_newsletter[nid]
    first = items[0]
    title_safe = first['newsletter_title'].encode('ascii', 'ignore').decode('ascii')[:60]
    print(f"Newsletter {nid}: {title_safe}")
    print(f"  Source: {first['source']}")
    print(f"  Bad links: {len(items)}")
    for item in items:
        print(f"    - '{item['link_title']}' ({item['reason']})")
    print()

# Save IDs for re-cleaning
affected_ids = sorted(by_newsletter.keys())
print(f"Newsletter IDs to re-clean: {affected_ids}")
