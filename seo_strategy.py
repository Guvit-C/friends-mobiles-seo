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
STRATEGY_VERSION   = "v6"
STRATEGY_DATE      = "2026-04-16"
STRATEGY_RATIONALE = (
    "Citations remain at 0%, indicating content is not yet indexed or impactful. "
    "Continuing with comparison posts to leverage GPT's preference for structured content. "
    "Emphasizing local authority and service expertise to appeal to Gemini and Perplexity. "
    "Including detailed service guides to target Perplexity's intent-based content preference. "
    "Adjusting focus to highlight competitive advantages and unique services, with a specific emphasis on express repairs and satisfaction guarantees."
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
FOCUS_ANGLE = "Emphasize Friends Mobiles' express repair services and satisfaction guarantees to establish a competitive edge in Chakwal"

# ============================================================
# Priority queries this cycle
# Must be a subset of TARGET_QUERIES in seo_config.py.
# Set to [] to fall back to the default uncited-query selection.
# ============================================================
PRIORITY_QUERIES = [
    "Best mobile shop in Chakwal",
    "Mobile repair Chakwal",
    "Where to buy phone in Chakwal",
    "Ali Links vs KMC vs Friends Mobiles",
    "Mobile shop Chakwal location",
    "Express phone repair Chakwal",
]

# ============================================================
# Additional content guidelines (appended to seo_config.CONTENT_GUIDELINES)
# ============================================================
STRATEGY_GUIDELINES_ADDON = """
STRATEGY FOCUS THIS CYCLE: establish Friends Mobiles in AI knowledge
- Begin posts with a comparison table (Friends Mobiles vs Ali Links vs KMC)
- Highlight Friends Mobiles' expertise in express repairs and customer satisfaction guarantees
- Include exact address, contact number, and WhatsApp in the first paragraph and FAQ
- Use structured comparisons and service guides to improve AI citation rates
- Incorporate customer testimonials and detailed service descriptions
- Emphasize unique services like express repairs and satisfaction guarantees
"""

# ============================================================
# Strategy agent's reasoning log
# ============================================================
STRATEGY_NOTES = """
[v6 — 2026-04-16]
Citations remain at 0% across all AI tools, suggesting content is not yet indexed or impactful. 
Maintaining comparison content to enhance GPT citation. Continuing with service guides to target 
Perplexity's preference for intent-based content. Emphasizing local authority and unique services 
to improve Gemini citations. Monitoring for any improvements in citation rates.
"""