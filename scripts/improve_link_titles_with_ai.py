"""
Use AI to generate descriptive titles for links with uninformative titles.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from src.utils.database import get_session, Newsletter, init_database
from openai import OpenAI
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI
client = OpenAI(api_key=config.OPENAI_API_KEY)


def generate_better_title(context, original_title):
    """
    Use AI to generate a better title from context.
    """
    try:
        prompt = f"""Generate a concise, descriptive title (5-8 words max) for this link based on its context.
Focus on the key company, technology, or event mentioned.

Context: {context}

Return ONLY the title, nothing else. Make it informative and specific."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You generate concise, informative link titles."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        
        new_title = response.choices[0].message.content.strip()
        
        # Remove quotes if AI added them
        if new_title.startswith('"') and new_title.endswith('"'):
            new_title = new_title[1:-1]
        if new_title.startswith("'") and new_title.endswith("'"):
            new_title = new_title[1:-1]
        
        return new_title
        
    except Exception as e:
        logger.error(f"Error generating title: {e}")
        return None


def improve_link_titles():
    """
    Find and improve uninformative link titles.
    """
    session = get_session()
    
    try:
        init_database()
        
        # Get all newsletters
        newsletters = session.query(Newsletter).filter(
            Newsletter.extracted_links != None
        ).all()
        
        logger.info(f"Checking {len(newsletters)} newsletters...")
        
        # Verb-only titles and other uninformative ones
        uninformative_titles = [
            'pulling', 'told', 'developed', 'come', 'building', 
            'secured', 'reports', 'said', 'raised', 'announced',
            'launched', 'unveiled', 'released', 'introducing',
            'showed', 'revealed', 'shared', 'posted', 'published',
            'confirmed', 'denied', 'added', 'noted', 'explained',
            'claimed', 'stated', 'mentioned', 'wrote', 'tweeted'
        ]
        
        updated_newsletters = 0
        improved_links = 0
        
        for newsletter in newsletters:
            if not newsletter.extracted_links:
                continue
            
            updated_any = False
            
            for link in newsletter.extracted_links:
                title = link.get('title', '').strip()
                context = link.get('context', '').strip()
                
                # Check if title is uninformative
                if title.lower() in uninformative_titles and context:
                    logger.info(f"\n{'='*60}")
                    logger.info(f"Newsletter ID {newsletter.id} ({newsletter.source})")
                    logger.info(f"Old title: '{title}'")
                    logger.info(f"Context: {context[:150]}...")
                    
                    # Generate better title
                    new_title = generate_better_title(context, title)
                    
                    if new_title and len(new_title) > 5:
                        link['title'] = new_title
                        logger.info(f"New title: '{new_title}'")
                        improved_links += 1
                        updated_any = True
                    else:
                        logger.warning("Failed to generate better title")
            
            if updated_any:
                updated_newsletters += 1
        
        if updated_newsletters > 0:
            logger.info(f"\n{'='*60}")
            logger.info(f"Preview of changes - updating {improved_links} links in {updated_newsletters} newsletters")
            logger.info(f"{'='*60}\n")
            
            response = input("Apply these changes? (yes/no): ").strip().lower()
            
            if response in ['yes', 'y']:
                session.commit()
                logger.info(f"✅ Updated {updated_newsletters} newsletters!")
                logger.info(f"✅ Improved {improved_links} link titles!")
                return updated_newsletters, improved_links
            else:
                logger.info("Changes cancelled")
                session.rollback()
                return 0, 0
        else:
            logger.info("✅ No uninformative links found!")
            return 0, 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return 0, 0
    
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("IMPROVE LINK TITLES WITH AI")
    print("="*60)
    print("\nThis will use AI to generate better titles for links like:")
    print("  'pulling' → 'K-Scale Labs Cancels K-Bot Preorders'")
    print("  'said' → 'OpenAI Reaches 1M Business Customers'")
    print("="*60 + "\n")
    
    print("⚠️  This will use OpenAI API (costs ~$0.01-0.05)")
    response = input("\nContinue? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\nAnalyzing and improving link titles...\n")
        updated, improved = improve_link_titles()
        
        if improved > 0:
            print(f"\n✅ Done! Improved {improved} links in {updated} newsletters.\n")
        else:
            print("\n✅ No changes needed!\n")
    else:
        print("\nCancelled.")


