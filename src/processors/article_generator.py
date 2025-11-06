"""
Article Generator Module
Uses AI to generate newsletter articles based on selected articles and user instructions.
"""

import logging
import os
from typing import List
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import OpenAI or other LLM libraries
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not installed. AI generation will use fallback method.")


def generate_article_with_ai(session, articles: List, user_content: str, instructions: str) -> str:
    """
    Generate an article using AI based on selected articles and user instructions.

    Args:
        session: Database session
        articles: List of Article objects marked as included
        user_content: Additional content from user
        instructions: Instructions for AI generation

    Returns:
        Generated article content as markdown string
    """
    logger.info(f"Generating article with AI for {len(articles)} articles")
    logger.info(f"User content: {user_content}")
    logger.info(f"Instructions: {instructions}")

    # Prepare context from articles
    context = build_context_from_articles(articles, user_content)
    logger.info(f"Context length: {len(context)} characters")

    # Check if OpenAI is available and configured
    if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
        return generate_with_openai(context, instructions)
    else:
        # Fallback: return structured template
        logger.warning("Using fallback generation method (no AI)")
        return generate_fallback(articles, user_content, instructions)


def build_context_from_articles(articles: List, user_content: str) -> str:
    """Build context string from articles for AI prompt with emphasis on user content."""
    context_lines = []

    # PRIORITY 1: User's additional content (most important)
    if user_content and user_content.strip():
        context_lines.append("=== EDITOR'S ADDITIONAL CONTENT (HIGHEST PRIORITY) ===")
        context_lines.append(f"{user_content}")
        context_lines.append("")
        logger.info(f"Added editor's additional content ({len(user_content)} characters)")
    else:
        logger.info("No editor's additional content provided")

    # PRIORITY 2: User's analysis for each article (very important)
    context_lines.append("=== EDITOR'S ANALYSIS FOR EACH ARTICLE (VERY IMPORTANT) ===")
    analysis_count = 0
    for i, article in enumerate(articles, 1):
        context_lines.append(f"\n--- Article {i}: {article.title} ---")
        if article.your_analysis and article.your_analysis.strip():
            context_lines.append(f"EDITOR'S ANALYSIS: {article.your_analysis}")
            analysis_count += 1
        else:
            context_lines.append("EDITOR'S ANALYSIS: [No analysis provided]")
    context_lines.append("")
    logger.info(f"Added editor's analysis for {analysis_count}/{len(articles)} articles")

    # PRIORITY 3: Article summaries (supporting information)
    context_lines.append("=== ARTICLE SUMMARIES (SUPPORTING INFORMATION) ===")
    for i, article in enumerate(articles, 1):
        context_lines.append(f"\n--- Article {i}: {article.title} ---")
        context_lines.append(f"Source: {article.source}")

        if article.published_date:
            context_lines.append(f"Date: {article.published_date.strftime('%Y-%m-%d')}")

        if article.category:
            context_lines.append(f"Category: {article.category.name}")

        if article.industries:
            industries_str = ', '.join([ind.name for ind in article.industries])
            context_lines.append(f"Industries: {industries_str}")

        if article.summary:
            context_lines.append(f"Summary: {article.summary}")

        if article.url:
            context_lines.append(f"URL: {article.url}")

    logger.info(f"Added summaries for {len(articles)} articles")

    context = '\n'.join(context_lines)

    # Log the complete context
    logger.info("="*80)
    logger.info("CONTEXT BUILT FROM ARTICLES AND NOTES")
    logger.info("="*80)
    logger.info(context)
    logger.info("="*80)

    return context


def generate_with_openai(context: str, instructions: str) -> str:
    """Generate article using OpenAI API with format detection."""
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Check if instructions contain format instructions
        format_keywords = ['format', 'structure', 'layout', 'headline', 'section', 'paragraph', 'style', 'write', 'create', 'focus on', 'emphasize', 'highlight']
        has_format_instructions = any(keyword in instructions.lower() for keyword in format_keywords)

        logger.info(f"AI Instructions: {instructions}")
        logger.info(f"Has format instructions: {has_format_instructions}")

        if has_format_instructions:
            # Use custom format based on user instructions
            system_prompt = """You are an expert newsletter writer and technology analyst specializing in AI and technology trends.
Your task is to synthesize multiple articles and insights into a cohesive, engaging newsletter article.

CRITICAL REQUIREMENTS:
- The EDITOR'S ADDITIONAL CONTENT and EDITOR'S ANALYSIS sections are the MOST IMPORTANT parts
- You MUST prominently feature and build upon the editor's insights and analysis
- The editor's content should be the foundation and primary focus of your article
- Use article summaries only as supporting evidence for the editor's points
- Make sure the editor's voice and perspective are clearly represented

WRITING GUIDELINES:
- Write in a clear, professional, and insightful style
- Focus on connecting themes, identifying trends, and providing valuable analysis
- Use markdown formatting for structure
- Create compelling headlines that capture attention
- Synthesize information rather than just summarizing
- Provide context and implications for readers
- Make complex topics accessible and engaging

Follow the specific format and structure instructions provided by the user."""

            user_prompt = f"""Create a newsletter article following these specific instructions:

{instructions}

CONTENT TO SYNTHESIZE (in order of importance):
{context}

IMPORTANT: The editor's additional content and analysis are the PRIMARY focus. Use article summaries only to support the editor's insights. Make sure the editor's perspective is prominently featured throughout the article.

Write the article now following the format instructions provided:"""
        else:
            # Use simple default format
            system_prompt = """You are an expert newsletter writer. Create a newsletter article with:
1. Your own AI-generated headline
2. AI-generated article content synthesizing all sources
3. All article links at the end

CRITICAL: The editor's additional content and analysis are the PRIMARY focus. Use article summaries only to support the editor's insights. Make sure the editor's perspective is prominently featured throughout the article.

Keep it professional and engaging."""

            user_prompt = f"""Create a newsletter article from these sources:

{context}

Format:
- Your own AI-generated headline
- AI-generated article with all sources synthesized
- All links to articles at the end

IMPORTANT: The editor's additional content and analysis are the PRIMARY focus. Use article summaries only to support the editor's insights. Make sure the editor's perspective is prominently featured throughout the article.

Write the article now:"""

        # Log the complete final prompt
        logger.info("="*80)
        logger.info("FINAL PROMPT BEING SENT TO AI")
        logger.info("="*80)
        logger.info("\n--- SYSTEM PROMPT ---")
        logger.info(system_prompt)
        logger.info("\n--- USER PROMPT ---")
        logger.info(user_prompt)
        logger.info("="*80)
        logger.info(f"Total prompt length: {len(system_prompt) + len(user_prompt)} characters")
        logger.info("="*80)

        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        generated_content = response.choices[0].message.content
        logger.info("Article generated successfully with OpenAI")
        logger.info(f"Generated content length: {len(generated_content)} characters")
        logger.info(f"Generated content preview: {generated_content[:200]}...")
        return generated_content

    except Exception as e:
        logger.error(f"Error generating with OpenAI: {e}")
        logger.info("Falling back to template generation")
        # Fallback if OpenAI fails
        return f"# AI Generation Error\n\nError: {str(e)}\n\nPlease check your OpenAI API key and try again, or use 'Use as Final Report' option instead."


def generate_standard_format(articles: List, user_content: str) -> str:
    """
    Generate article in standard format when AI is not used.
    Format: Just use the additional content box.
    """
    # Simply return the user's additional content
    if user_content:
        return user_content
    else:
        return "No additional content provided."


def generate_fallback(articles: List, user_content: str, instructions: str) -> str:
    """
    Fallback generation method when AI is not available.
    Uses simple format: headline + article content + links.
    """
    logger.info("Using simple fallback format (no AI available)")
    
    lines = []
    
    # Create headline
    if articles:
        categories = [article.category.name for article in articles if article.category]
        if categories:
            main_category = max(set(categories), key=categories.count)
            headline = f"AI Newsletter: {main_category} Developments"
        else:
            headline = "AI Newsletter: Key Developments"
        
        lines.append(f"# {headline}")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
        
        # Article content
        lines.append("## Article Content")
        lines.append("This newsletter synthesizes key insights from recent developments in AI and technology.\n")
        
        # Group by category
        articles_by_category = {}
        for article in articles:
            category_name = article.category.name if article.category else 'General'
            if category_name not in articles_by_category:
                articles_by_category[category_name] = []
            articles_by_category[category_name].append(article)
        
        for category_name in sorted(articles_by_category.keys()):
            category_articles = articles_by_category[category_name]
            lines.append(f"### {category_name}")
            
            for article in category_articles:
                lines.append(f"**{article.title}**")
                if article.summary:
                    lines.append(f"{article.summary}")
                if article.your_analysis:
                    lines.append(f"Analysis: {article.your_analysis}")
                lines.append("")
        
        # All links
        lines.append("## All Article Links")
        for article in articles:
            lines.append(f"- [{article.title}]({article.url}) - {article.source}")
    
    return '\n'.join(lines)


def main():
    """Test article generation."""
    print("Article Generator Module")
    print("This module requires database and articles to test.")
    print("Use the dashboard to generate articles.")


if __name__ == "__main__":
    main()
