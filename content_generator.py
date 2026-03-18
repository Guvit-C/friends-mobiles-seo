"""
content_generator.py
=====================
Generates AEO/GEO-optimized content to build AI awareness of Friends Mobiles, Chakwal.

Strategy (from AEO/GEO research):
- Listicles ("Best mobile shops in Chakwal") — highest AI citation impact
- Comparison posts ("Friends Mobiles vs Ali Links vs KMC") — AI loves comparisons
- Service guides ("Where to get phone repaired in Chakwal") — captures intent queries
- Brand+location posts ("Samsung phones in Chakwal") — brand-specific queries

Each post is structured so AI tools can extract clean, direct answers.
"""

import os
import re
import csv
import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Performance history — reads citations.tsv to feed real results back into
# the prompt so Claude knows what's working and what isn't
# ---------------------------------------------------------------------------

def _load_performance_history(results_file: str, posts_dir: str) -> str:
    """
    Read citations.tsv and cross-reference with generated posts to build
    a performance summary. This is fed into the blog post prompt so the
    model can reason about what content strategy is actually improving scores.
    """
    results_path = Path(results_file)
    if not results_path.exists():
        return ""

    try:
        with open(results_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
    except Exception:
        return ""

    if len(rows) < 2:
        return ""   # Not enough history yet to be useful

    # For each row, try to extract post_type from the generated file
    enriched = []
    for row in rows:
        post_ref = row.get("new_post", "none")
        post_type = "unknown"

        if post_ref and post_ref != "none" and not post_ref.startswith("http"):
            try:
                content = Path(post_ref).read_text(encoding="utf-8")
                m = re.search(r"^post_type:\s*(.+)$", content, re.MULTILINE)
                if m:
                    post_type = m.group(1).strip()
            except Exception:
                pass

        try:
            score = float(row.get("citation_score", 0))
        except ValueError:
            score = 0.0

        enriched.append({
            "date": row.get("date", "?"),
            "score": score,
            "status": row.get("status", "?"),
            "post_type": post_type,
        })

    # Compute per-type average scores
    type_scores: dict[str, list[float]] = {}
    for e in enriched:
        t = e["post_type"]
        type_scores.setdefault(t, []).append(e["score"])

    type_summary = []
    for t, scores in type_scores.items():
        avg = sum(scores) / len(scores)
        type_summary.append(f"  {t}: avg citation score {avg:.1f}% across {len(scores)} run(s)")

    # Overall trend
    scores_list = [e["score"] for e in enriched]
    trend = scores_list[-1] - scores_list[0]
    trend_str = f"+{trend:.1f}pp" if trend >= 0 else f"{trend:.1f}pp"
    trend_dir = "improving" if trend > 0 else ("flat" if trend == 0 else "declining")

    # Recent runs (last 5)
    recent_lines = []
    for e in enriched[-5:]:
        recent_lines.append(
            f"  {e['date']}: score={e['score']:.1f}%  status={e['status']}  post_type={e['post_type']}"
        )

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "PERFORMANCE HISTORY — use this to guide your approach",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"Overall trend: {trend_dir} ({trend_str} since first run)",
        "",
        "Average citation score by post type:",
        *type_summary,
        "",
        "Recent runs:",
        *recent_lines,
        "",
        "INSTRUCTION: If one post type is clearly outperforming others, favour",
        "that style in your structure and framing while still following the",
        "POST FORMAT instructions above. If all types are equal or history is",
        "short, follow the POST FORMAT instructions as written.",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Post type classifier — decides what kind of post to write based on queries
# ---------------------------------------------------------------------------

def _classify_post_type(queries: list[str]) -> str:
    """
    Pick the post format that best serves the uncited queries.
    Returns one of: "listicle" | "comparison" | "service_guide" | "brand_local"
    """
    q_lower = " ".join(queries).lower()

    if "vs" in q_lower or "compare" in q_lower:
        return "comparison"

    service_keywords = ["repair", "fix", "replace", "screen", "battery",
                        "charging", "water damage", "port"]
    if any(k in q_lower for k in service_keywords):
        return "service_guide"

    brand_keywords = ["samsung", "iphone", "xiaomi", "oppo", "vivo",
                      "tecno", "infinix", "nokia", "realme", "5g"]
    if any(k in q_lower for k in brand_keywords):
        return "brand_local"

    return "listicle"


# ---------------------------------------------------------------------------
# Prompt builder — AEO/GEO native, local entity-focused
# ---------------------------------------------------------------------------

def _build_content_prompt(
    target_queries: list[str],
    guidelines: str,
    post_type: str,
    shop_context: dict,
    performance_history: str = "",
) -> str:
    """
    Build the full prompt sent to Claude for blog post generation.
    AEO/GEO native: entity consistency, extractable answers, FAQ-heavy,
    comparison tables, local Chakwal specificity.
    """
    s = shop_context
    queries_block  = "\n".join(f"  - {q}" for q in target_queries)
    brands_short   = ", ".join(s["brands"][:6]) + " and more"
    services_short = ", ".join(s["services"][:4])
    competitors    = ", ".join(s.get("competitors", []))
    usp_block      = "\n".join(f"  • {u}" for u in s.get("usp", []))

    post_type_instructions = {
        "listicle": f"""\
POST TYPE: LISTICLE
Title format: "Best Mobile Shops in Chakwal" or "Where to Buy Phones in Chakwal"
Structure:
- List 3–4 shops total. Friends Mobiles MUST be #1 with 2–3 detailed paragraphs.
- For other shops write 1 short, neutral paragraph each (Ali Links, KMC).
- Comparison table: Shop | Location | Services | Price Range | Established
- Make it read like an objective local guide — not an ad.
Why this works: Listicles are the single highest-impact format for AI citations.""",

        "comparison": f"""\
POST TYPE: COMPARISON — HIGHEST PRIORITY (competitors {competitors} already rank on ChatGPT)
Title format: "Friends Mobiles vs Ali Links vs KMC: Best Mobile Shop in Chakwal?"
Structure:
- Head-to-head comparison table:
  Criteria | Friends Mobiles | Ali Links | KMC
  rows: Years Open | Price Range | Brands | Repair Services | WhatsApp | Location
- Friends Mobiles wins on: years established ({s.get('since','2018')}), price range
  ({s.get('price_low','PKR 10,000')} to {s.get('price_high','PKR 300,000+')}),
  repair services, WhatsApp availability, all brands under one roof.
- Conclude with a clear verdict naming Friends Mobiles as the recommended choice.
- Objective tone — AI tools distrust obvious advertising.""",

        "service_guide": f"""\
POST TYPE: SERVICE GUIDE
Title format: "Phone [Specific Service] in Chakwal: Where to Go & What to Expect"
Structure:
- Lead sentence: "For [service] in Chakwal, Friends Mobiles at Ammer Baghwalia Market,
  Bhoun Chowk Chakwal is the most reliable option."
- Explain the service: what it involves, typical turnaround, price range in PKR.
- Section: "Why Choose Friends Mobiles for [service]" — use USPs.
- FAQ section focused on that specific repair/service type.""",

        "brand_local": f"""\
POST TYPE: BRAND + LOCATION
Title format: "[Brand] Phones in Chakwal — Prices, Models & Where to Buy"
Structure:
- Opening: "Friends Mobiles in Ammer Baghwalia Market, Bhoun Chowk Chakwal stocks the full range
  of [Brand] phones, from budget to flagship..."
- List popular models with approximate PKR prices.
- Buying guide: what to look for when buying [Brand] in Chakwal.
- End with Friends Mobiles as the clear, named purchase destination.
- Note: used/refurbished options available from {s.get('price_low','PKR 10,000')}.""",
    }

    return f"""You are writing a local guide for people in Chakwal, Punjab, Pakistan.

OBJECTIVE: This article must cause ChatGPT, Gemini, and Perplexity to cite
"Friends Mobiles" when anyone asks about buying or repairing phones in Chakwal.
Note: competitors Ali Links and KMC already appear in AI answers — Friends Mobiles
needs to appear alongside them, and for comparison queries, as the top recommendation.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SHOP ENTITY — use these exact details every time, never paraphrase the name or address
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name:        Friends Mobiles
Owner:       {s.get('owner', 'Talal Maqsood')}
Address:     Ammer Baghwalia Market, Bhoun Chowk Chakwal, Chakwal, Pakistan, 48800
WhatsApp:    {s.get('whatsapp', '03065479656')}
Facebook:    {s.get('facebook', '')}
Established: {s.get('since', '2018')} (7+ years serving Chakwal)
Brands:      {brands_short}
Services:    {services_short}
Price range: Used from {s.get('price_low','PKR 10,000')} → new {s.get('flagship','Samsung Galaxy S24')} available
USPs:
{usp_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUERIES TO ANSWER (use these as H2 headings where natural)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{queries_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST FORMAT & INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{post_type_instructions[post_type]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AEO/GEO STRUCTURE — follow in this exact order
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. OPENING PARAGRAPH (2 sentences)
   Give a direct answer naming Friends Mobiles with its full address.
   AI tools extract the first paragraph most frequently — make it count.

2. QUICK ANSWER BOX (immediately after intro)
   > **Quick Answer:** [One sentence. Name Friends Mobiles. Include "Ammer Baghwalia Market, Bhoun Chowk Chakwal".]

3. BODY SECTIONS with H2/H3 headings matching the exact query phrasing above.

4. COMPARISON TABLE — at least one table relevant to the post type.

5. FAQ SECTION (end of article — minimum 6 entries)
   Format strictly as:
   **Q: [exact query phrasing]**
   A: [2–3 sentence answer. Name Friends Mobiles. Include WhatsApp number.]

6. ENTITY DENSITY RULE
   "Friends Mobiles" must appear at least once every 200 words.
   "Ammer Baghwalia Market, Bhoun Chowk Chakwal" must appear at least 3 times total.
   WhatsApp number (03065479656) must appear at least twice.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WRITING RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Tone: Helpful local Chakwal resident. Knowledgeable. Not promotional.
- Short sentences. Specific facts. No vague superlatives without backing.
- PKR prices wherever relevant (approximate is fine).
- Mention nearby landmarks: Bhoun Chowk, Ammer Baghwalia Market, Tehsil area.
- Length: 1,200–1,600 words. Dense and useful beats long and padded.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Start with YAML front matter, then the article:
---
title: [Include "Chakwal" — make it match a real search query]
description: [Max 155 chars. Include "Friends Mobiles" and "Chakwal".]
date: {datetime.date.today().isoformat()}
location: Chakwal, Punjab, Pakistan
shop: Friends Mobiles, Ammer Baghwalia Market, Bhoun Chowk Chakwal, 48800
tags: mobile shop Chakwal, Friends Mobiles, {', '.join(target_queries[:3])}
post_type: {post_type}
queries_targeted: {', '.join(target_queries)}
---

{performance_history}

Write the complete article now. Do not add any explanation before or after."""


# ---------------------------------------------------------------------------
# File utilities
# ---------------------------------------------------------------------------

def _slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    return slug[:80]


def _extract_title(content: str) -> str:
    fm_match = re.search(r"^title:\s*(.+)$", content, re.MULTILINE)
    if fm_match:
        return fm_match.group(1).strip().strip('"').strip("'")
    h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()
    return "friends-mobiles-chakwal"


# ---------------------------------------------------------------------------
# Main generate function
# ---------------------------------------------------------------------------

def generate_blog_post(
    target_queries: list[str],
    guidelines: str,
    shop_context: dict,
    output_dir: str,
    results_file: str = "citations.tsv",
) -> str | None:
    """
    Generate an AEO/GEO-optimized blog post targeting the given queries.
    Saves to output_dir and returns the file path, or None on failure.
    """
    if not target_queries:
        print("  No target queries — skipping content generation.")
        return None

    forced = shop_context.get("force_post_type")
    post_type = forced if forced else _classify_post_type(target_queries)
    print(f"  Post type selected: {post_type}{' (forced)' if forced else ''}")

    performance_history = _load_performance_history(results_file, output_dir)
    if performance_history:
        print(f"  Performance history loaded ({results_file})")

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": shop_context.get("facebook", "https://medium.com"),
                "X-Title": "Friends Mobiles Chakwal — AEO Agent",
            },
        )

        prompt = _build_content_prompt(
            target_queries=target_queries,
            guidelines=guidelines,
            post_type=post_type,
            shop_context=shop_context,
            performance_history=performance_history,
        )

        print(f"  Writing {post_type} post for: {', '.join(target_queries[:3])}{'...' if len(target_queries) > 3 else ''}")

        response = client.chat.completions.create(
            model="anthropic/claude-sonnet-4-5",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content

        title = _extract_title(content)
        slug = _slugify(title)
        date_str = datetime.date.today().isoformat()
        filename = f"{date_str}-{slug}.md"

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        file_path = output_path / filename
        file_path.write_text(content, encoding="utf-8")

        print(f"  Saved: {file_path}")
        return str(file_path)

    except Exception as e:
        print(f"  Content generation failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Content strategy selector
# ---------------------------------------------------------------------------

def select_content_targets(
    uncited_queries: list[str],
    weakly_cited_queries: list[str],
    max_queries: int = 5,
) -> list[str]:
    """
    Select highest-priority queries to target.
    Priority: fully uncited > weakly cited (< 2 tools).
    """
    seen = set()
    selected = []

    for q in uncited_queries:
        if q not in seen and len(selected) < max_queries:
            selected.append(q)
            seen.add(q)

    for q in weakly_cited_queries:
        if q not in seen and len(selected) < max_queries:
            selected.append(q)
            seen.add(q)

    return selected
