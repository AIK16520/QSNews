"""
Update category and industry names to replace & with 'and'.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.database import get_session, Category, Industry

def update_categories_and_industries():
    """Update all category and industry names to replace & with 'and'."""
    session = get_session()

    try:
        updated_count = 0

        print("Updating Categories and Industries...")
        print("=" * 80)

        # Update Categories
        print("\nCategories:")
        print("-" * 80)
        categories = session.query(Category).all()

        for category in categories:
            if '&' in category.name:
                old_name = category.name
                category.name = category.name.replace('&', 'and')
                print(f"{old_name} -> {category.name}")
                updated_count += 1

        # Update Industries
        print("\nIndustries:")
        print("-" * 80)
        industries = session.query(Industry).all()

        for industry in industries:
            if '&' in industry.name:
                old_name = industry.name
                industry.name = industry.name.replace('&', 'and')
                print(f"{old_name} -> {industry.name}")
                updated_count += 1

        # Commit changes
        session.commit()

        print("\n" + "=" * 80)
        print(f"Successfully updated {updated_count} categories/industries")
        print("All '&' replaced with 'and'")
        print("=" * 80)

        return updated_count

    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    updated = update_categories_and_industries()
    print(f"\nDatabase updated: {updated} items modified")
