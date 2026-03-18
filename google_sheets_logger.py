"""
google_sheets_logger.py
========================
Logs SEO agent run results to a Google Spreadsheet using a service account.

Three sheets are maintained (created automatically if absent):
  • Runs           — one row per agent run (overall citation scores, status, blog post URL)
  • Citation Tests — one row per (query × AI tool) check with cited/not result
  • Blog Posts     — one row per generated blog post

Authentication: Google Service Account via credentials.json
Sheet ID:       read from GOOGLE_SHEET_ID env var
"""

import os
import json
import datetime
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Sheet layout constants
# ---------------------------------------------------------------------------

RUNS_SHEET        = "Runs"
TESTS_SHEET       = "Citation Tests"
POSTS_SHEET       = "Blog Posts"

RUNS_HEADERS = [
    "Date", "Overall %", "GPT %", "Gemini %", "Perplexity %",
    "Total Checks", "Citations", "Status", "Strategy", "Blog Post URL", "Notes",
]

TESTS_HEADERS = [
    "Date", "AI Tool", "Query", "Cited", "Snippet", "Error",
]

POSTS_HEADERS = [
    "Date", "Title", "Post Type", "Queries Targeted", "File Path", "Blogger URL",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_client():
    """Return an authorised gspread client using the service account file."""
    import gspread

    SCOPES = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    # In CI the full JSON is supplied as an env var instead of a file on disk
    creds_json_str = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
    if creds_json_str:
        creds_dict = json.loads(creds_json_str)
        return gspread.service_account_from_dict(creds_dict, scopes=SCOPES)

    creds_file = os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    return gspread.service_account(filename=creds_file, scopes=SCOPES)


def _ensure_sheet(spreadsheet, title: str, headers: list[str]):
    """
    Return the worksheet named `title`, creating it (with headers) if it
    doesn't exist.  If the sheet exists but has no header row, write one.
    """
    try:
        ws = spreadsheet.worksheet(title)
    except Exception:
        ws = spreadsheet.add_worksheet(title=title, rows=1000, cols=len(headers) + 2)

    # Write headers if the sheet is empty or header row is missing
    existing = ws.row_values(1)
    if not existing or existing[0] != headers[0]:
        ws.insert_row(headers, index=1)

    return ws


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def log_run(
    run_data: dict,
    sheet_id: Optional[str] = None,
) -> bool:
    """
    Append one row to the 'Runs' sheet.

    run_data keys expected:
        date, citation_score, gpt_score, gemini_score, perplexity_score,
        total_checks, total_citations, status, strategy,
        new_post (URL or path), description
    """
    sheet_id = sheet_id or os.environ.get("GOOGLE_SHEET_ID", "")
    if not sheet_id:
        print("  [sheets] GOOGLE_SHEET_ID not set — skipping.")
        return False

    try:
        client = _get_client()
        spreadsheet = client.open_by_key(sheet_id)
        ws = _ensure_sheet(spreadsheet, RUNS_SHEET, RUNS_HEADERS)

        row = [
            run_data.get("date", ""),
            run_data.get("citation_score", ""),
            run_data.get("gpt_score", ""),
            run_data.get("gemini_score", ""),
            run_data.get("perplexity_score", ""),
            run_data.get("total_checks", ""),
            run_data.get("total_citations", ""),
            run_data.get("status", ""),
            run_data.get("strategy", ""),
            run_data.get("new_post", ""),
            run_data.get("description", ""),
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        print(f"  [sheets] Run logged to '{RUNS_SHEET}'")
        return True

    except Exception as e:
        print(f"  [sheets] Failed to log run: {e}")
        return False


def log_citation_tests(
    citation_results: list,
    run_date: Optional[str] = None,
    sheet_id: Optional[str] = None,
) -> bool:
    """
    Append one row per CitationResult to the 'Citation Tests' sheet.
    `citation_results` should be a list of CitationResult dataclass instances.
    """
    sheet_id = sheet_id or os.environ.get("GOOGLE_SHEET_ID", "")
    if not sheet_id:
        return False

    if not citation_results:
        return True

    date = run_date or datetime.datetime.utcnow().strftime("%Y-%m-%d")

    try:
        client = _get_client()
        spreadsheet = client.open_by_key(sheet_id)
        ws = _ensure_sheet(spreadsheet, TESTS_SHEET, TESTS_HEADERS)

        rows = []
        for r in citation_results:
            rows.append([
                date,
                getattr(r, "ai_tool", ""),
                getattr(r, "query", ""),
                "YES" if getattr(r, "cited", False) else "NO",
                getattr(r, "citation_snippet", "")[:200],
                getattr(r, "error", "") or "",
            ])

        if rows:
            ws.append_rows(rows, value_input_option="USER_ENTERED")
            print(f"  [sheets] {len(rows)} citation test(s) logged to '{TESTS_SHEET}'")
        return True

    except Exception as e:
        print(f"  [sheets] Failed to log citation tests: {e}")
        return False


def log_blog_post(
    post_path: Optional[str],
    blogger_url: Optional[str] = None,
    run_date: Optional[str] = None,
    sheet_id: Optional[str] = None,
) -> bool:
    """
    Append one row to the 'Blog Posts' sheet for the newly generated post.
    Reads the post file to extract title, post_type, queries_targeted.
    """
    sheet_id = sheet_id or os.environ.get("GOOGLE_SHEET_ID", "")
    if not sheet_id or not post_path:
        return False

    date = run_date or datetime.datetime.utcnow().strftime("%Y-%m-%d")

    # Extract metadata from the post file's YAML front matter
    title       = ""
    post_type   = ""
    queries     = ""

    import re
    try:
        content = Path(post_path).read_text(encoding="utf-8")
        title_m   = re.search(r"^title:\s*(.+)$",              content, re.MULTILINE)
        type_m    = re.search(r"^post_type:\s*(.+)$",          content, re.MULTILINE)
        queries_m = re.search(r"^queries_targeted:\s*(.+)$",   content, re.MULTILINE)
        if title_m:
            title = title_m.group(1).strip().strip("'\"")
        if type_m:
            post_type = type_m.group(1).strip()
        if queries_m:
            queries = queries_m.group(1).strip()
    except Exception:
        pass

    try:
        client = _get_client()
        spreadsheet = client.open_by_key(sheet_id)
        ws = _ensure_sheet(spreadsheet, POSTS_SHEET, POSTS_HEADERS)

        row = [date, title, post_type, queries, post_path or "", blogger_url or ""]
        ws.append_row(row, value_input_option="USER_ENTERED")
        print(f"  [sheets] Blog post logged to '{POSTS_SHEET}'")
        return True

    except Exception as e:
        print(f"  [sheets] Failed to log blog post: {e}")
        return False


def get_all_runs(sheet_id: Optional[str] = None) -> list[dict]:
    """
    Return all rows from the 'Runs' sheet as a list of dicts.
    Returns [] on any error.
    """
    sheet_id = sheet_id or os.environ.get("GOOGLE_SHEET_ID", "")
    if not sheet_id:
        return []

    try:
        client = _get_client()
        spreadsheet = client.open_by_key(sheet_id)
        ws = spreadsheet.worksheet(RUNS_SHEET)
        return ws.get_all_records()
    except Exception as e:
        print(f"  [sheets] Could not read runs: {e}")
        return []
