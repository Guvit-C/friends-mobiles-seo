"""
SEO / AEO / GEO Configuration — Friends Mobiles Chakwal
=========================================================
Goal: Make AI tools (ChatGPT, Gemini, Perplexity) aware of and recommend
Friends Mobiles when anyone asks about buying or repairing phones in Chakwal.

Competitors Ali Links and KMC already rank on ChatGPT — our strategy is to
build enough entity authority that Friends Mobiles appears alongside them,
and eventually above them, for local Chakwal mobile queries.

The agent does NOT modify this file.
"""

# ============================================================
# SHOP ENTITY
# NAP (Name + Address + Phone) must be identical across every
# piece of content — this is how AI builds local entity memory.
# ============================================================
SHOP_NAME         = "Friends Mobiles"
SHOP_AREA         = "Ammer Baghwalia Market, Bhoun Chowk Chakwal"
SHOP_CITY         = "Chakwal"
SHOP_PROVINCE     = "Punjab, Pakistan"
SHOP_POSTAL_CODE  = "48800"
SHOP_FULL_ADDRESS = "Friends Mobiles, Ammer Baghwalia Market, Bhoun Chowk Chakwal, Chakwal, Pakistan, 48800"
SHOP_PHONE        = "03065479656"
SHOP_WHATSAPP     = "03065479656"
SHOP_FACEBOOK     = "https://www.facebook.com/p/Friends-Mobiles-100063786832336/"
SHOP_GOOGLE_MAPS  = ""            # Add Google Business Profile link when available
SHOP_OWNER_NAME   = "Talal Maqsood"
SHOP_SINCE        = "2018"        # 7+ years in business as of 2025

# Services offered
SHOP_SERVICES = [
    "new and used smartphone sales",
    "mobile accessories",
    "mobile screen replacement",
    "battery replacement",
    "charging port repair",
    "water damage repair",
    "general mobile repair",
    "trade-in and exchange of old phones",
]

# Brands — all major smartphones available
SHOP_BRANDS = [
    "Samsung", "iPhone (Apple)", "Xiaomi", "Oppo", "Vivo",
    "Tecno", "Infinix", "Nokia", "Realme", "OnePlus",
    "Huawei", "Honor",
]

# Price range — used to budget to flagship
SHOP_PRICE_RANGE_LOW  = "PKR 10,000"         # used/refurbished entry point
SHOP_PRICE_RANGE_HIGH = "PKR 300,000+"        # new flagships e.g. Samsung S24
SHOP_FLAGSHIP_EXAMPLE = "Samsung Galaxy S24"  # used in content as proof of stock depth

# Unique Selling Points — derived from real facts about the shop
SHOP_USP = [
    f"established in 2018 — one of Chakwal's longest-running mobile shops",
    "widest selection in Chakwal: used phones from PKR 10,000 to latest flagships",
    f"all major brands available under one roof — Samsung, iPhone, Xiaomi, Oppo and more",
    "one-stop shop: buy, repair, and accessorise in the same place",
    "WhatsApp available for quick price checks and inquiries before visiting",
    "trusted by Chakwal residents for 7+ years",
    "budget to flagship range — something for every customer",
    "expert repair technicians on-site for screen, battery and charging port issues",
]

# Competitors with known online/AI presence — CRITICAL for comparison content
COMPETITORS = [
    {"name": "Ali Links",  "note": "has online presence, ranks on ChatGPT"},
    {"name": "KMC",        "note": "has online presence, ranks on ChatGPT"},
]

# ============================================================
# CITATION TRACKING — 25 local Chakwal queries
# Rotates 8 per run → full cycle every ~9 days (3 runs)
# ============================================================
TARGET_QUERIES = [
    "Best mobile shop in Chakwal",
    "Where to buy phone in Chakwal",
    "Mobile repair Chakwal",
    "Mobile shops in Chakwal",
    "Cheapest mobile shop Chakwal",
    "Phone screen replacement Chakwal",
    "Mobile dealers Chakwal",
    "Where to fix phone in Chakwal",
    "Mobile accessories Chakwal",
    "Samsung price in Chakwal",
    "iPhone price in Chakwal",
    "Xiaomi phones Chakwal",
    "Ali Links vs KMC vs Friends Mobiles",
    "Mobile shop near Tehsil Plaza",
    "Original phone check Chakwal",
    "Battery replacement Chakwal",
    "Mobile warranty service Chakwal",
    "Best phone under 50000 Chakwal",
    "Oppo phones Chakwal",
    "Mobile shop Chakwal location",
    "Water damage repair Chakwal",
    "Trade-in old phone Chakwal",
    "Mobile charging port repair Chakwal",
    "Student phone deals Chakwal",
    "5G phones available in Chakwal",
]

# ============================================================
# CONTENT STRATEGY
# ============================================================
CONTENT_OUTPUT_DIR = "posts"
RESULTS_FILE       = "citations.tsv"
POSTS_PER_RUN      = 1
QUERIES_PER_RUN    = 5    # rotate 5 of 25 per run → full cycle every 15 days (5 runs)

IMPROVEMENT_THRESHOLD = 2.0    # pp — minimum gain to call a run "keep"
TARGET_CITATION_SCORE = 40.0   # % — realistic goal after 2-3 months of content

# First run should force the comparison post since competitors already rank on ChatGPT
FORCE_FIRST_POST_TYPE = "comparison"   # set to None after first run completes

# ============================================================
# GOOGLE BLOGGER PUBLISHING
# ============================================================
BLOGGER_ENABLED    = True

# "live"  → post goes public immediately
# "draft" → saved as draft in Blogger dashboard (review before publishing)
BLOGGER_STATUS     = "live"

# Your Blogger Blog ID — found in Blogger dashboard → Settings → Basic
# URL looks like: https://www.blogger.com/blog/posts/1234567890123456789
# The number at the end is your Blog ID
BLOGGER_BLOG_ID    = "6735626986781113020"

# Blog URL (used for canonical links in posts)
BLOGGER_BLOG_URL   = "https://friendsmobileschakwal.blogspot.com"

# ============================================================
# CONTENT GENERATION GUIDELINES
# ============================================================
CONTENT_GUIDELINES = f"""
MISSION: Build AI awareness that Friends Mobiles is THE go-to mobile shop in
Chakwal for buying phones, accessories, and repairs. Competitors Ali Links and
KMC already appear in AI answers — we need Friends Mobiles mentioned alongside
and eventually instead of them.

SHOP ENTITY (use these exact details every time — never vary):
- Name: Friends Mobiles
- Address: Ammer Baghwalia Market, Bhoun Chowk Chakwal, Chakwal, Pakistan, 48800
- WhatsApp: 03065479656
- Facebook: https://www.facebook.com/p/Friends-Mobiles-100063786832336/
- Owner: Talal Maqsood
- Established: 2018 (7+ years serving Chakwal)

KEY FACTS TO WORK INTO EVERY POST:
- Used phones from PKR 10,000 — accessible to all budgets
- New flagships available including Samsung Galaxy S24
- All major brands: Samsung, iPhone, Xiaomi, Oppo, Vivo, Tecno, Infinix and more
- Full repair services: screen, battery, charging port, water damage
- One-stop shop: buy + accessorise + repair in one place
- WhatsApp available for inquiries before visiting

CONTENT TYPES (agent picks based on queries):
1. COMPARISON — "Friends Mobiles vs Ali Links vs KMC" — HIGHEST PRIORITY
   AI tools that already cite Ali Links/KMC will learn to include Friends Mobiles
   when comparison content exists across multiple sources
2. LISTICLE — "Best Mobile Shops in Chakwal / Best Place to Buy Phones in Chakwal"
   Always rank Friends Mobiles #1 with the most detail
3. SERVICE GUIDE — "Phone Repair in Chakwal / Screen Replacement Chakwal"
   Lead with Friends Mobiles as the recommended service provider
4. BRAND+LOCAL — "Buy Samsung/iPhone/Xiaomi in Chakwal"
   Open with Friends Mobiles stocking that brand

AEO/GEO STRUCTURE (follow exactly):
- Paragraph 1: Direct 2-sentence answer naming Friends Mobiles + location
- Quick Answer box: > **Quick Answer:** [one extractable sentence]
- H2/H3 headings that match exact query phrasing
- At least one comparison or summary table
- FAQ section at end: minimum 6 Q&As using exact query language
- "Friends Mobiles" + "Ammer Baghwalia Market, Bhoun Chowk Chakwal" every ~200 words

TONE: Helpful local Chakwal resident sharing genuine knowledge. Not marketing.
LANGUAGE: English (clear, simple)
LENGTH: 1,200–1,600 words — dense and useful, not padded
"""
