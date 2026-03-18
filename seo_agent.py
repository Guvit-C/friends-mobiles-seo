"""
seo_agent.py
=============
Main SEO Autoresearch orchestrator.

Analogous to train.py in autoresearch — this is the file that runs each cycle.
It orchestrates the full loop:

  1. Run citation checks across GPT, Gemini, Perplexity
  2. Compare to previous best (from citations.tsv)
  3. Identify uncited / weakly-cited queries
  4. Generate a new optimized blog post targeting those queries
  5. Publish the post to Medium as a draft
  6. Log results to citations.tsv
  7. Print a summary

Run via: python seo_agent.py
Triggered by: GitHub Actions on a 24-hour schedule

The agent NEVER stops autonomously — GitHub Actions handles the schedule.
Each run is one "experiment" in the autoresearch loop.
"""

import os
import sys
import csv
import datetime
from pathlib import Path

# Load .env for local development (no-op in GitHub Actions where secrets are env vars)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on env vars being set externally

# Load configuration (fixed constants — agent reads, does not modify)
import seo_config as config

# Load current strategy (modified each run by strategy_agent)
try:
    import seo_strategy as strategy
except ImportError:
    strategy = None

from citation_checker import run_citation_check, CitationReport
from content_generator import generate_blog_post, select_content_targets
from blogger_publisher import publish_post_file as blogger_publish_file
from strategy_agent import run_strategy_update
from google_sheets_logger import log_run, log_citation_tests, log_blog_post
from email_reporter import send_report
from dashboard import generate_dashboard


# ---------------------------------------------------------------------------
# Results tracking (citations.tsv)
# ---------------------------------------------------------------------------

TSV_HEADER = ["date", "citation_score", "gpt_score", "gemini_score",
               "perplexity_score", "total_checks", "total_citations",
               "new_post", "status", "strategy", "description"]


def select_queries_for_run(all_queries: list, results_file: str, per_run: int) -> list:
    """
    Return a rotating slice of queries for this run.
    Offset is derived from the number of previous runs so it's stateless —
    no extra files needed, just counts rows in citations.tsv.
    """
    n = len(all_queries)
    if per_run >= n:
        return all_queries

    run_count = 0
    path = Path(results_file)
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            run_count = max(0, sum(1 for _ in f) - 1)  # subtract header row

    offset = (run_count * per_run) % n
    return [all_queries[(offset + i) % n] for i in range(per_run)]


def load_previous_best(results_file: str) -> float:
    """Read citations.tsv and return the best citation_score achieved so far."""
    path = Path(results_file)
    if not path.exists():
        return 0.0

    best = 0.0
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                try:
                    score = float(row.get("citation_score", 0))
                    if score > best:
                        best = score
                except ValueError:
                    pass
    except Exception:
        pass
    return best


def append_result(results_file: str, row: dict) -> None:
    """Append one result row to citations.tsv."""
    path = Path(results_file)
    write_header = not path.exists()

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TSV_HEADER, delimiter="\t")
        if write_header:
            writer.writeheader()
        writer.writerow(row)


# ---------------------------------------------------------------------------
# Summary printer (mirrors autoresearch's val_bpb summary block)
# ---------------------------------------------------------------------------

def print_summary(report: CitationReport, status: str, new_post: str | None,
                  prev_best: float) -> None:
    improvement = report.citation_score - prev_best
    sign = "+" if improvement >= 0 else ""
    print()
    print("---")
    print(f"date:               {report.run_date}")
    print(f"citation_score:     {report.citation_score:.1f}%  ({sign}{improvement:.1f}% vs prev best {prev_best:.1f}%)")
    print(f"gpt_score:          {report.score_for_tool('gpt'):.1f}%")
    print(f"gemini_score:       {report.score_for_tool('gemini'):.1f}%")
    print(f"perplexity_score:   {report.score_for_tool('perplexity'):.1f}%")
    print(f"total_checks:       {report.total_checks}")
    print(f"total_citations:    {report.total_citations}")
    print(f"uncited_queries:    {len(report.uncited_queries())}")
    print(f"new_post:           {new_post or 'none'}")
    print(f"status:             {status}")
    print("---")
    print()


# ---------------------------------------------------------------------------
# Main agent loop (single execution = one 24-hour "experiment")
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("AEO/GEO Agent — Friends Mobiles Chakwal")
    print(f"Shop:     {config.SHOP_NAME}, {config.SHOP_AREA}, {config.SHOP_CITY}")
    print(f"Queries:  {len(config.TARGET_QUERIES)} total, {config.QUERIES_PER_RUN or 'all'} per run")
    print(f"Run date: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    # Build shop context dict passed to content generator
    shop_context = {
        "name":           config.SHOP_NAME,
        "address":        config.SHOP_FULL_ADDRESS,
        "city":           config.SHOP_CITY,
        "services":       config.SHOP_SERVICES,
        "brands":         config.SHOP_BRANDS,
        "usp":            config.SHOP_USP,
        "competitors":    [c["name"] for c in config.COMPETITORS],
        "phone":          config.SHOP_PHONE,
        "whatsapp":       config.SHOP_WHATSAPP,
        "facebook":       config.SHOP_FACEBOOK,
        "maps":           config.SHOP_GOOGLE_MAPS,
        "owner":          config.SHOP_OWNER_NAME,
        "since":          config.SHOP_SINCE,
        "price_low":      config.SHOP_PRICE_RANGE_LOW,
        "price_high":     config.SHOP_PRICE_RANGE_HIGH,
        "flagship":       config.SHOP_FLAGSHIP_EXAMPLE,
        "force_post_type": getattr(config, "FORCE_FIRST_POST_TYPE", None),
    }

    # ----------------------------------------------------------------
    # Step 1: Load previous best score
    # ----------------------------------------------------------------
    prev_best = load_previous_best(config.RESULTS_FILE)
    print(f"\nPrevious best citation score: {prev_best:.1f}%\n")

    # ----------------------------------------------------------------
    # Step 2: Select queries for this run (rotating subset)
    # ----------------------------------------------------------------
    if config.QUERIES_PER_RUN:
        queries_this_run = select_queries_for_run(
            config.TARGET_QUERIES, config.RESULTS_FILE, config.QUERIES_PER_RUN
        )
        print(f"Queries this run ({len(queries_this_run)} of {len(config.TARGET_QUERIES)}, rotating):")
    else:
        queries_this_run = config.TARGET_QUERIES
        print(f"Queries this run ({len(queries_this_run)}, all):")
    for q in queries_this_run:
        print(f"  - {q}")
    print()

    # ----------------------------------------------------------------
    # Step 3: Run citation checks
    # ----------------------------------------------------------------
    print("Running citation checks...")
    report = run_citation_check(
        queries=queries_this_run,
        domain="",   # no website — aliases handle all detection
        # Substring match: "Friends Mobiles" catches all variations
        # (Friends Mobiles Chakwal, Friends Mobiles Bhoun Chowk, etc.)
        # Case-insensitive by default in _detect_citation
        aliases=["Friends Mobiles", "FriendsMobiles", "Friends Mobile"],
        delay_between_requests=2.0,
    )

    # ----------------------------------------------------------------
    # Step 4: Determine status (keep / discard / baseline)
    # ----------------------------------------------------------------
    is_baseline = prev_best == 0.0
    improved = report.citation_score >= prev_best + config.IMPROVEMENT_THRESHOLD

    if is_baseline:
        status = "baseline"
        description = f"Baseline — {len(queries_this_run)} of {len(config.TARGET_QUERIES)} queries checked across 3 AI tools"
    elif improved:
        status = "keep"
        delta = report.citation_score - prev_best
        description = f"Score improved by {delta:.1f}pp — new content strategy effective"
    else:
        status = "watch"
        description = f"No significant improvement (need +{config.IMPROVEMENT_THRESHOLD}pp)"

    # ----------------------------------------------------------------
    # Step 4: Run strategy agent — analyses results, rewrites seo_strategy.py
    # This is the autoresearch loop: strategy agent modifies the strategy file
    # just like the ML agent modifies train.py
    # ----------------------------------------------------------------
    strategy_summary = run_strategy_update(
        results_file=config.RESULTS_FILE,
        strategy_file="seo_strategy.py",
        posts_dir=config.CONTENT_OUTPUT_DIR,
        all_queries=config.TARGET_QUERIES,
    )

    # Reload strategy after update so content generation uses the new version
    import importlib
    try:
        import seo_strategy as strategy_mod
        importlib.reload(strategy_mod)
    except Exception:
        strategy_mod = None

    # ----------------------------------------------------------------
    # Step 5: Generate blog post using the freshly updated strategy
    # ----------------------------------------------------------------
    new_post_path = None
    if config.POSTS_PER_RUN > 0:
        print("\nSelecting content targets...")

        # Strategy agent may have set PRIORITY_QUERIES — use those first
        strategy_queries = getattr(strategy_mod, "PRIORITY_QUERIES", []) if strategy_mod else []
        uncited = report.uncited_queries()

        if strategy_queries:
            # Intersect priority queries with actually-uncited ones; pad with uncited if needed
            targets = [q for q in strategy_queries if q in uncited]
            if len(targets) < 3:
                targets += select_content_targets(uncited, report.weakly_cited_queries(), 5)
                targets = list(dict.fromkeys(targets))[:5]   # dedupe, keep order
        else:
            targets = select_content_targets(uncited, report.weakly_cited_queries(), 5)

        # Merge strategy overrides into shop_context
        if strategy_mod:
            shop_context["force_post_type"] = (
                None if getattr(strategy_mod, "PREFERRED_POST_TYPE", "auto") == "auto"
                else getattr(strategy_mod, "PREFERRED_POST_TYPE", None)
            )
            shop_context["focus_angle"] = getattr(strategy_mod, "FOCUS_ANGLE", "")

        # Build merged guidelines: base + strategy addon
        strategy_addon = getattr(strategy_mod, "STRATEGY_GUIDELINES_ADDON", "") if strategy_mod else ""
        merged_guidelines = config.CONTENT_GUIDELINES + "\n" + strategy_addon

        if targets:
            print(f"  {len(targets)} targets: {targets[:3]}{'...' if len(targets) > 3 else ''}")
            print("\nGenerating blog post...")
            new_post_path = generate_blog_post(
                target_queries=targets,
                guidelines=merged_guidelines,
                shop_context=shop_context,
                output_dir=config.CONTENT_OUTPUT_DIR,
                results_file=config.RESULTS_FILE,
            )
        else:
            print("  All queries are being cited — no new content needed!")

    # ----------------------------------------------------------------
    # Step 6: Publish to Google Blogger
    # ----------------------------------------------------------------
    blogger_url = None
    if new_post_path and config.BLOGGER_ENABLED and config.BLOGGER_BLOG_ID:
        print("\nPublishing to Blogger...")
        post = blogger_publish_file(
            file_path=new_post_path,
            blog_id=config.BLOGGER_BLOG_ID,
            status=config.BLOGGER_STATUS,
        )
        if post:
            blogger_url = post.url
            print(f"  Published ({post.status}): {blogger_url}")
        else:
            print("  Blogger publish failed (check BLOGGER_* secrets in .env).")
    elif config.BLOGGER_ENABLED and not config.BLOGGER_BLOG_ID:
        print("\nBlogger: BLOGGER_BLOG_ID not set in seo_config.py — skipping publish.")

    # ----------------------------------------------------------------
    # Step 7: Log results to citations.tsv
    # ----------------------------------------------------------------
    strategy_version = getattr(strategy_mod, "STRATEGY_VERSION", "v?") if strategy_mod else "v?"
    result_row = {
        "date": report.run_date,
        "citation_score": f"{report.citation_score:.2f}",
        "gpt_score": f"{report.score_for_tool('gpt'):.2f}",
        "gemini_score": f"{report.score_for_tool('gemini'):.2f}",
        "perplexity_score": f"{report.score_for_tool('perplexity'):.2f}",
        "total_checks": report.total_checks,
        "total_citations": report.total_citations,
        "new_post": blogger_url or new_post_path or "none",
        "status": status,
        "strategy": strategy_version,
        "description": description,
    }
    append_result(config.RESULTS_FILE, result_row)
    print(f"\nResults logged to {config.RESULTS_FILE}")

    # ----------------------------------------------------------------
    # Step 7: Print summary (analogous to autoresearch's metric block)
    # ----------------------------------------------------------------
    print_summary(report, status, blogger_url or new_post_path, prev_best)

    # ----------------------------------------------------------------
    # Step 8a: Log to Google Sheets
    # ----------------------------------------------------------------
    print("\nLogging to Google Sheets...")
    log_run(result_row)
    log_citation_tests(report.results, run_date=report.run_date)
    if new_post_path:
        log_blog_post(
            post_path=new_post_path,
            blogger_url=blogger_url,
            run_date=report.run_date,
        )

    # ----------------------------------------------------------------
    # Step 8b: Generate / update HTML dashboard
    # ----------------------------------------------------------------
    print("\nGenerating dashboard...")
    generate_dashboard(
        results_file=config.RESULTS_FILE,
        posts_dir=config.CONTENT_OUTPUT_DIR,
        output_file="index.html",
    )

    # ----------------------------------------------------------------
    # Step 8c: Send Gmail report
    # ----------------------------------------------------------------
    print("\nSending email report...")
    send_report(run_data=result_row, citation_results=report.results)

    # ----------------------------------------------------------------
    # Step 9: Print detailed uncited queries for debugging
    # ----------------------------------------------------------------
    uncited = report.uncited_queries()
    if uncited:
        print("Queries not cited by any AI tool:")
        for q in uncited:
            print(f"  - {q}")
        print()

    # Report errors (API failures)
    errors = [r for r in report.results if r.error]
    if errors:
        print(f"WARNING: {len(errors)} API call(s) failed:")
        for r in errors:
            print(f"  [{r.ai_tool}] {r.query[:40]}: {r.error}")
        print()

    # Exit with non-zero code if all checks failed (helps CI detect broken runs)
    if all(r.error for r in report.results):
        print("FATAL: All API calls failed. Check your API keys in GitHub Secrets.")
        sys.exit(1)


if __name__ == "__main__":
    main()
