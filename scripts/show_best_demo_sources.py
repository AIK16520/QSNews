"""
Show the best sources and filters for demoing the Newsletter Builder.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from src.utils.database import get_session, Newsletter, init_database
from collections import Counter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_best_demo_sources():
    """
    Analyze newsletters to find best sources for demo.
    """
    session = get_session()
    
    try:
        init_database()
        
        # Get all newsletters with links
        newsletters = session.query(Newsletter).filter(
            Newsletter.extracted_links != None
        ).all()
        
        logger.info(f"Analyzing {len(newsletters)} newsletters...\n")
        
        # Count by source
        source_counts = Counter()
        source_link_counts = {}
        source_industries = {}
        
        for newsletter in newsletters:
            if newsletter.extracted_links and len(newsletter.extracted_links) > 0:
                source_counts[newsletter.source] += 1
                
                # Count links per source
                if newsletter.source not in source_link_counts:
                    source_link_counts[newsletter.source] = 0
                source_link_counts[newsletter.source] += len(newsletter.extracted_links)
                
                # Track industries
                if newsletter.industries:
                    if newsletter.source not in source_industries:
                        source_industries[newsletter.source] = Counter()
                    for industry in newsletter.industries:
                        source_industries[newsletter.source][industry] += 1
        
        print("="*60)
        print("BEST SOURCES FOR DEMO")
        print("="*60)
        print(f"\n{'Source':<20} {'Newsletters':<15} {'Total Links':<15} {'Avg Links':<10}")
        print("-"*60)
        
        for source, count in source_counts.most_common(10):
            total_links = source_link_counts.get(source, 0)
            avg_links = total_links / count if count > 0 else 0
            print(f"{source:<20} {count:<15} {total_links:<15} {avg_links:<10.1f}")
        
        print("\n" + "="*60)
        print("TOP INDUSTRIES")
        print("="*60)
        
        # Count industries across all newsletters
        all_industries = Counter()
        for newsletter in newsletters:
            if newsletter.industries:
                for industry in newsletter.industries:
                    all_industries[industry] += 1
        
        for industry, count in all_industries.most_common(10):
            print(f"  {industry:<40} {count} newsletters")
        
        # Show a sample newsletter with good content
        print("\n" + "="*60)
        print("SAMPLE HIGH-QUALITY NEWSLETTERS")
        print("="*60)
        
        # Find newsletters with 10-30 links (sweet spot)
        good_newsletters = [
            n for n in newsletters 
            if n.extracted_links and 10 <= len(n.extracted_links) <= 30
        ]
        
        for newsletter in good_newsletters[:5]:
            print(f"\n{newsletter.source} - {newsletter.title[:60]}...")
            print(f"  Date: {newsletter.published_date}")
            print(f"  Links: {len(newsletter.extracted_links)}")
            if newsletter.industries:
                print(f"  Industries: {', '.join(newsletter.industries[:3])}")
            print(f"  Sample links:")
            for link in newsletter.extracted_links[:3]:
                print(f"    • {link.get('title', 'Untitled')}")
        
        print("\n" + "="*60)
        print("RECOMMENDED DEMO FILTERS")
        print("="*60)
        print("\nOption 1 - General AI Focus:")
        print("  Content Type: Links")
        print("  Industry: General AI")
        print("  Source: Ben's Bites or The Rundown")
        
        print("\nOption 2 - Multiple Industries:")
        print("  Content Type: All")
        print("  Industry: All")
        print("  Source: All")
        print("  (Shows variety of content)")
        
        print("\nOption 3 - Specific Newsletter:")
        print("  Content Type: Links")
        print("  Source: Chief AI Office")
        print("  (Clean investment news)")
        
        print("\n" + "="*60)
        
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ANALYZE BEST DEMO SOURCES")
    print("="*60 + "\n")
    
    analyze_best_demo_sources()


