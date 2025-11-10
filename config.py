import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup logging for config
logger = logging.getLogger(__name__)

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Newsletter Gmail Credentials
NEWSLETTER_GMAIL = os.getenv('NEWSLETTER_GMAIL')
NEWSLETTER_PASS = os.getenv('NEWSLETTER_PASS') or os.getenv('GMAIL_APP_PASS')  # 16-character app password

# Debug: Log environment variables (remove after testing)
print(f"[CONFIG DEBUG] NEWSLETTER_GMAIL loaded: {'✓' if NEWSLETTER_GMAIL else '✗'} ({NEWSLETTER_GMAIL[:10] + '...' if NEWSLETTER_GMAIL else 'None'})", flush=True)
print(f"[CONFIG DEBUG] NEWSLETTER_PASS loaded: {'✓' if NEWSLETTER_PASS else '✗'} ({'***' if NEWSLETTER_PASS else 'None'})", flush=True)
print(f"[CONFIG DEBUG] OPENAI_API_KEY loaded: {'✓' if OPENAI_API_KEY else '✗'}", flush=True)
print(f"[CONFIG DEBUG] SUPABASE_URL loaded: {'✓' if SUPABASE_URL else '✗'} ({SUPABASE_URL[:30] + '...' if SUPABASE_URL else 'None'})", flush=True)
print(f"[CONFIG DEBUG] SUPABASE_KEY loaded: {'✓' if SUPABASE_KEY else '✗'} ({'eyJ...' if SUPABASE_KEY else 'None'})", flush=True)
print(f"[CONFIG DEBUG] USE_SUPABASE: {USE_SUPABASE}", flush=True)

# Database
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/articles.db')

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')  # https://xxxxx.supabase.co
SUPABASE_KEY = os.getenv('SUPABASE_KEY')  # API key (service_role preferred)
USE_SUPABASE = os.getenv('USE_SUPABASE', 'false').lower() == 'true'

# RSS Feed Sources
# Core sources (always enabled)
RSS_SOURCES = {
    # Original sources
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
    "The Verge AI": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "MIT Tech Review": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    "Ars Technica AI": "https://arstechnica.com/tag/artificial-intelligence/feed/",
    "Anthropic": "https://www.anthropic.com/news",  # Web-scraped, not RSS

    "Ahead of AI": "https://magazine.sebastianraschka.com/feed",
    "AI Business": "https://aibusiness.com/rss.xml",
    "AI Snake Oil": "https://aisnakeoil.substack.com/feed",
    "Wired AI": "https://www.wired.com/feed/tag/ai/latest/rss",
    "AI News": "https://www.artificialintelligence-news.com/feed/rss/",

    # Research 
    "Google AI Blog": "http://googleaiblog.blogspot.com/atom.xml",
    "OpenAI Blog": "https://openai.com/blog/rss/",
    "Berkeley AI Research": "https://bair.berkeley.edu/blog/feed.xml",
    

    # Technical
    "Simon Willison": "https://simonwillison.net/atom/everything/",
    "Eugene Yan": "https://eugeneyan.com/rss/",
    "Chip Huyen": "https://huyenchip.com/feed",
    "LangChain Blog": "https://blog.langchain.dev/rss/",

    
    "IEEE Spectrum": "https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss",

    # Newsletters
    "The Rundown AI": "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml",
    "Last Week in AI": "https://lastweekin.ai/feed",
    "TheSequence": "https://thesequence.substack.com/feed",
    "One Useful Thing": "https://www.oneusefulthing.org/feed",
}


# WARNING: Enabling all sources will significantly increase fetch time
RSS_SOURCES_EXTENDED = {
    
    "AI Accelerator Institute": "https://aiacceleratorinstitute.com/rss/",
    "AI-TechPark": "https://ai-techpark.com/category/ai/feed/",
    "KnowTechie AI": "https://knowtechie.com/category/ai/feed/",
    "AIModels.fyi": "https://aimodels.substack.com/feed",
    "AI Now Institute": "https://ainowinstitute.org/category/news/feed",
    "SiliconANGLE AI": "https://siliconangle.com/category/ai/feed",
    "Stability AI": "https://stability.ai/blog?format=rss",
    "The Conversation AI": "https://theconversation.com/europe/topics/artificial-intelligence-ai-90/articles.atom",
    "Futurism AI": "https://futurism.com/categories/ai-artificial-intelligence/feed",
    "ScienceDaily AI": "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml",
    "TechRepublic AI": "https://www.techrepublic.com/rssfeeds/topic/artificial-intelligence/",

    "r/aipromptprogramming": "https://www.reddit.com/r/aipromptprogramming/.rss",

    # Newsletters/Substacks
    "Interconnects": "https://www.interconnects.ai/feed",
    "Latent Space": "https://www.latent.space/feed",
    "Chain of Thought": "https://every.to/chain-of-thought/feed.xml",
    "Synthedia": "https://synthedia.substack.com/feed",
    "The Algorithmic Bridge": "https://thealgorithmicbridge.substack.com/feed",
    "Data Machina": "https://datamachina.substack.com/feed",
    "Generational": "https://www.generational.pub/feed",
    "Unwind AI": "https://unwindai.substack.com/feed",

    # Company Blogs
    "Weights & Biases": "https://wandb.ai/fully-connected/rss.xml",
    "Lightning AI": "https://lightning.ai/pages/feed/",
    "Explosion": "https://explosion.ai/feed",
    "Uber Engineering": "https://eng.uber.com/category/articles/ai/feed",
    "Mila Quebec": "https://mila.quebec/en/feed/",
    

    # AI-Focused Tech News
    "The Register AI": "https://www.theregister.com/software/ai_ml/headlines.atom",
    "Tech Monitor": "https://techmonitor.ai/feed",
    "ZDNET AI": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",

    # Analysis/Opinion
    "THE DECODER": "https://the-decoder.com/feed/",
    "MarkTechPost": "https://www.marktechpost.com/feed",
    "Unite.AI": "https://www.unite.ai/feed/",
    "Synced": "https://syncedreview.com/feed",
    "TechTalks": "https://bdtechtalks.com/feed/",
    "AIhub": "https://aihub.org/feed?cat=-473",

    # Medium Publications
    "Towards Data Science": "https://towardsdatascience.com/feed",
    "Towards AI": "https://pub.towardsai.net/feed",

    # Product Discovery
    "Product Hunt": "https://www.producthunt.com/feed",
}

# Newsletter Categories (single choice)
CATEGORIES = [
    "Tools and Products",
    "Legal and Regulations",
    "Funding and M&A", 
    "Security and Privacy",
    "Events and Conferences",
    "Research and Studies"
]

# Industries
INDUSTRIES = [
    "Healthcare and Medicine",
    "Manufacturing and Robotics",
    "Software and Development",
    "Finance and Banking",
    "Education and EdTech",
    "Retail and E-commerce",
    "Transportation and Autonomous Vehicles",
    "Media and Entertainment",
    "Agriculture and Food",
    "Energy and Utilities",
    "Legal and Law",
    "Marketing and Advertising",
    "Cybersecurity",
    "Government and Public Sector",
    "Real Estate and Construction",
    "Human Resources and Recruitment",
    "Customer Service and Support",
    "Telecommunications",
    "General AI"
]

# Scraping settings
SCRAPING_TIMEOUT = 15
MIN_ARTICLE_LENGTH = 200
USER_AGENT = 'Mozilla/5.0 (compatible; AI-Newsletter-Bot/1.0)'