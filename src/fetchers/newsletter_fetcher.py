"""
Newsletter Fetcher Module
Fetches newsletters from Gmail inbox via IMAP.
"""

import os
import sys
import imaplib
import email
import logging
from email.header import decode_header
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
from bs4 import BeautifulSoup

# Add parent directory to path for config import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import improved link extractor
from src.utils.link_extractor import extract_and_explain_links

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def connect_to_gmail(gmail_user: str, gmail_pass: str) -> Optional[imaplib.IMAP4_SSL]:
    """
    Connect to Gmail via IMAP.

    Args:
        gmail_user: Gmail email address
        gmail_pass: Gmail password or app password

    Returns:
        IMAP connection object or None if failed
    """
    try:
        logger.info(f"Connecting to Gmail for {gmail_user}")
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(gmail_user, gmail_pass)
        logger.info("Successfully connected to Gmail")
        return imap
    except Exception as e:
        logger.error(f"Failed to connect to Gmail: {e}")
        return None


def decode_email_subject(subject: str) -> str:
    """Decode email subject that might be encoded."""
    decoded_parts = []
    for part, encoding in decode_header(subject):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
        else:
            decoded_parts.append(part)
    return ''.join(decoded_parts)


def extract_email_body(msg: email.message.Message) -> tuple[str, str]:
    """
    Extract plain text and HTML body from email message.

    Returns:
        Tuple of (plain_text, html_content)
    """
    plain_text = ""
    html_content = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()

            try:
                body = part.get_payload(decode=True)
                if body:
                    if content_type == "text/plain":
                        plain_text = body.decode('utf-8', errors='ignore')
                    elif content_type == "text/html":
                        html_content = body.decode('utf-8', errors='ignore')
            except Exception as e:
                logger.warning(f"Error extracting email part: {e}")
                continue
    else:
        # Not multipart
        content_type = msg.get_content_type()
        try:
            body = msg.get_payload(decode=True)
            if body:
                if content_type == "text/plain":
                    plain_text = body.decode('utf-8', errors='ignore')
                elif content_type == "text/html":
                    html_content = body.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"Error extracting email body: {e}")

    return plain_text, html_content


def extract_links_from_html(html_content: str) -> List[Dict[str, str]]:
    """
    Extract all links from HTML content with context.

    Returns:
        List of dicts with {title, url, context}
    """
    if not html_content:
        return []

    links = []
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all <a> tags
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']

            # Skip non-http links (mailto, tel, etc.)
            if not href.startswith('http'):
                continue

            # Get link text
            link_text = a_tag.get_text(strip=True)

            # Get surrounding context (parent text)
            parent = a_tag.parent
            context = parent.get_text(strip=True) if parent else ""

            # Limit context length
            if len(context) > 200:
                context = context[:200] + "..."

            links.append({
                'title': link_text or 'Link',
                'url': href,
                'context': context
            })

    except Exception as e:
        logger.warning(f"Error extracting links from HTML: {e}")

    return links


def identify_newsletter_source(from_email: str, subject: str) -> str:
    """
    Identify newsletter source from email address and subject.

    Returns:
        Newsletter name (e.g., "The Rundown", "Ben's Bites")
    """
    from_email = from_email.lower()
    subject = subject.lower()

    # Map email patterns to newsletter names
    patterns = {
        'therundown.ai': 'The Rundown',
        'rundownai': 'The Rundown',
        'bensbites': "Ben's Bites",
        'superhuman.ai': 'Superhuman AI',
        'superhumanai': 'Superhuman AI',
        'theneuron.ai': 'The Neuron',
        'tldr.tech': 'TLDR AI',
        'tldrai': 'TLDR AI',
        'finxter': 'Finxter Daily AI Tips',
        'mindstream': 'Mindstream',
        'neatprompts': 'Prompt Engineering Daily',
        'lastweekin.ai': 'Last Week in AI',
        'thesequence': 'TheSequence',
        'oneusefulthing': 'One Useful Thing',
        'futuretools': 'Future Tools',
        'aibreakfast': 'AI Breakfast',
        'importai': 'Import AI',
        'interconnects': 'Interconnects',
        'latent.space': 'Latent Space',
        'chain-of-thought': 'Chain of Thought',
        'thealgorithmicbridge': 'The Algorithmic Bridge',
        'synthedia': 'Synthedia',
        'dataelixir': 'Data Elixir',
        'llmsresearch': 'LLMs Research',
    }

    for pattern, name in patterns.items():
        if pattern in from_email or pattern in subject:
            return name

    # If no match, extract domain from email
    match = re.search(r'@([a-zA-Z0-9.-]+)', from_email)
    if match:
        domain = match.group(1)
        return domain.replace('.com', '').replace('.ai', '').title()

    return 'Unknown Newsletter'


def fetch_newsletters_from_gmail(
    days_back: int = 30,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Fetch newsletters from Gmail inbox.

    Args:
        days_back: How many days back to fetch (default 30)
        limit: Maximum number of emails to fetch (None for all)

    Returns:
        List of newsletter dictionaries
    """
    import config
    gmail_user = config.NEWSLETTER_GMAIL
    gmail_pass = config.NEWSLETTER_PASS

    if not gmail_user or not gmail_pass:
        logger.error("Newsletter Gmail credentials not found in environment")
        return []

    imap = connect_to_gmail(gmail_user, gmail_pass)
    if not imap:
        return []

    newsletters = []

    try:
        # Select inbox
        imap.select('INBOX')

        # Calculate date for search
        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")

        # Search for emails since date
        logger.info(f"Searching for emails since {since_date}")
        status, messages = imap.search(None, f'(SINCE {since_date})')

        if status != 'OK':
            logger.error("Failed to search emails")
            return []

        email_ids = messages[0].split()
        total_emails = len(email_ids)
        logger.info(f"Found {total_emails} emails")

        # Apply limit if specified
        if limit:
            email_ids = email_ids[-limit:]  # Get most recent ones
            logger.info(f"Limiting to {len(email_ids)} most recent emails")

        # Fetch each email
        for i, email_id in enumerate(email_ids, 1):
            try:
                status, msg_data = imap.fetch(email_id, '(RFC822)')

                if status != 'OK':
                    continue

                # Parse email
                msg = email.message_from_bytes(msg_data[0][1])

                # Extract metadata
                subject = decode_email_subject(msg.get('Subject', ''))
                from_email = msg.get('From', '')
                date_str = msg.get('Date', '')

                # Parse date
                try:
                    email_date = email.utils.parsedate_to_datetime(date_str)
                except:
                    email_date = datetime.now()

                # Extract body
                plain_text, html_content = extract_email_body(msg)

                # Identify source first (needed for link extraction)
                source = identify_newsletter_source(from_email, subject)

                # Extract links with improved extraction
                links = extract_and_explain_links(html_content, source=source)

                newsletter = {
                    'email_subject': subject,
                    'source': source,
                    'from_email': from_email,
                    'received_date': email_date,
                    'plain_text': plain_text,
                    'html_content': html_content,
                    'extracted_links': links,
                    'total_links': len(links)
                }

                newsletters.append(newsletter)

                logger.info(f"[{i}/{len(email_ids)}] Fetched: {source} - {subject[:60]}")

            except Exception as e:
                logger.error(f"Error fetching email {email_id}: {e}")
                continue

        logger.info(f"Successfully fetched {len(newsletters)} newsletters")

    except Exception as e:
        logger.error(f"Error fetching newsletters: {e}")

    finally:
        try:
            imap.close()
            imap.logout()
        except:
            pass

    return newsletters


def list_subscribed_newsletters(days_back: int = 7) -> Dict[str, int]:
    """
    List all newsletters we're subscribed to and their counts.

    Returns:
        Dictionary mapping newsletter source to count
    """
    newsletters = fetch_newsletters_from_gmail(days_back=days_back)

    # Count by source
    source_counts = {}
    for newsletter in newsletters:
        source = newsletter['source']
        source_counts[source] = source_counts.get(source, 0) + 1

    return source_counts


if __name__ == "__main__":
    # Test the fetcher
    print("\n" + "="*80)
    print("CHECKING NEWSLETTER SUBSCRIPTIONS")
    print("="*80 + "\n")

    # List subscribed newsletters
    print("Checking newsletters from the past 7 days...\n")
    subscriptions = list_subscribed_newsletters(days_back=7)

    if subscriptions:
        print(f"Found {len(subscriptions)} different newsletter sources:\n")
        for source, count in sorted(subscriptions.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count} emails")
    else:
        print("No newsletters found. Make sure you've subscribed to some newsletters.")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")
