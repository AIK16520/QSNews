"""
Newsletter Formatter - Creates StrictlyVC-style newsletter output
Organizes links by category and funding size with clean formatting
"""

import openai
import os
from datetime import datetime


def categorize_links(links):
    """
    Categorize links into sections based on their tags and content.

    Returns dict with categories:
    - top_news: Major news stories
    - funding_massive: $50M+ rounds
    - funding_big: $20M-50M rounds
    - funding_small: <$20M rounds
    - other: Everything else
    """
    categories = {
        'top_news': [],
        'funding_massive': [],
        'funding_big': [],
        'funding_small': [],
        'other': []
    }

    for link in links:
        title = link.get('title', '').lower()
        context = link.get('context', '').lower()
        combined_text = title + ' ' + context

        # Check if it's funding news
        is_funding = any(keyword in combined_text for keyword in [
            'raise', 'raised', 'funding', 'series', 'round', 'million', 'billion',
            'seed', 'venture', 'investment', 'valuation'
        ])

        if is_funding:
            # Try to extract amount
            import re

            # Look for amounts like $100M, $1.5B, etc
            amount_match = re.search(r'\$(\d+(?:\.\d+)?)\s*(m|b|million|billion)', combined_text, re.IGNORECASE)

            if amount_match:
                amount_num = float(amount_match.group(1))
                unit = amount_match.group(2).lower()

                # Convert to millions
                if unit.startswith('b'):
                    amount_millions = amount_num * 1000
                else:
                    amount_millions = amount_num

                # Categorize by size
                if amount_millions >= 50:
                    categories['funding_massive'].append(link)
                elif amount_millions >= 20:
                    categories['funding_big'].append(link)
                else:
                    categories['funding_small'].append(link)
            else:
                # No amount found, put in other
                categories['funding_small'].append(link)
        else:
            # Check if it's major news (regulation, policy, major company moves)
            is_major_news = any(keyword in combined_text for keyword in [
                'regulation', 'policy', 'government', 'sec', 'ftc',
                'openai', 'google', 'microsoft', 'meta', 'anthropic',
                'acquisition', 'merger', 'ipo', 'public',
                'partnership', 'deal', 'agreement'
            ])

            if is_major_news:
                categories['top_news'].append(link)
            else:
                categories['other'].append(link)

    return categories


def generate_strictlyvc_style_newsletter(selected_links, newsletter_title=None):
    """
    Generate a StrictlyVC-style formatted newsletter from selected links.

    Args:
        selected_links: List of link dicts with 'title', 'url', 'context'
        newsletter_title: Optional custom title

    Returns:
        str: Formatted newsletter content
    """
    if not selected_links:
        return "No links selected"

    # Check if OpenAI is available
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return generate_simple_newsletter(selected_links, newsletter_title)

    try:
        client = openai.OpenAI(api_key=api_key)

        # Categorize links
        categories = categorize_links(selected_links)

        # Build newsletter sections
        newsletter_content = ""

        # Header
        if newsletter_title:
            newsletter_content += f"# {newsletter_title}\n\n"
        else:
            newsletter_content += f"# AI & Tech Newsletter\n\n"

        newsletter_content += f"*{datetime.now().strftime('%B %d, %Y')}*\n\n"
        newsletter_content += "---\n\n"

        # Top News Section
        if categories['top_news']:
            newsletter_content += "## Top News\n\n"
            for link in categories['top_news'][:5]:  # Top 5 news stories
                desc = generate_news_description(client, link)
                newsletter_content += f"{desc}\n\n"

        # Massive Fundings ($50M+)
        if categories['funding_massive']:
            newsletter_content += "## Massive Fundings\n\n"
            for link in sorted(categories['funding_massive'], key=lambda x: extract_amount(x.get('title', '') + x.get('context', '')), reverse=True):
                desc = generate_funding_description(client, link)
                newsletter_content += f"{desc}\n\n"

        # Big Fundings ($20M-50M)
        if categories['funding_big']:
            newsletter_content += "## Big Fundings\n\n"
            for link in sorted(categories['funding_big'], key=lambda x: extract_amount(x.get('title', '') + x.get('context', '')), reverse=True):
                desc = generate_funding_description(client, link)
                newsletter_content += f"{desc}\n\n"

        # Smaller Fundings (<$20M)
        if categories['funding_small']:
            newsletter_content += "## Smaller Fundings\n\n"
            for link in sorted(categories['funding_small'], key=lambda x: extract_amount(x.get('title', '') + x.get('context', '')), reverse=True):
                desc = generate_funding_description(client, link)
                newsletter_content += f"{desc}\n\n"

        # Other News
        if categories['other']:
            newsletter_content += "## Other News\n\n"
            for link in categories['other']:
                desc = generate_news_description(client, link)
                newsletter_content += f"{desc}\n\n"

        return newsletter_content

    except Exception as e:
        return f"Error generating newsletter: {e}\n\nFalling back to simple format:\n\n" + generate_simple_newsletter(selected_links, newsletter_title)


def extract_amount(text):
    """Extract funding amount from text for sorting. Returns 0 if not found."""
    import re
    amount_match = re.search(r'\$(\d+(?:\.\d+)?)\s*(m|b|million|billion)', text.lower())

    if amount_match:
        amount_num = float(amount_match.group(1))
        unit = amount_match.group(2).lower()

        # Convert to millions
        if unit.startswith('b'):
            return amount_num * 1000
        else:
            return amount_num
    return 0


def generate_news_description(client, link):
    """Generate a StrictlyVC-style description for a news item."""
    title = link.get('title', 'Untitled')
    url = link.get('url', '#')
    context = link.get('context', '')

    prompt = f"""Write a single paragraph (2-3 sentences, max 60 words) for this news item in the style of StrictlyVC newsletter:

Title: {title}
Context: {context}

Format: Brief, factual summary focusing on what happened, who's involved, and why it matters. End with "More here." and include the source link.

Example style: "Epic and Google struck a monumental settlement that forces Google to open Android app payments and cap fees at 9% or 20%, marking a landmark antitrust win that reshapes mobile app economics. TechCrunch has more here."

Write the description (2-3 sentences max, end with 'More here.'):"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a tech newsletter editor. Write concise, factual news summaries in the style of StrictlyVC."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=120
        )

        description = response.choices[0].message.content.strip()

        # Ensure it ends with link
        if not description.endswith('.'):
            description += '.'

        return f"{description} [Read more]({url})"

    except:
        return f"**{title}** - {context[:150]}... [Read more]({url})"


def generate_funding_description(client, link):
    """Generate a StrictlyVC-style description for a funding item."""
    title = link.get('title', 'Untitled')
    url = link.get('url', '#')
    context = link.get('context', '')

    prompt = f"""Write a single paragraph for this funding news in the style of StrictlyVC newsletter:

Title: {title}
Context: {context}

Format: **Company name**, age, location, what they do, raised $X round type at $Y valuation (if mentioned). Lead investor, with other investors. End with link.

Example style: "Armis, a nine-year-old San Francisco startup that provides security software for critical infrastructure, raised a $435 million round at a $6.1 billion post-money valuation. Goldman Sachs Alternatives was the deal lead, with Evolution Equity Partners also taking part."

Write the description (single paragraph, include all key details):"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a tech newsletter editor. Write concise funding announcements in the style of StrictlyVC."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )

        description = response.choices[0].message.content.strip()

        # Ensure it ends properly
        if not description.endswith('.'):
            description += '.'

        return f"{description} [Read more]({url})"

    except:
        return f"**{title}** - {context[:150]}... [Read more]({url})"


def generate_simple_newsletter(selected_links, newsletter_title=None):
    """Generate a simple newsletter without AI."""
    content = ""

    # Header
    if newsletter_title:
        content += f"# {newsletter_title}\n\n"
    else:
        content += f"# AI & Tech Newsletter\n\n"

    content += f"*{datetime.now().strftime('%B %d, %Y')}*\n\n"
    content += "---\n\n"

    # Categorize
    categories = categorize_links(selected_links)

    # Top News
    if categories['top_news']:
        content += "## Top News\n\n"
        for link in categories['top_news'][:5]:
            title = link.get('title', 'Untitled')
            url = link.get('url', '#')
            context = link.get('context', 'No description available')[:150]
            content += f"**{title}** - {context}... [Read more]({url})\n\n"

    # Massive Fundings
    if categories['funding_massive']:
        content += "## Massive Fundings\n\n"
        for link in categories['funding_massive']:
            title = link.get('title', 'Untitled')
            url = link.get('url', '#')
            context = link.get('context', 'No description available')[:150]
            content += f"**{title}** - {context}... [Read more]({url})\n\n"

    # Big Fundings
    if categories['funding_big']:
        content += "## Big Fundings\n\n"
        for link in categories['funding_big']:
            title = link.get('title', 'Untitled')
            url = link.get('url', '#')
            context = link.get('context', 'No description available')[:150]
            content += f"**{title}** - {context}... [Read more]({url})\n\n"

    # Smaller Fundings
    if categories['funding_small']:
        content += "## Smaller Fundings\n\n"
        for link in categories['funding_small']:
            title = link.get('title', 'Untitled')
            url = link.get('url', '#')
            context = link.get('context', 'No description available')[:150]
            content += f"**{title}** - {context}... [Read more]({url})\n\n"

    # Other News
    if categories['other']:
        content += "## Other News\n\n"
        for link in categories['other']:
            title = link.get('title', 'Untitled')
            url = link.get('url', '#')
            context = link.get('context', 'No description available')[:150]
            content += f"**{title}** - {context}... [Read more]({url})\n\n"

    return content
