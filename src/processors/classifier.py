"""
Classifier Module
Uses OpenAI API to classify articles into categories and industries.
Generates summaries and key points.
"""

import logging
import json
import time
from typing import Dict, List, Optional

from openai import OpenAI, APIError, RateLimitError

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = None
if config.OPENAI_API_KEY:
    client = OpenAI(api_key=config.OPENAI_API_KEY)
else:
    logger.warning("OPENAI_API_KEY not set. Classifier will use default classifications.")


def build_classification_prompt(
    title: str,
    content: str,
    categories: List[str],
    industries: List[str]
) -> str:
    """
    Build the classification prompt for OpenAI.

    Args:
        title: Article title
        content: Article content (truncated to 2000 chars)
        categories: List of valid categories
        industries: List of valid industries

    Returns:
        Formatted prompt string
    """
    # Truncate content to save tokens
    content_preview = content[:2000] if content else ""

    prompt = f"""You are an AI newsletter curator. Analyze the following article and provide a structured classification.

ARTICLE TITLE:
{title}

ARTICLE CONTENT:
{content_preview}

TASK:
Classify this article and provide:
1. ONE category (choose the most relevant)
2. 1-3 industries (choose the most relevant)
3. A 2-3 sentence summary
4. 5-7 key points/takeaways

VALID CATEGORIES (choose ONE):
{', '.join(categories)}

VALID INDUSTRIES (choose 1-3):
{', '.join(industries)}

RESPONSE FORMAT:
Respond ONLY with valid JSON in this exact format:
{{
  "category": "category name",
  "industries": ["industry1", "industry2"],
  "summary": "2-3 sentence summary of the article",
  "key_points": [
    "Key takeaway 1",
    "Key takeaway 2",
    "Key takeaway 3",
    "Key takeaway 4",
    "Key takeaway 5"
  ]
}}

IMPORTANT:
- Use ONLY categories and industries from the lists provided above
- Choose the SINGLE most relevant category
- Choose 1-3 most relevant industries
- Keep the summary concise (2-3 sentences)
- Provide 5-7 key points
- Return ONLY the JSON, no other text"""

    return prompt


def classify_article(
    title: str,
    content: str,
    categories_list: Optional[List[str]] = None,
    industries_list: Optional[List[str]] = None,
    max_retries: int = 3
) -> Dict:
    """
    Classify an article using OpenAI API.

    Args:
        title: Article title
        content: Article content
        categories_list: List of valid categories (defaults to config.CATEGORIES)
        industries_list: List of valid industries (defaults to config.INDUSTRIES)
        max_retries: Maximum number of retries on failure

    Returns:
        Dictionary with classification results:
        {
            'category': str,
            'industries': List[str],
            'summary': str,
            'key_points': List[str]
        }
    """
    # Use defaults if not provided
    if categories_list is None:
        categories_list = config.CATEGORIES
    if industries_list is None:
        industries_list = config.INDUSTRIES

    # Default classification (fallback)
    default_result = {
        'category': 'General AI',
        'industries': ['General AI'],
        'summary': title,  # Use title as summary fallback
        'key_points': []
    }

    # If no API key, return default
    if not client:
        logger.warning("No API key available, using default classification")
        return default_result

    # Build prompt
    prompt = build_classification_prompt(title, content, categories_list, industries_list)

    # Try classification with retries
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Classifying article (attempt {attempt}/{max_retries}): {title[:50]}...")

            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using GPT-4o-mini for cost efficiency
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that classifies articles. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
                temperature=0.3,
                response_format={"type": "json_object"}  # Force JSON response
            )

            # Extract response text
            response_text = response.choices[0].message.content

            # Parse JSON response
            try:
                result = json.loads(response_text)

                # Validate required fields
                if 'category' not in result or 'industries' not in result:
                    logger.warning(f"Invalid response format, missing required fields")
                    result = {**default_result, **result}  # Merge with defaults

                # Validate category
                if result['category'] not in categories_list:
                    logger.warning(f"Invalid category '{result['category']}', using default")
                    result['category'] = 'General AI'

                # Validate industries
                valid_industries = [ind for ind in result.get('industries', []) if ind in industries_list]
                if not valid_industries:
                    valid_industries = ['General AI']
                result['industries'] = valid_industries[:3]  # Max 3

                # Ensure summary exists
                if not result.get('summary'):
                    result['summary'] = title

                # Ensure key_points exists
                if not result.get('key_points'):
                    result['key_points'] = []

                logger.info(f"✓ Classification successful: {result['category']}, {result['industries']}")
                return result

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Response text: {response_text}")

                # If all parsing fails, return default
                if attempt == max_retries:
                    logger.error("All parsing attempts failed, using default classification")
                    return default_result

        except RateLimitError as e:
            logger.warning(f"Rate limit hit, waiting before retry... (attempt {attempt}/{max_retries})")
            if attempt < max_retries:
                # Exponential backoff
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                logger.error("Rate limit exceeded, using default classification")
                return default_result

        except APIError as e:
            logger.error(f"API error: {e}")
            if attempt == max_retries:
                logger.error("API error persists, using default classification")
                return default_result
            time.sleep(2)

        except Exception as e:
            logger.error(f"Unexpected error during classification: {e}")
            if attempt == max_retries:
                logger.error("Classification failed, using default classification")
                return default_result
            time.sleep(1)

    return default_result


def classify_multiple_articles(articles: List[Dict], delay: float = 1.0) -> List[Dict]:
    """
    Classify multiple articles with rate limiting.

    Args:
        articles: List of article dictionaries with 'title' and 'content' keys
        delay: Delay between API calls in seconds

    Returns:
        List of classification results
    """
    results = []

    for i, article in enumerate(articles, 1):
        logger.info(f"Classifying article {i}/{len(articles)}")

        title = article.get('title', 'Untitled')
        content = article.get('content', '')

        classification = classify_article(title, content)
        results.append(classification)

        # Rate limiting (except for last article)
        if i < len(articles):
            time.sleep(delay)

    logger.info(f"Classification complete: {len(results)} articles processed")
    return results


def main():
    """Test the classifier with a sample article."""
    print("Testing Article Classifier\n")

    # Sample article
    sample_article = {
        'title': 'OpenAI Launches New GPT-4 Turbo Model for Healthcare Applications',
        'content': '''OpenAI announced today the release of GPT-4 Turbo, a new language model
        specifically optimized for healthcare applications. The model has been trained on medical
        literature and can assist doctors in diagnosis and treatment planning. The company says
        the model achieves 95% accuracy in medical question answering tasks. Several hospitals
        have already begun pilot programs to test the technology. Privacy concerns have been
        addressed through on-premise deployment options.'''
    }

    print(f"Title: {sample_article['title']}\n")
    print("Classifying...\n")

    # Classify
    result = classify_article(
        title=sample_article['title'],
        content=sample_article['content']
    )

    # Display results
    print("="*80)
    print("CLASSIFICATION RESULTS")
    print("="*80)
    print(f"\nCategory: {result['category']}")
    print(f"Industries: {', '.join(result['industries'])}")
    print(f"\nSummary:\n{result['summary']}")
    print(f"\nKey Points:")
    for i, point in enumerate(result.get('key_points', []), 1):
        print(f"  {i}. {point}")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
