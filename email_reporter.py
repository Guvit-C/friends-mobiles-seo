"""
email_reporter.py
==================
Generates an HTML run-report and sends it to the configured Gmail address.

Email body is written by Gemini (gemini-2.0-flash) with GPT-4o-mini as
fallback.  Delivery is via Gmail SMTP using an app-password.

Environment variables required:
    GMAIL_USER            ahmedgoatkr@gmail.com
    GMAIL_APP_PASSWORD    16-char app password (spaces OK)
    GOOGLE_AI_API_KEY     Gemini API key
    OPENAI_API_KEY        OpenAI key (fallback)
"""

import os
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional


# ---------------------------------------------------------------------------
# Data preparation helpers
# ---------------------------------------------------------------------------

def _build_report_context(run_data: dict, citation_results: list) -> dict:
    """
    Flatten everything the email writer needs into a plain dict of strings
    so we can embed it cleanly into the prompt.
    """
    # Per-tool breakdown
    tool_rows = []
    for tool in ("gpt", "gemini", "perplexity"):
        results = [r for r in citation_results if getattr(r, "ai_tool", "") == tool]
        cited   = sum(1 for r in results if getattr(r, "cited", False))
        total   = len(results)
        pct     = round(cited / total * 100, 1) if total else 0.0
        tool_rows.append({"tool": tool.upper(), "cited": cited, "total": total, "pct": pct})

    # Individual test results
    test_rows = []
    for r in citation_results:
        test_rows.append({
            "tool":    getattr(r, "ai_tool", "").upper(),
            "query":   getattr(r, "query", ""),
            "cited":   "✅" if getattr(r, "cited", False) else "❌",
            "snippet": getattr(r, "citation_snippet", "")[:120],
            "error":   getattr(r, "error", "") or "",
        })

    # Uncited queries
    cited_any = set(r.query for r in citation_results if getattr(r, "cited", False))
    all_q     = list(dict.fromkeys(r.query for r in citation_results))
    uncited   = [q for q in all_q if q not in cited_any]

    return {
        "date":              run_data.get("date",             ""),
        "citation_score":    run_data.get("citation_score",   "0"),
        "gpt_score":         run_data.get("gpt_score",        "0"),
        "gemini_score":      run_data.get("gemini_score",     "0"),
        "perplexity_score":  run_data.get("perplexity_score", "0"),
        "total_checks":      run_data.get("total_checks",     "0"),
        "total_citations":   run_data.get("total_citations",  "0"),
        "status":            run_data.get("status",           ""),
        "strategy":          run_data.get("strategy",         ""),
        "new_post":          run_data.get("new_post",         "none"),
        "description":       run_data.get("description",      ""),
        "tool_rows":         tool_rows,
        "test_rows":         test_rows,
        "uncited_queries":   uncited,
    }


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_prompt(ctx: dict) -> str:
    tool_table_md = "\n".join(
        f"| {t['tool']} | {t['cited']}/{t['total']} | {t['pct']}% |"
        for t in ctx["tool_rows"]
    )

    test_table_md = "\n".join(
        f"| {t['tool']} | {t['query']} | {t['cited']} |"
        + (f" {t['snippet']}" if t['snippet'] else "")
        for t in ctx["test_rows"]
    )

    uncited_list = "\n".join(f"• {q}" for q in ctx["uncited_queries"]) or "None — all cited!"

    new_post_line = (
        f'<a href="{ctx["new_post"]}">{ctx["new_post"]}</a>'
        if ctx["new_post"].startswith("http")
        else ctx["new_post"]
    )

    return f"""You are writing a professional HTML email report for an SEO autoresearch system.
The system tracks how often "Friends Mobiles" — a mobile phone shop in Chakwal, Pakistan —
is cited by AI tools (ChatGPT, Gemini, Perplexity) for local search queries.

Write a complete, self-contained HTML email (no external CSS, inline styles only).
Design: clean, modern, mobile-friendly. Colour scheme: white background, dark headings,
a teal/green accent (#0d9488) for positive results, orange (#f97316) for warnings.

--- RUN DATA ---
Date:              {ctx["date"]}
Overall Score:     {ctx["citation_score"]}%
GPT Score:         {ctx["gpt_score"]}%
Gemini Score:      {ctx["gemini_score"]}%
Perplexity Score:  {ctx["perplexity_score"]}%
Total Checks:      {ctx["total_checks"]}
Total Citations:   {ctx["total_citations"]}
Status:            {ctx["status"]}  (baseline / keep / watch)
Strategy:          {ctx["strategy"]}
New Blog Post:     {new_post_line}
Notes:             {ctx["description"]}

--- PER-TOOL BREAKDOWN ---
| Tool | Cited/Checked | Score |
|------|--------------|-------|
{tool_table_md}

--- ALL CITATION TESTS ---
| Tool | Query | Cited |
|------|-------|-------|
{test_table_md}

--- UNCITED QUERIES (need more content targeting these) ---
{uncited_list}

--- EMAIL STRUCTURE ---
1. Subject line hint at top (styled as a pre-header, not shown in body)
2. Header banner: "Friends Mobiles SEO Report — {ctx["date"]}"
3. One-line status badge (green=keep, orange=watch, grey=baseline)
4. Score summary card: Overall | GPT | Gemini | Perplexity — each as a big number
5. Per-tool breakdown table
6. "All Citation Tests" collapsible-style table (just show it in full — no JS)
7. "Uncited Queries — Content Targets" section
8. New blog post line (linked if URL)
9. Footer: "Generated by Friends Mobiles SEO Autoresearch System"

Output ONLY the HTML — no markdown fences, no explanation before or after."""


# ---------------------------------------------------------------------------
# AI-powered HTML generation
# ---------------------------------------------------------------------------

def _write_email_gemini(prompt: str) -> Optional[str]:
    """Use Gemini 2.0 Flash to write the HTML email body."""
    try:
        from google import genai
        from google.genai.types import GenerateContentConfig

        client = genai.Client(api_key=os.environ["GOOGLE_AI_API_KEY"])
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=GenerateContentConfig(max_output_tokens=8192),
        )
        text = ""
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text"):
                    text += part.text
        return text.strip() or None
    except Exception as e:
        print(f"  [email] Gemini failed: {e}")
        return None


def _write_email_gpt(prompt: str) -> Optional[str]:
    """Fallback: use GPT-4o-mini to write the HTML email body."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8192,
        )
        return (response.choices[0].message.content or "").strip() or None
    except Exception as e:
        print(f"  [email] GPT-4o-mini fallback failed: {e}")
        return None


def _strip_md_fences(html: str) -> str:
    """Strip ```html ... ``` wrappers that AI sometimes adds."""
    import re
    html = re.sub(r"^```[a-z]*\n", "", html.strip())
    html = re.sub(r"\n```$", "", html.strip())
    return html.strip()


def generate_html_report(run_data: dict, citation_results: list) -> str:
    """
    Build the HTML email body using Gemini (or GPT-4o-mini fallback).
    Always returns a valid HTML string — falls back to a plain summary
    if both AI calls fail.
    """
    ctx    = _build_report_context(run_data, citation_results)
    prompt = _build_prompt(ctx)

    print("  [email] Asking Gemini to write HTML report...")
    html = _write_email_gemini(prompt)

    if not html:
        print("  [email] Falling back to GPT-4o-mini...")
        html = _write_email_gpt(prompt)

    if html:
        return _strip_md_fences(html)

    # Last-resort fallback: minimal HTML summary
    print("  [email] Both AI calls failed — using plain fallback template.")
    return _fallback_html(ctx)


def _fallback_html(ctx: dict) -> str:
    tool_rows_html = "".join(
        f"<tr><td>{t['tool']}</td><td>{t['cited']}/{t['total']}</td><td>{t['pct']}%</td></tr>"
        for t in ctx["tool_rows"]
    )
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>SEO Report {ctx['date']}</title></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
  <h1 style="color:#0d9488">Friends Mobiles SEO Report — {ctx['date']}</h1>
  <p><strong>Overall Citation Score:</strong> {ctx['citation_score']}%</p>
  <p><strong>Status:</strong> {ctx['status']}</p>
  <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
    <tr style="background:#f1f5f9"><th>Tool</th><th>Cited/Checked</th><th>Score</th></tr>
    {tool_rows_html}
  </table>
  <p><strong>New Post:</strong> {ctx['new_post']}</p>
  <p style="color:#888;font-size:12px">Generated by Friends Mobiles SEO Autoresearch</p>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Gmail SMTP delivery
# ---------------------------------------------------------------------------

def send_report(
    run_data: dict,
    citation_results: list,
    to_email: Optional[str] = None,
) -> bool:
    """
    Generate an HTML email report and send it via Gmail SMTP.

    Returns True if sent successfully, False otherwise.
    """
    to_email   = to_email or os.environ.get("GMAIL_USER", "")
    from_email = os.environ.get("GMAIL_USER", "")
    app_pass   = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")

    if not from_email or not app_pass:
        print("  [email] GMAIL_USER or GMAIL_APP_PASSWORD not set — skipping email.")
        return False

    date       = run_data.get("date", datetime.datetime.utcnow().strftime("%Y-%m-%d"))
    score      = run_data.get("citation_score", "?")
    status     = run_data.get("status", "").upper()
    subject    = f"[Friends Mobiles SEO] {date} — {score}% citation score ({status})"

    html_body  = generate_html_report(run_data, citation_results)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = from_email
    msg["To"]      = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        print(f"  [email] Sending report to {to_email}...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(from_email, app_pass)
            server.sendmail(from_email, to_email, msg.as_string())
        print(f"  [email] Report sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"  [email] Failed to send email: {e}")
        return False
