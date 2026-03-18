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
STRATEGY_VERSION   = "v5"
STRATEGY_DATE      = "2026-03-18"
STRATEGY_RATIONALE = (
    "Gemini's citation score remains at 0.00%, indicating a need for a focused strategy on local authority content. "
    "This cycle will emphasize Friends Mobiles' unique offerings and proximity to local landmarks to boost recognition. "
    "Service and repair guides will be highlighted to improve Perplexity scores, while maintaining comparison content "
    "to sustain ChatGPT and Perplexity citations."
)

# ============================================================
# Post type priority
# Options: "comparison" | "listicle" | "service_guide" | "brand_local" | "auto"
# "auto" = let the query keyword classifier decide each run
# ============================================================
PREFERRED_POST_TYPE = "service_guide"

# ============================================================
# Strategic focus angle for content this cycle
# The content generator weaves this angle into every post.
# Examples:
#   "repair services and technical expertise"
#   "price advantage — budget to flagship under one roof"
#   "local authority — serving Chakwal since 2018"
#   "brand variety — all brands available"
# ============================================================
FOCUS_ANGLE = "comprehensive repair services with landmark-based navigation"

# ============================================================
# Priority queries this cycle
# The agent will target these queries for content generation,
# rather than purely following the uncited-query rotation.
# Must be a subset of TARGET_QUERIES in seo_config.py.
# Set to [] to fall back to the default uncited-query selection.
# ============================================================
PRIORITY_QUERIES = [
    "Mobile repair Chakwal",
    "Where to fix phone in Chakwal",
    "Mobile shop Chakwal location",
    "Mobile shop near Tehsil Plaza",
    "Water damage repair Chakwal",
    "Battery replacement Chakwal",
]

# ============================================================
# Additional content guidelines (appended to seo_config.CONTENT_GUIDELINES)
# The strategy agent uses this to fine-tune Claude's writing
# based on what has or hasn't been getting cited.
# ============================================================
STRATEGY_GUIDELINES_ADDON = """
STRATEGY FOCUS THIS CYCLE: local authority and service expertise
- Provide clear directions from major landmarks like Tehsil Plaza
- Detail specific repair services offered by Friends Mobiles, including water damage and battery replacement
- Include customer testimonials and success stories to establish credibility
- Ensure all posts have contact information and operating hours prominently displayed
- Compare Friends Mobiles' services directly with competitors to highlight advantages
"""

# ============================================================
# Strategy agent's reasoning log
# Updated each run with observations and decisions.
# ============================================================
STRATEGY_NOTES = """
[v5 — 2026-03-18]
Observation: Gemini's citation score remains at 0.00%, indicating a need for stronger local authority content. 
Decision: Shift to 'service_guide' content type, focusing on comprehensive repair services and landmark-based navigation. 
Target service-related queries to improve Perplexity scores. Will review impact on Gemini after 2 cycles.
"""