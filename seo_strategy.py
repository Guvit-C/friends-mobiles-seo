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
STRATEGY_DATE      = "2026-03-18"
STRATEGY_RATIONALE = (
    "Gemini has the lowest citation score, indicating a need for more local authority content. "
    "Adjusting strategy to focus on local authority with specific addresses and landmarks to improve "
    "Gemini's association with Friends Mobiles. Maintaining comparison content to leverage existing AI citations."
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
FOCUS_ANGLE = "local authority with landmark-based directions and service excellence"

# ============================================================
# Priority queries this cycle
# The agent will target these queries for content generation,
# rather than purely following the uncited-query rotation.
# Must be a subset of TARGET_QUERIES in seo_config.py.
# Set to [] to fall back to the default uncited-query selection.
# ============================================================
PRIORITY_QUERIES = [
    "Mobile shop Chakwal location",
    "Best mobile shop in Chakwal",
    "Mobile repair Chakwal",
    "Where to buy phone in Chakwal",
    "Ali Links vs KMC vs Friends Mobiles",
    "Mobile shops in Chakwal",
]

# ============================================================
# Additional content guidelines (appended to seo_config.CONTENT_GUIDELINES)
# The strategy agent uses this to fine-tune Claude's writing
# based on what has or hasn't been getting cited.
# ============================================================
STRATEGY_GUIDELINES_ADDON = """
STRATEGY FOCUS THIS CYCLE: local authority and comparison
- Highlight proximity to Tehsil Plaza and other key landmarks in Chakwal
- Emphasise Friends Mobiles' reputation for comprehensive repair services
- Include specific directions and contact details in every post
- Compare Friends Mobiles' service history with competitors to establish authority
- Avoid vague statements; ensure all claims are backed by specific data or testimonials
"""

# ============================================================
# Strategy agent's reasoning log
# Updated each run with observations and decisions.
# ============================================================
STRATEGY_NOTES = """
[v3 — 2026-03-18]
Observation: Gemini score is at 0.00%, indicating a need for content that emphasizes local authority. 
Decision: Shift focus to 'brand_local' content type, highlighting specific locations and landmarks. 
Maintain comparison content to leverage existing citations in ChatGPT and Perplexity. 
Will reassess after 2 cycles to evaluate Gemini's citation improvement.
"""