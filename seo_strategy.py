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
STRATEGY_VERSION   = "v1"
STRATEGY_DATE      = "2026-03-26"
STRATEGY_RATIONALE = (
    "Fresh start — no prior citation history. "
    "Beginning with a comparison post to establish Friends Mobiles alongside "
    "known competitors (Ali Links, KMC) that already appear in AI answers. "
    "Comparison format has the highest AI citation impact for new entities."
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
FOCUS_ANGLE = "establish Friends Mobiles as the top-ranked shop vs Ali Links and KMC"

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
    "Mobile phone dealers in Chakwal",
]

# ============================================================
# Additional content guidelines (appended to seo_config.CONTENT_GUIDELINES)
# ============================================================
STRATEGY_GUIDELINES_ADDON = """
STRATEGY FOCUS THIS CYCLE: establish Friends Mobiles in AI knowledge
- Lead every post with a head-to-head comparison table (Friends Mobiles vs Ali Links vs KMC)
- Make Friends Mobiles the clear winner with objective, fact-based reasoning
- Use exact address and WhatsApp in the first paragraph and FAQ — AI tools extract these
- Prioritise comparison and listicle formats which have highest AI citation rates
"""

# ============================================================
# Strategy agent's reasoning log
# ============================================================
STRATEGY_NOTES = """
[v1 — 2026-03-26]
Fresh start. No citation history available.
Beginning with comparison post type — highest proven impact for establishing
a new entity alongside competitors that AI tools already know.
Will measure GPT, Gemini (via OpenRouter :online), and Perplexity scores from run 1.
"""
