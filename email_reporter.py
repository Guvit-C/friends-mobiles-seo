"""
email_reporter.py
==================
Generates an HTML run-report and sends it to the configured Gmail address.

Uses a hardcoded HTML template — no AI generation — so every section always
appears consistently regardless of model behaviour.

Environment variables required:
    GMAIL_USER            ahmedgoatkr@gmail.com
    GMAIL_APP_PASSWORD    16-char app password (spaces OK)
"""

import os
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional


# ---------------------------------------------------------------------------
# HTML template builder
# ---------------------------------------------------------------------------

def _build_html(run_data: dict, citation_results: list) -> str:
    date             = run_data.get("date", "")
    citation_score   = run_data.get("citation_score", "0")
    gpt_score        = run_data.get("gpt_score", "0")
    gemini_score     = run_data.get("gemini_score", "0")
    perplexity_score = run_data.get("perplexity_score", "0")
    total_checks     = run_data.get("total_checks", "0")
    total_citations  = run_data.get("total_citations", "0")
    status           = run_data.get("status", "")
    strategy         = run_data.get("strategy", "")
    new_post         = run_data.get("new_post", "none")
    description      = run_data.get("description", "")

    # Status badge colour
    status_colour = {"keep": "#16a34a", "baseline": "#6b7280", "watch": "#f97316",
                     "content_only": "#6b7280"}.get(status, "#6b7280")

    # Score card colour helper
    def score_colour(val):
        try:
            v = float(val)
            if v >= 50: return "#16a34a"
            if v >= 20: return "#f97316"
            return "#dc2626"
        except Exception:
            return "#6b7280"

    # Per-tool breakdown rows
    tool_rows_html = ""
    for tool in ("gpt", "gemini", "perplexity"):
        results = [r for r in citation_results if getattr(r, "ai_tool", "") == tool]
        cited   = sum(1 for r in results if getattr(r, "cited", False))
        total   = len(results)
        pct     = round(cited / total * 100, 1) if total else 0.0
        colour  = score_colour(pct)
        tool_rows_html += f"""
        <tr>
          <td style="padding:10px 14px;border-bottom:1px solid #e5e7eb;font-weight:600">{tool.upper()}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #e5e7eb">{cited}/{total}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #e5e7eb;color:{colour};font-weight:700">{pct}%</td>
        </tr>"""

    # All citation tests rows
    test_rows_html = ""
    if citation_results:
        for r in citation_results:
            tool    = getattr(r, "ai_tool", "").upper()
            query   = getattr(r, "query", "")
            cited   = getattr(r, "cited", False)
            snippet = getattr(r, "citation_snippet", "")[:120]
            error   = getattr(r, "error", "") or ""
            icon    = "✅" if cited else "❌"
            detail  = snippet if snippet else (f"<span style='color:#dc2626'>Error: {error[:80]}</span>" if error else "—")
            test_rows_html += f"""
        <tr>
          <td style="padding:8px 14px;border-bottom:1px solid #f3f4f6;font-size:13px">{tool}</td>
          <td style="padding:8px 14px;border-bottom:1px solid #f3f4f6;font-size:13px">{query}</td>
          <td style="padding:8px 14px;border-bottom:1px solid #f3f4f6;font-size:13px;text-align:center">{icon}</td>
          <td style="padding:8px 14px;border-bottom:1px solid #f3f4f6;font-size:12px;color:#6b7280">{detail}</td>
        </tr>"""
    else:
        test_rows_html = """
        <tr><td colspan="4" style="padding:12px 14px;color:#9ca3af;font-style:italic">
          No citation tests run this cycle (SKIP_CITATION_CHECK=true)
        </td></tr>"""

    # Uncited queries
    cited_any = set(r.query for r in citation_results if getattr(r, "cited", False))
    all_q     = list(dict.fromkeys(r.query for r in citation_results))
    uncited   = [q for q in all_q if q not in cited_any]
    if uncited:
        uncited_html = "".join(
            f'<li style="margin:4px 0;font-size:14px">{q}</li>' for q in uncited
        )
    else:
        uncited_html = '<li style="color:#16a34a;font-size:14px">All queries cited! 🎉</li>'

    # New post link
    if new_post and new_post.startswith("http"):
        post_html = f'<a href="{new_post}" style="color:#0d9488;word-break:break-all">{new_post}</a>'
    else:
        post_html = f'<span style="color:#9ca3af">{new_post or "none"}</span>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Friends Mobiles SEO Report — {date}</title>
</head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:Arial,Helvetica,sans-serif">
<div style="max-width:680px;margin:30px auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08)">

  <!-- Header -->
  <div style="background:#0d9488;padding:28px 32px">
    <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700">
      Friends Mobiles SEO Report — {date}
    </h1>
    <p style="margin:6px 0 0;color:#ccfbf1;font-size:14px">{description}</p>
  </div>

  <div style="padding:28px 32px">

    <!-- Status badge -->
    <div style="margin-bottom:24px">
      <span style="display:inline-block;background:{status_colour};color:#fff;
                   padding:4px 14px;border-radius:20px;font-size:13px;font-weight:600">
        {status.upper()}
      </span>
      &nbsp;
      <span style="color:#6b7280;font-size:13px">Strategy: {strategy}</span>
    </div>

    <!-- Score cards -->
    <div style="display:flex;gap:12px;margin-bottom:28px;flex-wrap:wrap">
      <div style="flex:1;min-width:120px;background:#f0fdf4;border-radius:8px;padding:16px;text-align:center">
        <div style="font-size:28px;font-weight:700;color:{score_colour(citation_score)}">{citation_score}%</div>
        <div style="font-size:12px;color:#6b7280;margin-top:4px">Overall</div>
      </div>
      <div style="flex:1;min-width:120px;background:#f8fafc;border-radius:8px;padding:16px;text-align:center">
        <div style="font-size:28px;font-weight:700;color:{score_colour(gpt_score)}">{gpt_score}%</div>
        <div style="font-size:12px;color:#6b7280;margin-top:4px">GPT</div>
      </div>
      <div style="flex:1;min-width:120px;background:#f8fafc;border-radius:8px;padding:16px;text-align:center">
        <div style="font-size:28px;font-weight:700;color:{score_colour(gemini_score)}">{gemini_score}%</div>
        <div style="font-size:12px;color:#6b7280;margin-top:4px">Gemini</div>
      </div>
      <div style="flex:1;min-width:120px;background:#f8fafc;border-radius:8px;padding:16px;text-align:center">
        <div style="font-size:28px;font-weight:700;color:{score_colour(perplexity_score)}">{perplexity_score}%</div>
        <div style="font-size:12px;color:#6b7280;margin-top:4px">Perplexity</div>
      </div>
    </div>

    <!-- Per-tool breakdown -->
    <h2 style="font-size:16px;margin:0 0 12px;color:#111827">Per-Tool Breakdown</h2>
    <table style="width:100%;border-collapse:collapse;margin-bottom:28px;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden">
      <thead>
        <tr style="background:#f9fafb">
          <th style="padding:10px 14px;text-align:left;font-size:13px;color:#6b7280">Tool</th>
          <th style="padding:10px 14px;text-align:left;font-size:13px;color:#6b7280">Cited / Checked</th>
          <th style="padding:10px 14px;text-align:left;font-size:13px;color:#6b7280">Score</th>
        </tr>
      </thead>
      <tbody>{tool_rows_html}
      </tbody>
    </table>

    <!-- All citation tests -->
    <h2 style="font-size:16px;margin:0 0 12px;color:#111827">All Citation Tests</h2>
    <table style="width:100%;border-collapse:collapse;margin-bottom:28px;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden">
      <thead>
        <tr style="background:#f9fafb">
          <th style="padding:8px 14px;text-align:left;font-size:13px;color:#6b7280">Tool</th>
          <th style="padding:8px 14px;text-align:left;font-size:13px;color:#6b7280">Query</th>
          <th style="padding:8px 14px;text-align:center;font-size:13px;color:#6b7280">Cited</th>
          <th style="padding:8px 14px;text-align:left;font-size:13px;color:#6b7280">Snippet</th>
        </tr>
      </thead>
      <tbody>{test_rows_html}
      </tbody>
    </table>

    <!-- Uncited queries -->
    <h2 style="font-size:16px;margin:0 0 10px;color:#111827">Uncited Queries — Content Targets</h2>
    <ul style="margin:0 0 28px;padding-left:20px">
      {uncited_html}
    </ul>

    <!-- New blog post -->
    <div style="background:#f0fdf4;border-left:4px solid #0d9488;padding:14px 18px;border-radius:4px;margin-bottom:8px">
      <span style="font-size:13px;font-weight:600;color:#374151">New Blog Post:&nbsp;</span>
      {post_html}
    </div>

  </div>

  <!-- Footer -->
  <div style="background:#f9fafb;padding:14px 32px;border-top:1px solid #e5e7eb">
    <p style="margin:0;font-size:12px;color:#9ca3af">
      Generated by Friends Mobiles SEO Autoresearch System &middot; {total_citations}/{total_checks} citations
    </p>
  </div>

</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Gmail SMTP delivery
# ---------------------------------------------------------------------------

def generate_html_report(run_data: dict, citation_results: list) -> str:
    return _build_html(run_data, citation_results)


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

    date    = run_data.get("date", datetime.datetime.utcnow().strftime("%Y-%m-%d"))
    score   = run_data.get("citation_score", "?")
    status  = run_data.get("status", "").upper()
    subject = f"[Friends Mobiles SEO] {date} — {score}% citation score ({status})"

    html_body = _build_html(run_data, citation_results)

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
