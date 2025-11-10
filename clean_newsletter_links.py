"""
Comprehensive Newsletter Link Cleaner
Cleans and improves link quality in newsletters using AI and NLP methods.

This script:
1. Removes tracking parameters from URLs
2. Improves bad/uninformative link titles using AI
3. Removes duplicate links within each newsletter
4. Filters out spam/promotional links
5. Validates URL quality
"""

import sqlite3
import json
import os
import re
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from collections import Counter
import openai
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# URL CLEANING
# ============================================================================

def clean_tracking_parameters(url: str) -> str:
    """
    Remove tracking parameters from URLs while keeping essential parameters.
    """
    try:
        parsed = urlparse(url)
        if not parsed.query:
            return url

        # Parse query parameters
        params = parse_qs(parsed.query, keep_blank_values=True)

        # Tracking parameters to remove
        tracking_params = [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'gaa_at', 'gaa_source', 'gaa_medium', 'gaa_campaign',
            'mc_cid', 'mc_eid',  # Mailchimp
            'ref', 'referrer',
            'source', 'campaign',
            'itm_source', 'itm_medium', 'itm_campaign',
            '_hsenc', '_hsmi',  # HubSpot
            'fbclid', 'gclid', 'msclkid',  # Ad tracking
        ]

        # Remove tracking parameters
        cleaned_params = {k: v for k, v in params.items() if k.lower() not in tracking_params}

        # Rebuild URL
        if cleaned_params:
            # Convert back to query string
            new_query = urlencode(cleaned_params, doseq=True)
            cleaned = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
        else:
            # No parameters left, return URL without query string
            cleaned = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                '',
                parsed.fragment
            ))

        return cleaned

    except Exception as e:
        logger.warning(f"Error cleaning URL parameters: {e}")
        return url


def is_valid_url(url: str) -> bool:
    """Check if URL is valid and accessible."""
    try:
        parsed = urlparse(url)
        return all([parsed.scheme in ['http', 'https'], parsed.netloc])
    except:
        return False


# ============================================================================
# LINK QUALITY FILTERING
# ============================================================================

def should_filter_link(link: Dict) -> bool:
    """
    Determine if a link should be filtered out entirely.
    Returns True if link should be removed.
    INVESTOR GRADE: Be extremely aggressive - filter ANY promotional/navigation content.
    """
    title = link.get('title', '').lower().strip()
    url = link.get('url', '').lower()

    # COMPREHENSIVE filter patterns
    FILTER_PATTERNS = [
        # Subscription/promotional
        r'(subscribe|unsubscribe|sign up|signup)',
        r'(register now|register for)',
        r'(manage.*(subscription|email|preferences))',
        r'(update.*(newsletter|email)\s+preferences)',
        r'(email.*(forwarded|preferences))',
        r'(advertise|sponsor|advertising|ad\s+spot)',
        r'(advertise with us|contact us|get in touch)',
        r'(learn more\.|read more\.|click here\.)',
        r'(you\'re currently a.*subscriber)',
        r'(free subscriber to)',

        # Navigation/utility
        r'(settings|preferences|profile)',
        r'(privacy policy|terms of service|about us)',
        r'(view in browser|view online|web version)',

        # Social media prompts
        r'(follow us|social media)',
        r'(subscribe to our)',

        # Newsletter self-promotion
        r'(trending ai tools)',
        r'(discover for free)',
        r'(everything else in)',
        r'(get axios|axios pro|axios hq)',

        # Generic incomplete fragments
        r'^(currently shows)$',
        r'^(its .* page)$',
        r'^(a new .*)$',
        r'(stateside)$',

        # Combined navigation (with pipes or separators)
        r'(sign up\|)',
        r'(advertise\|)',
        r'(view online\|)',
        r'(update newsletter)',

        # Investment fragments (Chief AI Office) - FILTER OUT ENTIRELY
        r'^why .* invested',
        r'(periodic labs|axiom|madrona|felicis|b capital|andreessen horowitz)$',
    ]

    for pattern in FILTER_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            logger.debug(f"Filtering link: {title}")
            return True

    # Filter by URL patterns
    URL_FILTER = [
        '/unsubscribe',
        '/manage-subscription',
        '/preferences',
        '/subscribe',
        '/signup',
        'adjust.com',
        'convertkit-mail',
        'list-manage.com',
        'email.mg',
    ]

    for pattern in URL_FILTER:
        if pattern in url:
            logger.debug(f"Filtering URL: {url}")
            return True

    return False


def is_bad_title(title: str) -> bool:
    """
    Determine if a link title is bad/uninformative.
    INVESTOR-GRADE: Be strict - any ambiguous or unclear title should be improved.
    """
    title_clean = title.strip()
    title_lower = title_clean.lower()

    # Empty or very short (except known abbreviations)
    if len(title_clean) <= 2 and title_clean.upper() not in ['AI', 'ML', 'RL', 'NLP', 'GPT']:
        return True

    # Single common words that are likely anchor text from sentences
    # INVESTOR GRADE: Be extremely comprehensive
    COMMON_VERBS = [
        # Action verbs
        'reportedly', 'pressed', 'signed', 'wrote', 'filed', 'said', 'says', 'reports',
        'pulled', 'pulling', 'backlash', 'became', 'signing', 'relaunching', 'announced',
        'released', 'launched', 'unveiled', 'revealed', 'confirmed', 'denied',
        'claims', 'suggests', 'shows', 'finds', 'discover', 'see', 'view',
        'read', 'learn', 'check', 'get', 'download', 'install',
        'told', 'telling', 'added', 'noted', 'stated', 'mentioned', 'explained',
        'described', 'shared', 'posted', 'publishing', 'published', 'discussed',
        'highlighted', 'emphasized', 'focusing', 'targeting', 'planning', 'considering',
        # More verbs commonly used as link anchors
        'working', 'developed', 'developing', 'come', 'coming', 'building', 'built',
        'secured', 'raised', 'raising', 'funded', 'funding', 'acquired', 'acquiring',
        'hired', 'hiring', 'joined', 'joining', 'left', 'leaving', 'moving', 'moved',
        'started', 'starting', 'ended', 'ending', 'closed', 'closing', 'opened', 'opening',
        'tested', 'testing', 'tried', 'trying', 'used', 'using', 'made', 'making',
        'created', 'creating', 'designed', 'designing', 'studied', 'studying',
    ]

    if title_lower in COMMON_VERBS:
        return True

    # Sentence fragments (common in newsletters)
    SENTENCE_FRAGMENTS = [
        'can help', 'will help', 'could help', 'may help',
        'driving the news', 'why it matters', "what they're saying",
        'yes, but', 'the big picture', 'go deeper', 'between the lines',
        'the bottom line', 'what to watch', "what's next",
        'slated to close', 'set to launch', 'expected to',
        'controversy', 'model', 'initiative', 'program', 'project',
        'to power', 'log in', 'sign in', 'the hustle',
        'currently shows', 'stateside',
        # Investment-related (Chief AI Office)
        'periodic labs', 'axiom', 'madrona', 'felicis', 'b capital',
        'andreessen horowitz',
    ]

    if title_lower in SENTENCE_FRAGMENTS:
        return True

    # Investment fragments: "Why X invested" - incomplete, not useful
    if title_lower.startswith('why ') and 'invest' in title_lower:
        # These are incomplete fragments from Chief AI Office newsletters
        return True

    # Financial/sentence fragments (incomplete context)
    # Examples: "for $250 million", "$15 billion valuation in 2022."
    if re.search(r'^\$\d+|for \$\d+|\d+ (billion|million) valuation', title_lower):
        # Only flag if it's short (< 5 words) - longer context is OK
        if len(title_clean.split()) < 5:
            return True

    # Single names without context (journalist names, but NOT product names)
    if len(title_clean.split()) <= 2 and len(title_clean) < 20:
        # If it looks like a person's name (two title-cased words)
        words = title_clean.split()
        if len(words) == 2 and all(w[0].isupper() for w in words if w):
            # Check if it's a tech product/feature name (contains tech keywords)
            tech_keywords = ['ai', 'code', 'studio', 'hq', 'os', 'sdk', 'api', 'ocr',
                           'firefly', 'gemini', 'claude', 'gpt', 'enterprise', 'premium',
                           'agent', 'dash', 'mode', 'suite', 'opal', 'comet', 'patents',
                           'realtime', 'deepseek', 'perplexity', 'elevenlabs', 'krea',
                           'encord', 'builder', 'engineering', 'cameos', 'kilo']

            # If contains tech keyword, it's probably a product name - keep it
            if any(keyword in title_lower for keyword in tech_keywords):
                return False

            # Otherwise, it might be a person's name - flag it
            # Exception: Well-known people who are often linked
            known_ok = ['steve jobs', 'bill gates', 'elon musk', 'sam altman']
            if title_lower not in known_ok:
                return True

    # Structural phrases (used for newsletter sections)
    if any(title_lower.startswith(phrase) for phrase in [
        'why it matters', 'driving the news', "what they're", 'yes, but',
        'the big picture', 'what to watch', 'between the lines'
    ]):
        return True

    # Generic link text and navigation
    GENERIC_TERMS = [
        'link', 'here', 'click here', 'read more', 'see more', 'learn more',
        'view more', 'more info', 'more information', 'details',
        'learn more.', 'read more.', 'click here.',  # with periods
    ]

    if title_lower in GENERIC_TERMS:
        return True

    # Brand names or company names alone (without context) - usually not good link titles
    # Exception: if it's a well-known company and the only content
    SHORT_NAMES_ONLY = [
        'axios hq', 'axios', 'the hustle',  # Newsletter self-references
    ]

    if title_lower in SHORT_NAMES_ONLY:
        return True

    # Titles ending with prepositions/conjunctions (clearly incomplete)
    # BUT: Only flag SHORT titles - longer ones are likely complete phrases
    if re.search(r'\b(and|or|but|with|for|to|in|on|at|by|of)$', title_lower):
        # Only flag if it's short (< 6 words) - longer titles are likely OK
        if len(title_clean.split()) < 6:
            return True

    # Very short titles (2 words or less, < 15 chars) that look like fragments
    if len(title_clean.split()) <= 2 and len(title_clean) < 15:
        # Exceptions for valid short brand names, terms, and financial terms
        exceptions = [
            'ai', 'ml', 'gpt', 'llm', 'nlp', 'openai', 'google', 'meta', 'apple',
            'amazon', 'microsoft', 'nvidia', 'anthropic', 'deepmind',
            'series a', 'series b', 'series c', 'series d', 'ipo', 'vc'
        ]

        # If it contains an exception term, it's probably OK
        if not any(exc in title_lower for exc in exceptions):
            # Check if it's just common words
            words = title_lower.split()
            common_words = ['the', 'a', 'an', 'to', 'for', 'of', 'in', 'on', 'at', 'by', 'with']

            # If first word is common or it's a fragment like "to power", it's bad
            if len(words) > 0 and (words[0] in common_words or
                                   (len(words) > 1 and words[0] in ['to', 'for', 'with', 'by'])):
                return True

    return False


# ============================================================================
# AI-POWERED TITLE IMPROVEMENT
# ============================================================================

def improve_link_title_with_ai(link: Dict, newsletter_context: str = "") -> str:
    """
    Use AI to generate a better, more descriptive title for a link.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.warning("OpenAI API key not found, falling back to context-based title")
        return improve_link_title_contextual(link)

    title = link.get('title', '')
    url = link.get('url', '')
    context = link.get('context', '')

    # Build prompt with available information
    prompt = f"""You are helping to create a concise, descriptive title for a link in an AI/tech newsletter.

Current title: "{title}"
URL: {url}
"""

    if context:
        prompt += f"Context from newsletter: {context}\n"

    if newsletter_context:
        prompt += f"Newsletter topic: {newsletter_context}\n"

    prompt += """
Generate a short, descriptive title (3-8 words) that clearly describes what this link is about.
The title should be professional and informative.

Rules:
- Be specific and descriptive
- Keep it concise (3-8 words)
- No emojis or special characters
- Focus on what the link is about, not generic terms like "article" or "post"
- Make it informative for AI/tech professionals

Examples of good titles:
- "OpenAI announces GPT-5 with 10T parameters"
- "Google releases new Gemini Pro model"
- "Meta's LLaMA 3 outperforms GPT-4"

Respond with ONLY the improved title, nothing else."""

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates clear, concise titles for links."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )

        improved_title = response.choices[0].message.content.strip()

        # Remove quotes if present
        improved_title = improved_title.strip('"\'')

        logger.info(f"Improved title: '{title}' → '{improved_title}'")
        return improved_title

    except Exception as e:
        logger.error(f"Error improving title with AI: {e}")
        return improve_link_title_contextual(link)


def improve_link_title_contextual(link: Dict) -> str:
    """
    Fallback: Improve link title using context and URL analysis (no AI).
    """
    title = link.get('title', '')
    url = link.get('url', '')
    context = link.get('context', '')

    # If context is good, use it
    if context and len(context) > 20:
        # Clean context (remove common prefixes)
        context_clean = re.sub(r'^(check out|read about|learn about|see)\s+', '', context, flags=re.IGNORECASE)
        context_clean = context_clean.strip()

        # Use first sentence if multiple
        if '.' in context_clean:
            context_clean = context_clean.split('.')[0]

        # Limit length
        if len(context_clean) > 80:
            context_clean = context_clean[:77] + '...'

        return context_clean

    # Try to extract from URL
    try:
        parsed = urlparse(url)
        path = parsed.path.strip('/')

        # Get last part of path
        if path:
            parts = path.split('/')
            last_part = parts[-1]

            # Convert URL slug to readable title
            if last_part and last_part not in ['index', 'index.html', 'index.php']:
                # Remove file extensions
                last_part = re.sub(r'\.(html|php|aspx|jsp)$', '', last_part)

                # Replace dashes/underscores with spaces
                readable = last_part.replace('-', ' ').replace('_', ' ')

                # Title case
                readable = readable.title()

                if len(readable) > 10:  # Only use if substantial
                    return readable

    except:
        pass

    # Last resort: use domain + original title
    try:
        domain = urlparse(url).netloc.replace('www.', '')
        return f"{title} from {domain}"
    except:
        return title


# ============================================================================
# MAIN CLEANING FUNCTION
# ============================================================================

def clean_newsletter_links(newsletter_id: int, links: List[Dict],
                          newsletter_summary: str = "",
                          use_ai: bool = True) -> List[Dict]:
    """
    Clean and improve links for a single newsletter.

    Args:
        newsletter_id: Newsletter database ID
        links: List of link dictionaries
        newsletter_summary: Summary of newsletter for context
        use_ai: Whether to use AI for title improvement

    Returns:
        Cleaned list of links
    """
    if not links:
        return []

    logger.info(f"Cleaning {len(links)} links for newsletter {newsletter_id}")

    cleaned_links = []
    seen_urls = set()
    filtered_count = 0
    duplicates_count = 0
    improved_titles_count = 0

    for link in links:
        # Step 1: Filter out spam/promotional links
        if should_filter_link(link):
            filtered_count += 1
            continue

        # Step 2: Clean URL (remove tracking)
        original_url = link.get('url', '')
        cleaned_url = clean_tracking_parameters(original_url)
        link['url'] = cleaned_url

        # Step 3: Check for duplicates (by cleaned URL)
        if cleaned_url in seen_urls:
            duplicates_count += 1
            continue
        seen_urls.add(cleaned_url)

        # Step 4: Validate URL
        if not is_valid_url(cleaned_url):
            logger.warning(f"Invalid URL filtered: {cleaned_url}")
            continue

        # Step 5: Improve bad titles
        title = link.get('title', '')
        if is_bad_title(title):
            if use_ai:
                improved_title = improve_link_title_with_ai(link, newsletter_summary)
            else:
                improved_title = improve_link_title_contextual(link)

            link['title'] = improved_title
            improved_titles_count += 1

        cleaned_links.append(link)

    logger.info(f"Newsletter {newsletter_id}: Kept {len(cleaned_links)}/{len(links)} links")
    logger.info(f"  Filtered: {filtered_count}, Duplicates: {duplicates_count}, Improved titles: {improved_titles_count}")

    return cleaned_links


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def clean_all_newsletters(dry_run: bool = True, use_ai: bool = True, limit: Optional[int] = None):
    """
    Clean links for all newsletters in database.

    Args:
        dry_run: If True, don't write changes to database
        use_ai: Whether to use AI for title improvement
        limit: Optional limit on number of newsletters to process
    """
    conn = sqlite3.connect('data/articles.db')
    cursor = conn.cursor()

    # Get all newsletters with links
    query = 'SELECT id, title, summary, extracted_links FROM newsletters WHERE extracted_links IS NOT NULL'
    if limit:
        query += f' LIMIT {limit}'

    cursor.execute(query)
    newsletters = cursor.fetchall()

    logger.info(f"Processing {len(newsletters)} newsletters (dry_run={dry_run}, use_ai={use_ai})")

    total_original_links = 0
    total_cleaned_links = 0

    for row in newsletters:
        newsletter_id = row[0]
        title = row[1]
        summary = row[2] or ""
        links = json.loads(row[3]) if row[3] else []

        total_original_links += len(links)

        # Clean links
        cleaned_links = clean_newsletter_links(
            newsletter_id,
            links,
            newsletter_summary=summary,
            use_ai=use_ai
        )

        total_cleaned_links += len(cleaned_links)

        # Update database
        if not dry_run:
            links_json = json.dumps(cleaned_links)
            cursor.execute(
                'UPDATE newsletters SET extracted_links = ? WHERE id = ?',
                (links_json, newsletter_id)
            )

    if not dry_run:
        conn.commit()
        logger.info("Changes committed to database")
    else:
        logger.info("DRY RUN - No changes made to database")

    conn.close()

    logger.info(f"\n=== SUMMARY ===")
    logger.info(f"Total newsletters processed: {len(newsletters)}")
    logger.info(f"Total original links: {total_original_links}")
    logger.info(f"Total cleaned links: {total_cleaned_links}")
    logger.info(f"Links removed: {total_original_links - total_cleaned_links}")
    logger.info(f"Reduction: {(total_original_links - total_cleaned_links) / total_original_links * 100:.1f}%")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Clean newsletter links')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Run without making changes to database (default: True)')
    parser.add_argument('--no-dry-run', action='store_true',
                       help='Actually write changes to database')
    parser.add_argument('--no-ai', action='store_true',
                       help='Disable AI title improvement (faster, but lower quality)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of newsletters to process (for testing)')

    args = parser.parse_args()

    dry_run = not args.no_dry_run
    use_ai = not args.no_ai

    logger.info(f"Starting link cleaning (dry_run={dry_run}, use_ai={use_ai})")

    clean_all_newsletters(
        dry_run=dry_run,
        use_ai=use_ai,
        limit=args.limit
    )
