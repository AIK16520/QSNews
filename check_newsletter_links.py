from src.utils.database import get_session, Newsletter

session = get_session()

# Get a newsletter with links
newsletters = session.query(Newsletter).limit(10).all()

for nl in newsletters:
    links = nl.extracted_links or []
    if links:
        print(f"\n{nl.source} - {nl.title[:60]}")
        print(f"  Number of links: {len(links)}")
        for i, link in enumerate(links[:3], 1):
            url = link.get('url', 'No URL')
            title = link.get('title', 'No title')
            print(f"  {i}. {title[:40]}")
            print(f"     URL: {url[:100]}")

session.close()
