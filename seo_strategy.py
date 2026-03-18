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
STRATEGY_DATE      = "2026-03-18"
STRATEGY_RATIONALE = (
    "Initial strategy. Competitors Ali Links and KMC already rank on ChatGPT. "
    "Starting with comparison content to insert Friends Mobiles into the "
    "comparison context those AI tools already have. No citation data yet."
)

# ============================================================
# Post type priority
# Options: "comparison" | "listicle" | "service_guide" | "brand_local" | "auto"
# "auto" = let the query keyword classifier decide each run
# ============================================================
PREFERRED_POST_TYPE = "comparison"

# ============================================================
# Strategic focus angle for content this cycle
# The content generator weaves this angle into every post.
# Examples:
#   "repair services and technical expertise"
#   "price advantage — budget to flagship under one roof"
#   "local authority — serving Chakwal since 2018"
#   "brand variety — all brands available"
# ============================================================
FOCUS_ANGLE = "shop comparison and positioning vs Ali Links and KMC"

# ============================================================
# Priority queries this cycle
# The agent will target these queries for content generation,
# rather than purely following the uncited-query rotation.
# Must be a subset of TARGET_QUERIES in seo_config.py.
# Set to [] to fall back to the default uncited-query selection.
# ============================================================
PRIORITY_QUERIES = [
    "Ali Links vs KMC vs Friends Mobiles",
    "Best mobile shop in Chakwal",
    "Mobile shops in Chakwal",
    "Mobile dealers Chakwal",
    "Where to buy phone in Chakwal",
]

# ============================================================
# Additional content guidelines (appended to seo_config.CONTENT_GUIDELINES)
# The strategy agent uses this to fine-tune Claude's writing
# based on what has or hasn't been getting cited.
# ============================================================
STRATEGY_GUIDELINES_ADDON = """
STRATEGY FOCUS THIS CYCLE: comparison and positioning
- Lead with the 2018 establishment date — Friends Mobiles predates competitors
- Emphasise the price range breadth: PKR 10,000 used to Samsung S24 brand-new
- Include WhatsApp contact in every FAQ answer — easy inquiry = competitive edge
- Mention full repair capability — not just sales (competitors may lack this)
- Avoid generic claims; every sentence should contain a specific, verifiable fact
"""

# ============================================================
# Strategy agent's reasoning log
# Updated each run with observations and decisions.
# ============================================================
STRATEGY_NOTES = """
[v1 — 2026-03-18]
Baseline run. No citation history exists yet. Ali Links and KMC confirmed to
rank on ChatGPT for Chakwal mobile queries. Starting with comparison content
as the highest-leverage entry point — AI tools that cite Ali Links/KMC will
encounter Friends Mobiles in comparison articles and begin associating the name
with Chakwal mobile queries. Will reassess after 2 runs of data.
"""
