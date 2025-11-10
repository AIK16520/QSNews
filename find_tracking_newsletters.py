"""Find newsletters with tracking links."""
from src.utils.database import get_session, Newsletter

session = get_session()

# Get all newsletters
newsletters = session.query(Newsletter).all()

print(f"Checking {len(newsletters)} newsletters for tracking links...\n")

tracking_newsletters = []

for nl in newsletters:
    links = nl.extracted_links or []
    if not links:
        continue

    # Check for tracking domains
    tracking_domains = ['elink', 'insidr.ai', 'link.gettheelevator', 'link.mail.beehiiv']

    for link in links:
        url = link.get('url', '')

        # Check if URL contains tracking domain or is very long
        is_tracking = any(domain in url for domain in tracking_domains) or len(url) > 400

        if is_tracking:
            tracking_newsletters.append({
                'newsletter': nl,
                'source': nl.source,
                'title': nl.title,
                'url': url[:100]
            })
            break  # Only need to find one tracking link per newsletter

print(f"Found {len(tracking_newsletters)} newsletters with tracking links:\n")

for item in tracking_newsletters[:20]:  # Show first 20
    print(f"{item['source']} - {item['title'][:60]}")
    print(f"  Tracking URL: {item['url']}...")
    print()

session.close()
