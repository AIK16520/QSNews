"""
Show the best filters for demoing the Newsletters workflow.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from src.utils.database import get_session, Newsletter, init_database
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def show_best_demo_newsletters():
    """
    Show best newsletters for demo.
    """
    session = get_session()
    
    try:
        init_database()
        
        # Get recent newsletters with good link counts
        recent_date = datetime.now() - timedelta(days=7)
        
        newsletters = session.query(Newsletter).filter(
            Newsletter.extracted_links != None,
            Newsletter.published_date >= recent_date
        ).all()
        
        # Filter to those with 10-25 links (good for demo)
        good_newsletters = [
            n for n in newsletters 
            if n.extracted_links and 10 <= len(n.extracted_links) <= 25
        ]
        
        print("="*80)
        print("BEST NEWSLETTERS FOR WORKFLOW DEMO")
        print("="*80)
        print(f"\nFound {len(good_newsletters)} newsletters with 10-25 links (ideal for demo)\n")
        
        # Group by source
        by_source = {}
        for n in good_newsletters:
            if n.source not in by_source:
                by_source[n.source] = []
            by_source[n.source].append(n)
        
        print(f"{'Source':<20} {'Count':<10} {'Avg Links':<15} {'Industries':<30}")
        print("-"*80)
        
        for source, newsletters_list in sorted(by_source.items(), key=lambda x: len(x[1]), reverse=True):
            avg_links = sum(len(n.extracted_links) for n in newsletters_list) / len(newsletters_list)
            
            # Get common industries
            industries = set()
            for n in newsletters_list:
                if n.industries:
                    industries.update(n.industries[:2])
            industries_str = ", ".join(list(industries)[:2])
            
            print(f"{source:<20} {len(newsletters_list):<10} {avg_links:<15.1f} {industries_str:<30}")
        
        print("\n" + "="*80)
        print("SAMPLE NEWSLETTERS (READY FOR DEMO)")
        print("="*80)
        
        # Show 5 best examples
        for i, newsletter in enumerate(good_newsletters[:5], 1):
            print(f"\n{i}. {newsletter.source} - {newsletter.title[:60]}...")
            print(f"   Date: {newsletter.published_date.strftime('%b %d, %Y')}")
            print(f"   Links: {len(newsletter.extracted_links)}")
            if newsletter.industries:
                print(f"   Industries: {', '.join(newsletter.industries[:3])}")
            print(f"   Sample links:")
            for link in newsletter.extracted_links[:4]:
                title = link.get('title', 'Untitled')
                print(f"      • {title[:70]}")
        
        print("\n" + "="*80)
        print("RECOMMENDED DEMO FILTERS")
        print("="*80)
        
        print("\n🎯 BEST OPTION - Single Newsletter Focus:")
        print("   1. Go to Newsletters workflow")
        print("   2. Filter by Source: 'Ben's Bites' or 'TLDR'")
        print("   3. Filter by Industry: 'General AI'")
        print("   4. Select 1-2 newsletters (checkboxes)")
        print("   5. Click 'Review Selected Newsletters →'")
        print("   6. Review links (all pre-selected)")
        print("   7. Click 'Generate Report'")
        print("   8. See AI-generated descriptions")
        print("   9. Export as PDF or DOCX")
        
        print("\n📊 ALTERNATIVE - Multiple Newsletters:")
        print("   1. Filter by Industry: 'General AI'")
        print("   2. Select 2-3 newsletters from different sources")
        print("   3. Shows variety in the review page")
        
        print("\n⚡ QUICK DEMO (30 seconds):")
        print("   1. Select any 1 newsletter with ~15 links")
        print("   2. Click 'Review Selected'")
        print("   3. Uncheck 2-3 links to show filtering")
        print("   4. Click 'Generate Report'")
        print("   5. Show the formatted output")
        print("   6. Export as PDF")
        
        print("\n" + "="*80)
        
        # Show what the user will see
        print("\nWHAT HAPPENS IN THE DEMO:")
        print("="*80)
        print("Step 1: Newsletter Selection Page")
        print("  → Shows list of newsletters with metadata")
        print("  → User checks 1-2 newsletters")
        print("  → Clicks 'Review Selected Newsletters →'")
        print()
        print("Step 2: Newsletter Review Page")
        print("  → Shows ALL links from selected newsletters")
        print("  → All links are checked by default")
        print("  → User can uncheck unwanted links")
        print("  → Clicks 'Generate Report'")
        print()
        print("Step 3: Final Report Page")
        print("  → Shows generated report with:")
        print("    • Title, date, source info")
        print("    • Each link with 2-3 sentence AI description")
        print("    • Clean markdown formatting")
        print("  → Export buttons: PDF & DOCX")
        print()
        print("="*80)
        
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("NEWSLETTER WORKFLOW DEMO GUIDE")
    print("="*80 + "\n")
    
    show_best_demo_newsletters()


