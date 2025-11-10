import sqlite3
import json

conn = sqlite3.connect('data/articles.db')
cursor = conn.cursor()

cursor.execute('SELECT id, extracted_links FROM newsletters WHERE extracted_links IS NOT NULL')
rows = cursor.fetchall()

total_links = 0
tracking = 0
short_titles = 0

for row in rows:
    links = json.loads(row[1]) if row[1] else []
    total_links += len(links)
    tracking += sum(1 for link in links if 'utm_' in link.get('url', ''))
    short_titles += sum(1 for link in links if len(link.get('title', '')) <= 10)

print(f'Total newsletters with links: {len(rows)}')
print(f'Total links: {total_links}')
print(f'Links still with tracking: {tracking} ({tracking/total_links*100:.1f}%)')
print(f'Links with short titles (<=10 chars): {short_titles} ({short_titles/total_links*100:.1f}%)')

cleaned_count = sum(1 for row in rows if row[0] <= 20)
uncleaned_count = len(rows) - cleaned_count
print(f'\nCleaned newsletters (IDs 1-20): {cleaned_count}')
print(f'Remaining to clean: {uncleaned_count}')

conn.close()
