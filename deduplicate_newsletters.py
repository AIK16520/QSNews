"""
Newsletter Deduplication Script
Identifies similar newsletters and groups them together, combining their links.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.database import get_session, Newsletter
from datetime import datetime, timedelta
import openai
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def are_newsletters_similar(newsletter1: Newsletter, newsletter2: Newsletter) -> dict:
    """
    Use AI to determine if two newsletters cover similar topics.

    Returns:
        dict with keys: 'similar' (bool), 'reason' (str), 'confidence' (float)
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OpenAI API key not found")
        return {'similar': False, 'reason': 'API key missing', 'confidence': 0.0}

    try:
        client = openai.OpenAI(api_key=api_key)

        # Prepare newsletter data
        nl1_data = f"""
Title: {newsletter1.title}
Source: {newsletter1.source}
Summary: {newsletter1.summary or 'N/A'}
Tags: {', '.join(newsletter1.tags) if newsletter1.tags else 'N/A'}
"""

        nl2_data = f"""
Title: {newsletter2.title}
Source: {newsletter2.source}
Summary: {newsletter2.summary or 'N/A'}
Tags: {', '.join(newsletter2.tags) if newsletter2.tags else 'N/A'}
"""

        system_prompt = """You are an expert at comparing newsletter content to identify duplicates or very similar topics.

Two newsletters should be considered SIMILAR if they:
1. Cover the same main story/event (e.g., both about OpenAI's funding round, both about a specific product launch)
2. Discuss the same companies/developments with significant overlap (e.g., both discussing OpenAI's recent developments even if different specific stories)
3. Cover the same general topic area with overlapping content (e.g., both about AI model releases, both about OpenAI company news)
4. Would have significant content overlap if you were to read both

Two newsletters should NOT be considered similar if they:
1. Just mention the same company in passing while focusing on completely different topics
2. Cover different time periods AND different topics (e.g., weekly roundups from weeks apart with no overlapping stories)
3. Have completely different main focuses with minimal overlap

NOTE: If both newsletters cover multiple stories about the same company/topic (like OpenAI), they SHOULD be considered similar even if the specific stories differ.

Respond with JSON only."""

        user_prompt = f"""Compare these two newsletters and determine if they are similar enough to be grouped together:

Newsletter 1:
{nl1_data}

Newsletter 2:
{nl2_data}

Respond ONLY with valid JSON in this format:
{{
  "similar": true or false,
  "reason": "brief explanation of why they are or aren't similar",
  "confidence": 0.0 to 1.0
}}"""

        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=200,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        logger.error(f"Error comparing newsletters: {e}")
        return {'similar': False, 'reason': f'Error: {str(e)}', 'confidence': 0.0}


def find_duplicate_groups(newsletters: list, min_confidence: float = 0.7) -> list:
    """
    Find groups of similar newsletters.

    Args:
        newsletters: List of Newsletter objects
        min_confidence: Minimum confidence threshold for similarity (0.0-1.0)

    Returns:
        List of groups, where each group is a list of similar newsletter IDs
    """
    groups = []
    processed = set()

    total_comparisons = len(newsletters) * (len(newsletters) - 1) // 2
    current_comparison = 0

    logger.info(f"Comparing {len(newsletters)} newsletters ({total_comparisons} comparisons)...")

    for i, nl1 in enumerate(newsletters):
        if nl1.id in processed:
            continue

        # Start a new group with this newsletter
        current_group = [nl1.id]

        # Compare with all subsequent newsletters
        for j in range(i + 1, len(newsletters)):
            nl2 = newsletters[j]

            if nl2.id in processed:
                continue

            current_comparison += 1

            # Skip if from same source and very close dates (likely same newsletter)
            if nl1.source == nl2.source:
                time_diff = abs((nl1.published_date - nl2.published_date).total_seconds()) if nl1.published_date and nl2.published_date else 999999
                if time_diff < 3600:  # Less than 1 hour apart
                    logger.info(f"  [{current_comparison}/{total_comparisons}] Skipping same source+time: {nl1.source}")
                    continue

            logger.info(f"  [{current_comparison}/{total_comparisons}] Comparing: '{nl1.title[:40]}...' vs '{nl2.title[:40]}...'")

            result = are_newsletters_similar(nl1, nl2)

            if result['similar'] and result['confidence'] >= min_confidence:
                current_group.append(nl2.id)
                processed.add(nl2.id)
                logger.info(f"    ✓ SIMILAR (confidence: {result['confidence']:.2f}) - {result['reason']}")
            else:
                logger.info(f"    ✗ Different (confidence: {result['confidence']:.2f}) - {result['reason']}")

        # Only add group if it has more than 1 newsletter
        if len(current_group) > 1:
            groups.append(current_group)
            processed.update(current_group)

    return groups


def merge_newsletter_links(newsletters: list) -> dict:
    """
    Combine links from multiple similar newsletters.

    Returns:
        dict with merged data
    """
    all_links = []
    sources = []
    titles = []
    summaries = []
    all_tags = set()
    all_industries = set()

    for nl in newsletters:
        sources.append(nl.source)
        titles.append(nl.title)
        if nl.summary:
            summaries.append(nl.summary)

        if nl.extracted_links:
            all_links.extend(nl.extracted_links)

        if nl.tags:
            all_tags.update(nl.tags)

        if nl.industries:
            all_industries.update(nl.industries)

    # Deduplicate links by URL
    unique_links = {}
    for link in all_links:
        url = link.get('url', '')
        if url and url not in unique_links:
            unique_links[url] = link

    merged_title = f"Combined: {' | '.join(set(sources))}"
    merged_summary = "\n\n".join([f"**From {newsletters[i].source}:** {summaries[i]}" for i in range(len(summaries))])

    return {
        'title': merged_title,
        'sources': list(set(sources)),
        'original_titles': titles,
        'summary': merged_summary,
        'links': list(unique_links.values()),
        'tags': list(all_tags),
        'industries': list(all_industries),
        'count': len(newsletters)
    }


def display_duplicate_groups(session, groups: list):
    """Display found duplicate groups."""
    if not groups:
        logger.info("\n✓ No duplicate groups found!")
        return

    logger.info(f"\n{'='*80}")
    logger.info(f"FOUND {len(groups)} DUPLICATE GROUPS")
    logger.info(f"{'='*80}\n")

    for i, group_ids in enumerate(groups, 1):
        newsletters = [session.query(Newsletter).get(nid) for nid in group_ids]

        logger.info(f"GROUP {i}: {len(newsletters)} similar newsletters")
        logger.info("-" * 80)

        for nl in newsletters:
            logger.info(f"  [{nl.id}] {nl.source} - {nl.title[:70]}")
            logger.info(f"      Date: {nl.published_date.strftime('%Y-%m-%d') if nl.published_date else 'N/A'}")
            logger.info(f"      Links: {len(nl.extracted_links) if nl.extracted_links else 0}")
            logger.info(f"      Tags: {', '.join(nl.tags) if nl.tags else 'None'}")

        # Show merged version
        merged = merge_newsletter_links(newsletters)
        logger.info(f"\n  MERGED VERSION:")
        logger.info(f"    Title: {merged['title']}")
        logger.info(f"    Total Links: {len(merged['links'])}")
        logger.info(f"    Tags: {', '.join(merged['tags'])}")
        logger.info(f"    Industries: {', '.join(merged['industries'])}")

        logger.info("\n")


def mark_duplicates_as_merged(session, groups: list, dry_run: bool = True):
    """
    Mark duplicate newsletters and create merged versions.

    Args:
        session: Database session
        groups: List of duplicate groups
        dry_run: If True, only show what would be done
    """
    if not groups:
        logger.info("No groups to merge.")
        return

    if dry_run:
        logger.info("\n*** DRY RUN MODE - No changes will be made ***")
        display_duplicate_groups(session, groups)
        logger.info(f"\nTo actually merge these groups, run with --merge flag")
        return

    # Actually merge
    logger.info(f"\nMerging {len(groups)} duplicate groups...")

    for i, group_ids in enumerate(groups, 1):
        newsletters = [session.query(Newsletter).get(nid) for nid in group_ids]

        # Keep the first one, mark others as duplicates
        primary = newsletters[0]
        duplicates = newsletters[1:]

        # Merge all links into primary
        merged = merge_newsletter_links(newsletters)

        # Update primary newsletter
        primary.title = merged['title']
        primary.summary = merged['summary']
        primary.extracted_links = merged['links']
        primary.tags = merged['tags']
        primary.industries = merged['industries']

        # Mark duplicates
        for nl in duplicates:
            nl.status = 'duplicate'
            nl.your_analysis = f"Duplicate - merged into newsletter #{primary.id}"

        logger.info(f"  ✓ Merged group {i}: {len(newsletters)} newsletters -> Newsletter #{primary.id}")

    session.commit()
    logger.info(f"\n✓ Successfully merged {len(groups)} groups")


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description='Deduplicate similar newsletters')
    parser.add_argument('--merge', action='store_true',
                       help='Actually merge the duplicates (default is dry run)')
    parser.add_argument('--days', type=int, default=30,
                       help='Only check newsletters from the last N days (default: 30)')
    parser.add_argument('--confidence', type=float, default=0.7,
                       help='Minimum confidence threshold for similarity (0.0-1.0, default: 0.7)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of newsletters to check (for testing)')
    args = parser.parse_args()

    session = get_session()

    try:
        # Get newsletters from the last N days
        cutoff_date = datetime.now() - timedelta(days=args.days)
        query = session.query(Newsletter).filter(
            Newsletter.published_date >= cutoff_date,
            Newsletter.status != 'duplicate'  # Skip already marked duplicates
        ).order_by(Newsletter.published_date.desc())

        if args.limit:
            query = query.limit(args.limit)

        newsletters = query.all()

        logger.info(f"Checking {len(newsletters)} newsletters from the last {args.days} days...")
        logger.info(f"Similarity confidence threshold: {args.confidence}")

        if not newsletters:
            logger.info("No newsletters found to check.")
            return

        # Find duplicate groups
        groups = find_duplicate_groups(newsletters, min_confidence=args.confidence)

        # Display or merge
        mark_duplicates_as_merged(session, groups, dry_run=not args.merge)

    except Exception as e:
        logger.error(f"Error: {e}")
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    main()
