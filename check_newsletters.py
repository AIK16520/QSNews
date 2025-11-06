"""
Quick script to view newsletters in the database.
"""

from src.utils.database import get_session, Newsletter
import json

session = get_session()

# Get all newsletters
newsletters = session.query(Newsletter).order_by(Newsletter.published_date.desc()).all()

print(f"\n{'='*80}")
print(f"NEWSLETTERS IN DATABASE: {len(newsletters)}")
print(f"{'='*80}\n")

# Group by source
by_source = {}
for nl in newsletters:
    if nl.source not in by_source:
        by_source[nl.source] = []
    by_source[nl.source].append(nl)

for source, nls in sorted(by_source.items()):
    print(f"\n{source}: {len(nls)} newsletters")
    print("-" * 80)

    for nl in nls[:3]:  # Show first 3 from each source
        print(f"\n  Title: {nl.title}")
        print(f"  Date: {nl.published_date.strftime('%Y-%m-%d') if nl.published_date else 'N/A'}")
        print(f"  Summary: {nl.summary[:150]}..." if nl.summary else "  Summary: N/A")
        print(f"  Links: {len(nl.extracted_links) if nl.extracted_links else 0}")

    if len(nls) > 3:
        print(f"\n  ... and {len(nls) - 3} more")

print(f"\n{'='*80}")
print("Sample newsletter with full details:")
print(f"{'='*80}\n")

# Show one newsletter in detail
sample = newsletters[0]
print(f"Source: {sample.source}")
print(f"Title: {sample.title}")
print(f"Published: {sample.published_date.strftime('%Y-%m-%d %H:%M') if sample.published_date else 'N/A'}")
print(f"\nSummary:\n{sample.summary}\n")
print(f"Total Links: {len(sample.extracted_links) if sample.extracted_links else 0}")

if sample.extracted_links:
    print(f"\nFirst 5 Links:")
    for i, link in enumerate(sample.extracted_links[:5], 1):
        print(f"  {i}. {link['title']}")
        print(f"     {link['url']}")

session.close()
