from src.utils.database import get_session, Newsletter

session = get_session()
nl = session.query(Newsletter).filter(Newsletter.title.like('%weekend%')).first()

print('Title:', nl.title)
print('\nExtracted links:')
links = nl.extracted_links or []
for i, link in enumerate(links[:5], 1):
    title = link.get('title', 'No title')
    url = link.get('url', 'No URL')
    print(f'{i}. {title}')
    print(f'   URL: {url[:100]}...')

print('\nSummary:')
print(nl.summary)

session.close()
