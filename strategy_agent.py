"""
strategy_agent.py
==================
The strategy modifier — analogous to the AI agent modifying train.py in autoresearch.

After each citation check, this agent:
  1. Reads citations.tsv (full run history + scores)
  2. Reads seo_strategy.py (current strategy)
  3. Reads recent posts in posts/ (what content was actually generated)
  4. Calls GPT-4o to analyze results and write a new seo_strategy.py
  5. Validates the output (must be valid Python)
  6. Overwrites seo_strategy.py (committed to git by GitHub Actions)

Uses GPT-4o (via direct OpenAI) — a different model from the content generator
(Claude Sonnet) to get an independent analytical perspective.

The keep/discard logic mirrors autoresearch:
  - If citation_score improved → new strategy stays (git keeps the commit)
  - If score declined 2+ consecutive runs → strategy agent is instructed to
    recognise this and pivot significantly (not just tweak)
"""

import os
import re
import csv
import ast
import datetime
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Read current strategy file as raw text
# ---------------------------------------------------------------------------

def _read_current_strategy(strategy_file: str) -> str:
    try:
        return Path(strategy_file).read_text(encoding="utf-8")
    except Exception:
        return "(strategy file not found — this may be the first run)"


# ---------------------------------------------------------------------------
# Load full citation history from TSV
# ---------------------------------------------------------------------------

def _load_citation_history(results_file: str) -> list[dict]:
    path = Path(results_file)
    if not path.exists():
        return []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f, delimiter="\t"))
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Summarise recent post types and content angles from post files
# ---------------------------------------------------------------------------

def _summarise_posts(posts_dir: str, max_posts: int = 5) -> str:
    posts_path = Path(posts_dir)
    if not posts_path.exists():
        return "No posts generated yet."

    posts = sorted(posts_path.glob("*.md"), reverse=True)[:max_posts]
    if not posts:
        return "No posts generated yet."

    lines = []
    for p in posts:
        try:
            content = p.read_text(encoding="utf-8")
            title_m = re.search(r"^title:\s*(.+)$", content, re.MULTILINE)
            type_m  = re.search(r"^post_type:\s*(.+)$", content, re.MULTILINE)
            date_m  = re.search(r"^date:\s*(.+)$", content, re.MULTILINE)
            title     = title_m.group(1).strip() if title_m else p.stem
            post_type = type_m.group(1).strip()  if type_m  else "unknown"
            date      = date_m.group(1).strip()   if date_m  else "?"
            lines.append(f"  {date} | {post_type:12s} | {title[:60]}")
        except Exception:
            lines.append(f"  {p.name} (unreadable)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Detect consecutive declining runs (signal to pivot strategy)
# ---------------------------------------------------------------------------

def _consecutive_declines(history: list[dict]) -> int:
    """Return number of consecutive 'watch' (no improvement) runs at the end."""
    count = 0
    for row in reversed(history):
        if row.get("status") == "watch":
            count += 1
        else:
            break
    return count


# ---------------------------------------------------------------------------
# Build the analysis prompt for GPT-4o
# ---------------------------------------------------------------------------

def _build_strategy_prompt(
    history: list[dict],
    current_strategy: str,
    posts_summary: str,
    consecutive_declines: int,
    all_queries: list[str],
) -> str:

    if not history:
        history_block = "No runs yet — this is the first execution."
    else:
        rows = []
        for row in history[-8:]:   # last 8 runs max
            rows.append(
                f"  {row.get('date','?')}  score={row.get('citation_score','?')}%  "
                f"status={row.get('status','?')}  "
                f"gpt={row.get('gpt_score','?')}%  "
                f"gemini={row.get('gemini_score','?')}%  "
                f"perplexity={row.get('perplexity_score','?')}%  "
                f"post={row.get('new_post','none')}"
            )
        history_block = "\n".join(rows)

    queries_block = "\n".join(f"  - {q}" for q in all_queries)

    decline_warning = ""
    if consecutive_declines >= 2:
        decline_warning = f"""
⚠️  WARNING: {consecutive_declines} consecutive runs with no improvement.
The current strategy is not working. You MUST make a significant strategic pivot —
not just minor tweaks. Try a completely different FOCUS_ANGLE, PREFERRED_POST_TYPE,
and PRIORITY_QUERIES. Think: what hasn't been tried yet?
"""

    return f"""You are the strategy agent for an AEO/GEO citation-building campaign.

MISSION: Friends Mobiles is a mobile phone shop in Chakwal, Pakistan. The goal is
to make AI tools (ChatGPT, Gemini, Perplexity) cite "Friends Mobiles" when anyone
asks about buying or repairing phones in Chakwal. We measure success by citation_score
— the % of (query × AI tool) pairs where Friends Mobiles is mentioned in the response.

YOUR ROLE: Analyse the citation history and decide what content strategy to run next.
You will output a complete replacement for seo_strategy.py.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CITATION HISTORY (last 8 runs)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{history_block}
{decline_warning}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECENT POSTS GENERATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{posts_summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CURRENT STRATEGY (seo_strategy.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{current_strategy}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALL AVAILABLE QUERIES (from seo_config.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{queries_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYSIS RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Look at which AI tool has the lowest score — that tool needs targeted content.
2. If Perplexity score lags: prioritise service and repair queries (Perplexity favours intent-based content).
3. If GPT score lags: prioritise comparison and listicle content (GPT cites structured comparisons).
4. If Gemini score lags: prioritise local authority content with specific addresses and landmarks.
5. If all scores are 0% after 2+ runs: content is not indexed yet — maintain strategy but update STRATEGY_NOTES.
6. If score is improving consistently: keep the same PREFERRED_POST_TYPE, refine FOCUS_ANGLE.
7. If score declined 2+ runs: pivot PREFERRED_POST_TYPE and FOCUS_ANGLE significantly.
8. Choose PRIORITY_QUERIES that directly match the weakest AI tool's query patterns.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Output ONLY a complete, valid Python file that replaces seo_strategy.py.
No explanation before or after. No markdown fences. Just the Python file content.

Rules for the output:
- Increment STRATEGY_VERSION (e.g. "v1" → "v2")
- Set STRATEGY_DATE to today: {datetime.date.today().isoformat()}
- Write STRATEGY_RATIONALE explaining WHY you made these specific changes
- Set PREFERRED_POST_TYPE based on your analysis
- Set FOCUS_ANGLE to a specific, actionable angle (not generic)
- Set PRIORITY_QUERIES to 4-6 queries from the available list above
- Write STRATEGY_GUIDELINES_ADDON with specific writing instructions that address gaps
- Update STRATEGY_NOTES with a timestamped entry explaining what you observed and decided
- Preserve the docstring at the top of the file
"""


# ---------------------------------------------------------------------------
# Validate the output is valid Python before saving
# ---------------------------------------------------------------------------

def _validate_python(code: str) -> tuple[bool, str]:
    try:
        ast.parse(code)
        # Also check required fields exist
        required = [
            "STRATEGY_VERSION", "STRATEGY_DATE", "STRATEGY_RATIONALE",
            "PREFERRED_POST_TYPE", "FOCUS_ANGLE", "PRIORITY_QUERIES",
            "STRATEGY_GUIDELINES_ADDON", "STRATEGY_NOTES",
        ]
        for field in required:
            if field not in code:
                return False, f"Missing required field: {field}"
        return True, "OK"
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_strategy_update(
    results_file: str,
    strategy_file: str,
    posts_dir: str,
    all_queries: list[str],
    dry_run: bool = False,
) -> Optional[str]:
    """
    Analyse citation history and rewrite seo_strategy.py with updated strategy.

    Returns a short summary string of what changed, or None on failure.
    """
    print("\nRunning strategy agent (GPT-4o)...")

    history         = _load_citation_history(results_file)
    current         = _read_current_strategy(strategy_file)
    posts_summary   = _summarise_posts(posts_dir)
    declines        = _consecutive_declines(history)

    print(f"  History: {len(history)} runs  |  Consecutive no-improvement: {declines}")

    prompt = _build_strategy_prompt(
        history=history,
        current_strategy=current,
        posts_summary=posts_summary,
        consecutive_declines=declines,
        all_queries=all_queries,
    )

    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise SEO strategy analyst. You output valid Python "
                        "files only — no markdown, no explanation, no code fences."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2048,
            temperature=0.4,   # Low temp — we want consistent, reasoned output not creative
        )

        new_strategy = response.choices[0].message.content.strip()

        # Strip accidental markdown fences if model adds them
        new_strategy = re.sub(r"^```python\s*", "", new_strategy)
        new_strategy = re.sub(r"^```\s*",        "", new_strategy)
        new_strategy = re.sub(r"\s*```$",         "", new_strategy)

        valid, reason = _validate_python(new_strategy)
        if not valid:
            print(f"  Strategy output invalid ({reason}) — keeping current strategy.")
            return None

        # Extract version and rationale for the summary
        ver_m = re.search(r'STRATEGY_VERSION\s*=\s*["\'](.+?)["\']', new_strategy)
        rat_m = re.search(r'STRATEGY_RATIONALE\s*=\s*["\'](.+?)["\']', new_strategy, re.DOTALL)
        version   = ver_m.group(1) if ver_m else "?"
        rationale = rat_m.group(1)[:120] if rat_m else "?"

        if dry_run:
            print(f"  [DRY RUN] Would write strategy {version}: {rationale}...")
            return f"dry-run: {version}"

        # Back up current strategy before overwriting
        backup = Path(strategy_file).with_suffix(".py.bak")
        backup.write_text(current, encoding="utf-8")

        Path(strategy_file).write_text(new_strategy, encoding="utf-8")
        print(f"  Strategy updated to {version}: {rationale[:80]}...")
        return f"strategy updated to {version}"

    except Exception as e:
        print(f"  Strategy agent failed: {e}")
        return None
