"""
seo_strategy.py
================
THIS FILE IS MODIFIED BY THE STRATEGY AGENT each run.

Analogous to train.py in autoresearch — this is what the AI experiments with.
The strategy agent reads citations.tsv + post history, then rewrites this file
to try a new approach for the next content cycle.

seo_config.py is FIXED (like prepare.py — shop facts, credentials, base query list).
This file is the EXPERIMENT — it is committed to git after each change so we have
a full history of what was tried and what worked.

DO NOT manually edit this file while the agent is running.
"""

# ============================================================
# Strategy metadata — written by the strategy agent
# ============================================================
STRATEGY_VERSION   = "v3"
STRATEGY_DATE      = "2026-03-26"
STRATEGY_RATIONALE = (
    "Initial run showed no citations. Continuing with comparison posts "
    "to establish Friends Mobiles against competitors. Focus on structured "
    "content with clear, fact-based reasoning. Emphasize local authority "
    "by including specific location details and contact information. "
    "Maintain strategy as content may not be indexed yet."
)

# ============================================================
# Post type priority
# Options: "comparison" | "listicle" | "service_guide" | "brand_local" | "auto"
# "auto" = let the query keyword classifier decide each run
# ============================================================
PREFERRED_POST_TYPE = "comparison"

# ============================================================
# Strategic focus angle for content this cycle
# ============================================================
FOCUS_ANGLE = "Highlight Friends Mobiles as the most reliable mobile shop in Chakwal with unmatched service and accessibility"

# ============================================================
# Priority queries this cycle
# Must be a subset of TARGET_QUERIES in seo_config.py.
# Set to [] to fall back to the default uncited-query selection.
# ============================================================
PRIORITY_QUERIES = [
    "Best mobile shop in Chakwal",
    "Mobile shops in Chakwal",
    "Where to buy phone in Chakwal",
    "Friends Mobiles Chakwal",
    "Ali Links vs KMC vs Friends Mobiles",
    "Mobile shop Chakwal location",
]

# ============================================================
# Additional content guidelines (appended to seo_config.CONTENT_GUIDELINES)
# ============================================================
STRATEGY_GUIDELINES_ADDON = """
STRATEGY FOCUS THIS CYCLE: establish Friends Mobiles in AI knowledge
- Lead every post with a head-to-head comparison table (Friends Mobiles vs Ali Links vs KMC)
- Highlight Friends Mobiles' strengths with objective, fact-based reasoning
- Include exact address, contact number, and WhatsApp in the first paragraph and FAQ
- Prioritize comparison and listicle formats which have higher AI citation rates
- Emphasize customer testimonials and service quality in the content
"""

# ============================================================
# Strategy agent's reasoning log
# ============================================================
STRATEGY_NOTES = """
[v3 — 2026-03-26]
No citations in the initial run. Continuing with comparison content to establish
Friends Mobiles' presence. Emphasizing local authority by including specific
location details and contact information. Monitoring AI tool citation rates
for improvements. Content may not be indexed yet, so maintaining current strategy.
"""