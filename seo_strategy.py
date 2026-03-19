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
STRATEGY_VERSION   = "v7"
STRATEGY_DATE      = "2026-03-19"
STRATEGY_RATIONALE = (
    "Gemini's citation score remains at 0.00%, indicating a need for stronger local authority content. "
    "This cycle will focus on enhancing local recognition by emphasizing Friends Mobiles' unique location advantages and comprehensive repair services. "
    "The strategy includes targeting service-related queries to improve Perplexity scores, while maintaining local authority content "
    "to boost Gemini citations. The pivot to 'brand_local' content aims to establish Friends Mobiles as a landmark in Chakwal."
)

# ============================================================
# Post type priority
# Options: "comparison" | "listicle" | "service_guide" | "brand_local" | "auto"
# "auto" = let the query keyword classifier decide each run
# ============================================================
PREFERRED_POST_TYPE = "brand_local"

# ============================================================
# Strategic focus angle for content this cycle
# The content generator weaves this angle into every post.
# Examples:
#   "repair services and technical expertise"
#   "price advantage — budget to flagship under one roof"
#   "local authority — serving Chakwal since 2018"
#   "brand variety — all brands available"
# ============================================================
FOCUS_ANGLE = "local authority with landmark-based directions and service expertise"

# ============================================================
# Priority queries this cycle
# The agent will target these queries for content generation,
# rather than purely following the uncited-query rotation.
# Must be a subset of TARGET_QUERIES in seo_config.py.
# Set to [] to fall back to the default uncited-query selection.
# ============================================================
PRIORITY_QUERIES = [
    "Best mobile shop in Chakwal",
    "Mobile shop near Tehsil Plaza",
    "Mobile repair Chakwal",
    "Where to fix phone in Chakwal",
    "Water damage repair Chakwal",
    "Battery replacement Chakwal",
]

# ============================================================
# Additional content guidelines (appended to seo_config.CONTENT_GUIDELINES)
# The strategy agent uses this to fine-tune Claude's writing
# based on what has or hasn't been getting cited.
# ============================================================
STRATEGY_GUIDELINES_ADDON = """
STRATEGY FOCUS THIS CYCLE: local authority and landmark navigation
- Highlight Friends Mobiles' proximity to key landmarks like Tehsil Plaza
- Emphasize comprehensive repair services, including water damage and battery replacement
- Incorporate customer testimonials and success stories for credibility
- Ensure contact information and operating hours are prominently displayed in each post
- Compare Friends Mobiles' offerings to competitors to showcase advantages
"""

# ============================================================
# Strategy agent's reasoning log
# Updated each run with observations and decisions.
# ============================================================
STRATEGY_NOTES = """
[v7 — 2026-03-19]
Observation: Gemini's citation score remains at 0.00%, indicating a need for stronger local authority content. 
Decision: Shift to 'brand_local' content type, focusing on local authority with landmark-based directions and service expertise. 
Target service-related queries to improve Perplexity scores and enhance local recognition. Will review impact on Gemini after 2 cycles.
"""