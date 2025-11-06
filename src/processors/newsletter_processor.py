"""
Newsletter Processor Module
Processes newsletters: generates summaries with embedded links using AI.
"""

import logging
import os
import json
from typing import Dict, List
from bs4 import BeautifulSoup
import openai

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clean_html_content(html_content: str) -> str:
    """
    Clean HTML content to extract readable text while preserving link structure.

    Returns:
        Cleaned text with link markers
    """
    if not html_content:
        return ""

    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(['script', 'style', 'head', 'meta']):
            script.decompose()

        # Get text
        text = soup.get_text(separator='\n', strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        cleaned = '\n'.join(line for line in lines if line)

        return cleaned
    except Exception as e:
        logger.warning(f"Error cleaning HTML: {e}")
        return html_content[:5000]  # Fallback to first 5000 chars


def generate_newsletter_summary(
    newsletter_data: Dict,
    max_length: int = 300
) -> str:
    """
    Generate a brief summary of the newsletter with embedded links using AI.

    The summary should:
    - Be 2-3 sentences
    - Highlight main themes/topics
    - Include important links inline in markdown format: [text](url)

    Args:
        newsletter_data: Dictionary with newsletter content and links
        max_length: Maximum summary length in words

    Returns:
        Markdown-formatted summary with embedded links
    """
    source = newsletter_data.get('source', 'Newsletter')
    title = newsletter_data.get('email_subject', 'Untitled')
    html_content = newsletter_data.get('html_content', '')
    plain_text = newsletter_data.get('plain_text', '')
    extracted_links = newsletter_data.get('extracted_links', [])

    # Use plain text if available, otherwise clean HTML
    content = plain_text if plain_text else clean_html_content(html_content)

    # Limit content length for API (keep first 3000 chars)
    if len(content) > 3000:
        content = content[:3000] + "..."

    # Format links for context
    links_context = ""
    if extracted_links:
        links_context = "\n\nKey Links Found:\n"
        for i, link in enumerate(extracted_links[:10], 1):  # Top 10 links
            link_title = link.get('title', 'Link')
            link_url = link.get('url', '')
            links_context += f"{i}. {link_title}: {link_url}\n"

    # Check if OpenAI is available
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.warning("OpenAI API key not found, using fallback summary")
        return generate_fallback_summary(newsletter_data)

    try:
        client = openai.OpenAI(api_key=api_key)

        system_prompt = """You are an expert at summarizing newsletters. Create a brief 2-3 sentence summary that:
1. Highlights the main themes and topics covered
2. Embeds the most important/relevant links inline using markdown format: [descriptive text](url)
3. Is concise and informative
4. Focuses on what matters most to AI/tech/VC professionals
5. Does NOT use any emojis - use plain text only

Example format:
"This week's newsletter covers [OpenAI's new GPT-5 announcement](https://example.com), discusses [implications for enterprise AI](https://example2.com), and highlights [3 new coding tools](https://example3.com) that boost developer productivity."
"""

        user_prompt = f"""Summarize this newsletter from {source}:

Title: {title}

Content:
{content}
{links_context}

Create a 2-3 sentence summary with embedded markdown links to the most relevant articles/topics."""

        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )

        summary = response.choices[0].message.content.strip()
        logger.info(f"Generated AI summary for {source}: {len(summary)} chars")
        return summary

    except Exception as e:
        logger.error(f"Error generating AI summary: {e}")
        return generate_fallback_summary(newsletter_data)


def generate_fallback_summary(newsletter_data: Dict) -> str:
    """
    Generate a simple fallback summary without AI.
    Just lists the top links.
    """
    source = newsletter_data.get('source', 'Newsletter')
    extracted_links = newsletter_data.get('extracted_links', [])

    if not extracted_links:
        return f"Newsletter from {source} (no links extracted)"

    # Create summary with top 3 links
    summary_parts = [f"This {source} newsletter covers:"]

    for i, link in enumerate(extracted_links[:3], 1):
        title = link.get('title', 'Link')
        url = link.get('url', '')
        summary_parts.append(f"[{title}]({url})")

    return " ".join(summary_parts[:1]) + " " + ", ".join(summary_parts[1:]) + "."


def extract_newsletter_tags(title: str, summary: str) -> List[str]:
    """
    Extract topic tags from newsletter using OpenAI API.
    Uses the same CATEGORIES from config.py that are used for articles.
    Returns a list of category names like ["Tools and Products", "Research and Studies"]
    """
    # Import categories from config
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    import config

    categories = config.CATEGORIES

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        # Fallback to keyword matching
        tags = []
        text = (title + " " + (summary or "")).lower()

        if any(word in text for word in ['tool', 'product', 'launch', 'release', 'app', 'platform']):
            tags.append('Tools and Products')
        if any(word in text for word in ['research', 'paper', 'study', 'academic']):
            tags.append('Research and Studies')
        if any(word in text for word in ['regulation', 'legal', 'law', 'policy', 'compliance']):
            tags.append('Legal and Regulations')
        if any(word in text for word in ['funding', 'investment', 'acquisition', 'merger', 'raised']):
            tags.append('Funding and M&A')

        return tags[:2]

    try:
        client = openai.OpenAI(api_key=api_key)

        # Format categories for prompt
        categories_list = '\n'.join([f"- {cat}" for cat in categories])

        prompt = f"""You are analyzing a newsletter to extract relevant category tags.

NEWSLETTER TITLE:
{title}

NEWSLETTER SUMMARY:
{summary or "No summary available"}

TASK:
Extract 1-3 relevant category tags that best categorize this newsletter's main themes.

AVAILABLE CATEGORIES (choose 1-3):
{categories_list}

RESPONSE FORMAT:
Respond ONLY with valid JSON:
{{
  "tags": ["Category 1", "Category 2"]
}}

Use ONLY categories from the list above. Choose 1-3 most relevant categories. Use the EXACT category names as shown."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts category tags. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        tags_list = result.get('tags', [])

        # Validate tags against actual categories
        tags = [tag for tag in tags_list if tag in categories]

        logger.info(f"Extracted {len(tags)} tags for newsletter: {tags}")
        return tags[:3]

    except Exception as e:
        logger.error(f"Error extracting tags: {e}")
        # Fallback to basic keyword matching
        tags = []
        text = (title + " " + (summary or "")).lower()

        if any(word in text for word in ['tool', 'product', 'launch']):
            tags.append('Tools and Products')
        if any(word in text for word in ['research', 'study']):
            tags.append('Research and Studies')

        return tags[:2]


def extract_newsletter_industries(title: str, summary: str) -> List[str]:
    """
    Extract industry tags from newsletter using OpenAI API.
    Uses the same INDUSTRIES from config.py that are used for articles.
    Returns a list of industry names like ["Healthcare", "Finance", "Enterprise"]
    """
    # Import industries from config
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    import config
    
    industries_list = config.INDUSTRIES
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        # Fallback to keyword matching
        industries = []
        text = (title + " " + (summary or "")).lower()
        
        if any(word in text for word in ['healthcare', 'medical', 'health', 'biotech', 'pharma']):
            industries.append('Healthcare')
        if any(word in text for word in ['finance', 'fintech', 'banking', 'payment']):
            industries.append('Finance')
        if any(word in text for word in ['enterprise', 'business', 'b2b', 'corporate']):
            industries.append('Enterprise')
        if any(word in text for word in ['education', 'edtech', 'learning', 'training']):
            industries.append('Education')
        
        return industries[:2]
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Format industries for prompt
        industries_formatted = '\n'.join([f"- {ind}" for ind in industries_list])
        
        prompt = f"""You are analyzing a newsletter to extract relevant industry tags.

NEWSLETTER TITLE:
{title}

NEWSLETTER SUMMARY:
{summary or "No summary available"}

TASK:
Extract 1-3 relevant industry tags that best represent the industries discussed in this newsletter.

AVAILABLE INDUSTRIES (choose 1-3):
{industries_formatted}

RESPONSE FORMAT:
Respond ONLY with valid JSON:
{{
  "industries": ["Industry 1", "Industry 2"]
}}

Use ONLY industries from the list above. Choose 1-3 most relevant industries. Use the EXACT industry names as shown."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts industry tags. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        industries_result = result.get('industries', [])
        
        # Validate industries against actual list
        industries = [ind for ind in industries_result if ind in industries_list]
        
        logger.info(f"Extracted {len(industries)} industries for newsletter: {industries}")
        return industries[:3]
    
    except Exception as e:
        logger.error(f"Error extracting industries: {e}")
        # Fallback to basic keyword matching
        industries = []
        text = (title + " " + (summary or "")).lower()
        
        if any(word in text for word in ['healthcare', 'medical']):
            industries.append('Healthcare')
        if any(word in text for word in ['finance', 'fintech']):
            industries.append('Finance')
        
        return industries[:2]


def extract_newsletter_title(newsletter_data: Dict) -> str:
    """
    Extract a clean title from the newsletter.
    Falls back to email subject if no better title found.
    """
    email_subject = newsletter_data.get('email_subject', '')
    source = newsletter_data.get('source', '')

    # Clean up common subject line prefixes
    title = email_subject

    # Remove common prefixes
    prefixes_to_remove = [
        f"{source} - ",
        f"{source}: ",
        "Newsletter: ",
        "Weekly: ",
        "Daily: ",
        "Re: ",
        "Fwd: ",
    ]

    for prefix in prefixes_to_remove:
        if title.startswith(prefix):
            title = title[len(prefix):]

    # Remove emojis at start
    while title and not title[0].isalnum():
        title = title[1:].strip()

    # If title is too generic, use source + date
    if not title or len(title) < 10:
        received_date = newsletter_data.get('received_date')
        if received_date:
            title = f"{source} - {received_date.strftime('%B %d, %Y')}"
        else:
            title = f"{source} Newsletter"

    return title


if __name__ == "__main__":
    # Test the processor
    print("Newsletter Processor Module")
    print("This module requires newsletter data to test.")

    # Test with sample data
    sample_data = {
        'source': 'Test Newsletter',
        'email_subject': '🚀 Welcome to Test Newsletter',
        'html_content': '<html><body><h1>Test</h1><p>This is a test newsletter about <a href="https://example.com">AI developments</a>.</p></body></html>',
        'plain_text': 'Test Newsletter\n\nThis is a test newsletter about AI developments.',
        'extracted_links': [
            {'title': 'AI Developments', 'url': 'https://example.com', 'context': 'Latest AI news'}
        ]
    }

    print("\nTesting title extraction...")
    title = extract_newsletter_title(sample_data)
    print(f"Title: {title}")

    print("\nTesting summary generation...")
    summary = generate_newsletter_summary(sample_data)
    print(f"Summary: {summary}")
