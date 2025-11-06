"""
Content Quality Validator
Validates article content quality to prevent bundled/multi-topic articles.
"""

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_bundled_article(title: str, summary: str, content: str = None) -> bool:
    """
    Check if an article appears to be bundled/multi-topic.

    Args:
        title: Article title
        summary: Article summary
        content: Optional full content

    Returns:
        True if article appears to be bundled, False otherwise
    """
    if not summary:
        return False

    # Indicators of bundled/multi-topic articles
    bundled_indicators = [
        'various topics',
        'the article discusses various',
        'additionally, it touches',
        'also discusses',
        'among other things',
        'multiple developments',
        'several topics',
        'range of topics',
        'variety of subjects',
        'covers topics from',
        'ranging from',
        'as well as',
        'in addition to',
    ]

    # Check summary for indicators
    summary_lower = summary.lower()
    for indicator in bundled_indicators:
        if indicator in summary_lower:
            logger.warning(f"Bundled article detected ('{indicator}'): {title[:60]}")
            return True

    # Additional check: if summary mentions too many disparate topics
    # Look for unusual topic combinations
    disparate_topics = [
        ('popcorn', 'ai'),
        ('dracula', 'tech'),
        ('rainfall', 'social media'),
        ('food', 'technology'),
        ('cooking', 'artificial intelligence'),
    ]

    for topic1, topic2 in disparate_topics:
        if topic1 in summary_lower and topic2 in summary_lower:
            logger.warning(f"Disparate topics detected ({topic1}, {topic2}): {title[:60]}")
            return True

    return False


def validate_article_quality(article_data: dict) -> tuple[bool, str]:
    """
    Validate overall article quality.

    Args:
        article_data: Dictionary with article data (title, summary, content, etc.)

    Returns:
        Tuple of (is_valid, reason)
    """
    title = article_data.get('title', '')
    summary = article_data.get('summary', '')
    content = article_data.get('full_content', '')

    # Check 1: Bundled article detection
    if is_bundled_article(title, summary, content):
        return False, "Article appears to be bundled/multi-topic"

    # Check 2: Summary quality (not too generic)
    if summary:
        generic_phrases = [
            'this article discusses',
            'the article covers',
            'this piece explores',
        ]

        # If summary is too short and generic, it might be low quality
        if len(summary) < 100:
            summary_lower = summary.lower()
            if any(phrase in summary_lower for phrase in generic_phrases):
                return False, "Summary too generic/low quality"

    # Check 3: Title-summary mismatch
    # If title is about one topic but summary mentions many unrelated topics
    if title and summary:
        title_words = set(title.lower().split())
        summary_lower = summary.lower()

        # Count comma-separated phrases (often indicates multiple topics)
        comma_count = summary.count(',')
        if comma_count > 5 and len(summary) < 300:
            return False, "Summary contains too many comma-separated topics"

    # All checks passed
    return True, "OK"


def main():
    """Test the validator."""
    # Test cases
    test_cases = [
        {
            'title': 'Donald Trump AI Slop',
            'summary': 'The article discusses various topics, including Donald Trump\'s influence on social media and AI, the benefits of air-popped popcorn, and the impact of rainfall on infrastructure.',
            'expected': False
        },
        {
            'title': 'New AI Model Released',
            'summary': 'OpenAI has released a new language model with improved capabilities for understanding context and generating coherent responses.',
            'expected': True
        },
        {
            'title': 'Adobe Updates',
            'summary': 'The article discusses various developments in AI technology, including platforms, social apps, and chatbots.',
            'expected': False
        },
    ]

    print("Testing Content Validator")
    print("=" * 80)

    for i, test in enumerate(test_cases, 1):
        is_valid, reason = validate_article_quality(test)
        expected = test['expected']
        status = "PASS" if (is_valid == expected) else "FAIL"

        print(f"\nTest {i}: {status}")
        print(f"Title: {test['title']}")
        print(f"Summary: {test['summary'][:100]}...")
        print(f"Expected valid: {expected}, Got valid: {is_valid}")
        print(f"Reason: {reason}")


if __name__ == "__main__":
    main()
