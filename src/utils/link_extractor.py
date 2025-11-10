"""
Enhanced Link Extraction Utility
Intelligently extracts links from newsletter HTML with better context and filtering.
"""

import re
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Navigation/utility link patterns to filter out
UTILITY_LINK_PATTERNS = [
    # Common navigation
    r'^(sign up|subscribe|unsubscribe|preferences|settings)$',
    r'^(read online|view in browser|web version)$',
    r'^(advertise|sponsor|advertising)$',
    r'^(about|about us|contact|contact us)$',
    r'^(privacy|privacy policy|terms|terms of service)$',
    r'^(follow us|social|twitter|linkedin|facebook)$',
    r'^(download|get the app|install)$',

    # App store links
    r'(app store|google play|microsoft store)',

    # Generic/empty
    r'^(link|here|click here|read more)$',
    r'^(see more|learn more|view more)$',
    r'^(share|forward|forward to a friend)$',

    # Single words that are likely navigation
    r'^(home|archive|blog|newsletter|feed)$',

    # Promotional/spam patterns
    r'(ai marketplace)',
    r'(access our database)',
    r'(funding database)',
    r'(chief ai office pro)',
    r'(for free|get free access)',
    r'(referral|refer a friend)',
    r'(\d+\+?\s*(ai\s*)?startups)',  # "2000+ AI Startups"
]

# URL patterns to filter out
URL_FILTER_PATTERNS = [
    # Tracking and utility URLs
    r'unsubscribe',
    r'preferences',
    r'manage-subscription',
    r'/subscribe',
    r'/signup',
    r'app\.adjust\.com',
    r'click\.convertkit-mail',
    r'email\.mg\.',
    r'mandrillapp\.com',
    r'list-manage\.com',  # Mailchimp
    
    # Social media profile links (not articles)
    r'^https?://(www\.)?(twitter|x)\.com/[^/]+/?$',
    r'^https?://(www\.)?linkedin\.com/in/[^/]+/?$',
    r'^https?://(www\.)?facebook\.com/[^/]+/?$',
    
    # App store links
    r'apps\.apple\.com',
    r'play\.google\.com',
    r'microsoft\.com/store',
]


def should_filter_link(link_text: str, url: str) -> bool:
    """
    Determine if a link should be filtered out.
    
    Args:
        link_text: The anchor text of the link
        url: The URL
        
    Returns:
        True if link should be filtered out, False otherwise
    """
    # Check link text patterns
    link_text_lower = link_text.lower().strip()
    for pattern in UTILITY_LINK_PATTERNS:
        if re.search(pattern, link_text_lower, re.IGNORECASE):
            return True
    
    # Check URL patterns
    for pattern in URL_FILTER_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    
    # Filter very short link text (likely navigation)
    if len(link_text.strip()) <= 2 and link_text.strip() not in ['AI', 'ML', 'RL']:
        return True
    
    return False


def get_link_domain(url: str) -> str:
    """Extract clean domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        return domain
    except:
        return ''


def clean_tracking_url(url: str) -> str:
    """
    Clean tracking URLs and extract the real destination.

    Common tracking patterns:
    - marketing.statnews.com/e3t/... (email tracking)
    - click.convertkit-mail.com/...
    - email.mg.../c/...

    Args:
        url: Raw URL that might be a tracking link

    Returns:
        Cleaned URL (or original if not a tracking link)
    """
    try:
        # Only warn about extremely long URLs (>2000 chars), but don't truncate
        # Many newsletter tracking URLs are legitimately 500-1500 chars
        if len(url) > 2000:
            logger.warning(f"Very long URL detected ({len(url)} chars): {url[:100]}...")
            # Keep the full URL - it might still be valid

        # Known tracking domains
        tracking_domains = [
            'marketing.statnews.com',
            'click.convertkit-mail',
            'email.mg.',
            'mandrillapp.com',
            'list-manage.com',
            'links.ml.',
            'go.redirectingat.com',
            'link.mail.',
            'elinka',  # Common in Insidr and other newsletters
            'elinkaf',  # Variant
        ]

        # Check if this is a tracking URL
        is_tracking = any(domain in url for domain in tracking_domains)

        if is_tracking:
            # Try to extract destination from query parameters
            from urllib.parse import parse_qs, urlparse

            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)

            # Common parameter names for destination URLs
            destination_params = ['url', 'u', 'redirect', 'dest', 'destination', 'link', 'goto']

            for param in destination_params:
                if param in query_params:
                    destination = query_params[param][0]
                    if destination.startswith('http'):
                        logger.debug(f"Extracted destination from tracking URL: {destination}")
                        return destination

            # If we can't extract destination, keep the tracking URL but note it
            logger.debug(f"Could not extract destination from tracking URL: {url[:100]}")

        return url

    except Exception as e:
        logger.warning(f"Error cleaning tracking URL: {e}")
        return url


def extract_better_context(a_tag, soup) -> str:
    """
    Extract better contextual description for a link.
    Looks for surrounding text that explains what the link is about.
    
    Args:
        a_tag: BeautifulSoup anchor tag
        soup: BeautifulSoup object
        
    Returns:
        Contextual description string
    """
    # Strategy 1: Look for heading before the link
    heading = None
    for tag in a_tag.find_previous_siblings():
        if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b']:
            heading = tag.get_text(strip=True)
            break
    
    # Strategy 2: Get parent paragraph text
    parent = a_tag.parent
    parent_text = ''
    
    # Go up to find meaningful parent (p, td, div with text)
    current = a_tag.parent
    depth = 0
    while current and depth < 5:
        if current.name in ['p', 'td', 'li', 'div']:
            parent_text = current.get_text(strip=True)
            if len(parent_text) > 20:  # Meaningful amount of text
                break
        current = current.parent
        depth += 1
    
    # Strategy 3: Look for text immediately before link in same element
    previous_text = ''
    if a_tag.previous_sibling:
        if isinstance(a_tag.previous_sibling, str):
            previous_text = a_tag.previous_sibling.strip()
        else:
            previous_text = a_tag.previous_sibling.get_text(strip=True)
    
    # Strategy 4: Look for text immediately after link
    next_text = ''
    if a_tag.next_sibling:
        if isinstance(a_tag.next_sibling, str):
            next_text = a_tag.next_sibling.strip()
        else:
            next_text = a_tag.next_sibling.get_text(strip=True)
    
    # Build context intelligently
    context_parts = []
    
    # Use heading if it's relevant and not too long
    if heading and len(heading) < 100 and heading.lower() not in ['link', 'links', 'read more']:
        context_parts.append(heading)
    
    # Use previous text if meaningful
    if previous_text and len(previous_text) > 10 and len(previous_text) < 200:
        # Remove common prefixes
        previous_text = re.sub(r'^(check out|read about|learn about|see)\s+', '', previous_text, flags=re.IGNORECASE)
        context_parts.append(previous_text)
    
    # Use parent text as fallback if nothing else
    if not context_parts and parent_text:
        # Extract sentence containing the link
        sentences = re.split(r'[.!?]\s+', parent_text)
        for sentence in sentences:
            if len(sentence) > 15 and len(sentence) < 300:
                context_parts.append(sentence)
                break
    
    # Combine and clean
    context = ' - '.join(context_parts) if context_parts else ''
    
    # Clean up context
    context = re.sub(r'\s+', ' ', context)  # Remove extra whitespace
    context = context.strip()
    
    # Limit length
    if len(context) > 250:
        context = context[:247] + '...'
    
    return context


def extract_links_with_intelligence(html_content: str, source: str = '') -> List[Dict[str, str]]:
    """
    Extract links from HTML with intelligent filtering and context extraction.
    
    Args:
        html_content: HTML content to parse
        source: Newsletter source name (optional, for source-specific logic)
        
    Returns:
        List of dicts with {title, url, context, domain}
    """
    if not html_content:
        return []
    
    links = []
    seen_urls = set()  # Deduplication
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script, style, and other non-content tags
        for tag in soup(['script', 'style', 'meta', 'link', 'noscript']):
            tag.decompose()
        
        # Find all <a> tags
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']

            # Skip non-http links (mailto, tel, etc.)
            if not href.startswith('http'):
                continue

            # Clean tracking URLs and extract real destination
            href = clean_tracking_url(href)

            # Get link text
            link_text = a_tag.get_text(strip=True)
            
            # Skip if no text
            if not link_text:
                continue
            
            # Apply filters
            if should_filter_link(link_text, href):
                logger.debug(f"Filtered out: {link_text} - {href}")
                continue
            
            # Deduplicate by URL
            if href in seen_urls:
                continue
            seen_urls.add(href)
            
            # Extract better context
            context = extract_better_context(a_tag, soup)
            
            # Get domain for reference
            domain = get_link_domain(href)
            
            # Build link object
            link_obj = {
                'title': link_text,
                'url': href,
                'context': context,
                'domain': domain
            }
            
            links.append(link_obj)
            logger.debug(f"Extracted: {link_text} -> {context[:50]}")
        
        logger.info(f"Extracted {len(links)} quality links (filtered from total)")
        
    except Exception as e:
        logger.warning(f"Error extracting links from HTML: {e}")
    
    return links


def generate_link_explanation(link: Dict[str, str], use_ai: bool = False) -> str:
    """
    Generate a one-line explanation for a link.
    
    Args:
        link: Link dictionary with title, url, context, domain
        use_ai: Whether to use AI for explanation (future enhancement)
        
    Returns:
        One-line explanation string
    """
    title = link.get('title', 'Link')
    context = link.get('context', '')
    domain = link.get('domain', '')
    
    # If we have good context, use it
    if context and len(context) > 20:
        # Context already provides explanation
        explanation = context
    else:
        # Build explanation from title and domain
        if domain:
            domain_clean = domain.replace('.com', '').replace('.ai', '').replace('.io', '')
            explanation = f"{title} from {domain_clean}"
        else:
            explanation = title
    
    # Clean and format
    explanation = re.sub(r'\s+', ' ', explanation).strip()
    
    # Ensure it ends with proper punctuation
    if explanation and not explanation[-1] in '.!?':
        explanation += '.'
    
    return explanation


# Convenience function that combines extraction and explanation
def extract_and_explain_links(html_content: str, source: str = '') -> List[Dict[str, str]]:
    """
    Extract links and generate explanations in one go.
    
    Returns:
        List of dicts with {title, url, context, domain, explanation}
    """
    links = extract_links_with_intelligence(html_content, source)
    
    for link in links:
        link['explanation'] = generate_link_explanation(link)
    
    return links


if __name__ == "__main__":
    # Test with sample HTML
    test_html = """
    <html>
    <body>
        <h2>AI Research News</h2>
        <p>OpenAI announced their latest model. <a href="https://openai.com/research/gpt4">Read the paper</a></p>
        
        <p>Check out <a href="https://example.com/article">this breakthrough in computer vision</a> from Google.</p>
        
        <!-- These should be filtered -->
        <a href="https://newsletter.com/subscribe">Subscribe</a>
        <a href="https://newsletter.com/unsubscribe">Unsubscribe</a>
        <a href="https://twitter.com/someuser">Follow us</a>
    </body>
    </html>
    """
    
    print("Testing enhanced link extraction:\n")
    links = extract_and_explain_links(test_html)
    
    print(f"Found {len(links)} quality links:\n")
    for i, link in enumerate(links, 1):
        print(f"{i}. {link['title']}")
        print(f"   URL: {link['url']}")
        print(f"   Explanation: {link['explanation']}")
        print()




