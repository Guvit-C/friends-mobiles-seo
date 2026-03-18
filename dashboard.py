"""
dashboard.py
=============
Generates a Tailwind CSS-powered static dashboard (index.html).
Tailwind is loaded via CDN — no build step required.

GitHub Pages hosting:
  • Repo Settings → Pages → Source: Deploy from branch → master → / (root)
  • Dashboard lives at https://<user>.github.io/<repo>/

Output: index.html (repo root, committed on every agent run)
Called by seo_agent.py after each run.  Also runnable standalone:
  python dashboard.py
"""

import os
import csv
import re
import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def _load_runs(results_file: str = "citations.tsv") -> list[dict]:
    path = Path(results_file)
    if not path.exists():
        return []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f, delimiter="\t"))
    except Exception:
        return []


def _load_posts(posts_dir: str = "posts") -> list[dict]:
    posts = []
    dir_path = Path(posts_dir)
    if not dir_path.exists():
        return []

    for md_file in sorted(dir_path.glob("*.md"), reverse=True):
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        def _fm(key: str) -> str:
            m = re.search(rf"^{key}:\s*(.+)$", content, re.MULTILINE)
            return m.group(1).strip().strip("'\"") if m else ""

        posts.append({
            "file":    md_file.name,
            "title":   _fm("title") or md_file.stem,
            "type":    _fm("post_type"),
            "queries": _fm("queries_targeted"),
            "date":    _fm("date"),
            "desc":    _fm("description"),
        })
    return posts


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def _score_class(score: float) -> str:
    if score >= 50:
        return "text-emerald-600"
    if score >= 25:
        return "text-orange-500"
    return "text-red-500"


def _score_bg(score: float) -> str:
    if score >= 50:
        return "bg-emerald-500"
    if score >= 25:
        return "bg-orange-400"
    return "bg-red-400"


def _status_pill(status: str) -> str:
    classes = {
        "keep":     "bg-emerald-100 text-emerald-800",
        "watch":    "bg-orange-100 text-orange-800",
        "baseline": "bg-slate-100 text-slate-600",
    }
    cls = classes.get(status.lower(), "bg-slate-100 text-slate-600")
    return f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold {cls}">{status.upper()}</span>'


def _post_type_pill(ptype: str) -> str:
    classes = {
        "comparison":    "bg-violet-100 text-violet-800",
        "listicle":      "bg-emerald-100 text-emerald-800",
        "service_guide": "bg-amber-100 text-amber-800",
        "brand_local":   "bg-sky-100 text-sky-800",
    }
    cls = classes.get(ptype, "bg-slate-100 text-slate-600")
    label = ptype.replace("_", " ").title()
    return f'<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium {cls}">{label}</span>'


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _summary_cards(runs: list[dict], post_count: int) -> str:
    if not runs:
        return ""
    latest    = runs[-1]
    best      = max(float(r.get("citation_score", 0)) for r in runs)
    l_score   = float(latest.get("citation_score", 0))
    l_status  = latest.get("status", "—")
    l_date    = latest.get("date", "—")
    run_count = len(runs)

    def card(label: str, value: str, sub: str, color: str = "text-slate-800") -> str:
        return f"""
        <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-5">
          <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">{label}</p>
          <p class="text-3xl font-bold {color} leading-none mb-2">{value}</p>
          <p class="text-xs text-slate-400">{sub}</p>
        </div>"""

    return f"""
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {card("Latest Score", f"{l_score:.1f}%", f"{_status_pill(l_status)} on {l_date}", _score_class(l_score))}
      {card("Best Ever",    f"{best:.1f}%",    f"across {run_count} run(s)")}
      {card("Total Runs",   str(run_count),    "every 3 days via GitHub Actions")}
      {card("Blog Posts",   str(post_count),   "in posts/ directory")}
    </div>"""


def _trend_bars(runs: list[dict]) -> str:
    recent = runs[-15:]
    if not recent:
        return '<p class="text-sm text-slate-400">No data yet.</p>'

    bars = ""
    for r in recent:
        s   = float(r.get("citation_score", 0))
        h   = max(4, int(s * 1.2))         # scale height (max 120px for 100%)
        cls = _score_bg(s)
        bars += f"""
          <div class="flex flex-col items-center gap-1 flex-1">
            <span class="text-[10px] font-semibold {_score_class(s)}">{s:.0f}%</span>
            <div class="w-full {cls} rounded-t-sm" style="height:{h}px"></div>
            <span class="text-[9px] text-slate-400 rotate-45 origin-left">{r.get('date','')[-5:]}</span>
          </div>"""

    return f"""
    <div class="flex items-end gap-1 h-32 pt-4">
      {bars}
    </div>"""


def _tool_row(label: str, score: float) -> str:
    pct   = min(100, round(score))
    cls   = _score_bg(score)
    tcls  = _score_class(score)
    return f"""
    <div class="flex items-center gap-3">
      <span class="w-24 text-sm font-medium text-slate-600 shrink-0">{label}</span>
      <div class="flex-1 bg-slate-100 rounded-full h-2.5 overflow-hidden">
        <div class="{cls} h-2.5 rounded-full transition-all" style="width:{pct}%"></div>
      </div>
      <span class="w-12 text-right text-sm font-bold {tcls}">{score:.1f}%</span>
    </div>"""


def _runs_table(runs: list[dict]) -> str:
    if not runs:
        return '<p class="text-sm text-slate-400 py-4">No runs logged yet.</p>'

    rows = ""
    for r in reversed(runs[-25:]):
        score = float(r.get("citation_score", 0))
        post  = r.get("new_post", "none")
        if post and post.startswith("http"):
            post_cell = f'<a href="{post}" target="_blank" class="text-teal-600 hover:underline text-xs font-medium">View post ↗</a>'
        elif post and post != "none":
            post_cell = f'<span class="font-mono text-xs text-slate-500">{Path(post).name}</span>'
        else:
            post_cell = '<span class="text-slate-300">—</span>'

        rows += f"""
        <tr class="border-b border-slate-50 hover:bg-slate-50 transition-colors">
          <td class="py-2.5 px-3 text-xs text-slate-500">{r.get('date','')}</td>
          <td class="py-2.5 px-3 font-bold text-sm {_score_class(score)}">{score:.1f}%</td>
          <td class="py-2.5 px-3 text-xs text-slate-500">{float(r.get('gpt_score',0)):.1f}%</td>
          <td class="py-2.5 px-3 text-xs text-slate-500">{float(r.get('gemini_score',0)):.1f}%</td>
          <td class="py-2.5 px-3 text-xs text-slate-500">{float(r.get('perplexity_score',0)):.1f}%</td>
          <td class="py-2.5 px-3">{_status_pill(r.get('status',''))}</td>
          <td class="py-2.5 px-3 text-xs text-slate-400">{r.get('strategy','')}</td>
          <td class="py-2.5 px-3">{post_cell}</td>
        </tr>"""

    return f"""
    <div class="overflow-x-auto">
    <table class="w-full text-left">
      <thead>
        <tr class="border-b border-slate-100">
          <th class="py-2 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Date</th>
          <th class="py-2 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Overall</th>
          <th class="py-2 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">GPT</th>
          <th class="py-2 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Gemini</th>
          <th class="py-2 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Perplexity</th>
          <th class="py-2 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
          <th class="py-2 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Strategy</th>
          <th class="py-2 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Post</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    </div>"""


def _posts_table(posts: list[dict]) -> str:
    if not posts:
        return '<p class="text-sm text-slate-400 py-4">No posts generated yet.</p>'

    rows = ""
    for p in posts[:30]:
        q_preview = (p["queries"][:90] + "…") if len(p["queries"]) > 90 else p["queries"]
        rows += f"""
        <tr class="border-b border-slate-50 hover:bg-slate-50 transition-colors">
          <td class="py-2.5 px-3 text-xs text-slate-500 whitespace-nowrap">{p['date']}</td>
          <td class="py-2.5 px-3 text-sm font-medium text-slate-700 max-w-xs">{p['title']}</td>
          <td class="py-2.5 px-3">{_post_type_pill(p['type'])}</td>
          <td class="py-2.5 px-3 text-xs text-slate-400 max-w-xs">{q_preview}</td>
          <td class="py-2.5 px-3">
            <a href="posts/{p['file']}" class="text-teal-600 hover:underline text-xs font-mono" target="_blank">{p['file']}</a>
          </td>
        </tr>"""

    return f"""
    <div class="overflow-x-auto">
    <table class="w-full text-left">
      <thead>
        <tr class="border-b border-slate-100">
          <th class="py-2 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Date</th>
          <th class="py-2 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Title</th>
          <th class="py-2 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Type</th>
          <th class="py-2 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Queries Targeted</th>
          <th class="py-2 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">File</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    </div>"""


def _section(title: str, content: str) -> str:
    return f"""
    <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-5 mb-6">
      <h2 class="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-4">{title}</h2>
      {content}
    </div>"""


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_dashboard(
    results_file: str = "citations.tsv",
    posts_dir: str    = "posts",
    output_file: str  = "index.html",
) -> str:
    """Build index.html and return its path."""

    runs  = _load_runs(results_file)
    posts = _load_posts(posts_dir)
    now   = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="en" class="h-full">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Friends Mobiles — SEO Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          colors: {{
            teal: {{ 600: '#0d9488', 700: '#0f766e' }}
          }}
        }}
      }}
    }}
  </script>
</head>
<body class="bg-slate-50 min-h-full font-sans text-slate-800 antialiased">

  <!-- Header -->
  <header class="bg-gradient-to-r from-slate-900 to-teal-700 text-white px-6 py-6 shadow-lg">
    <div class="max-w-6xl mx-auto flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
      <div>
        <h1 class="text-xl font-bold tracking-tight">Friends Mobiles — SEO/AEO Dashboard</h1>
        <p class="text-sm text-white/60 mt-0.5">Ammer Baghwalia Market, Bhoun Chowk Chakwal &nbsp;·&nbsp; Owner: Talal Maqsood</p>
      </div>
      <div class="text-right">
        <p class="text-xs text-white/50">Last updated</p>
        <p class="text-sm font-medium text-white/80">{now}</p>
      </div>
    </div>
  </header>

  <main class="max-w-6xl mx-auto px-4 py-8">

    <!-- Summary cards -->
    {_summary_cards(runs, len(posts))}

    <!-- Trend + Per-tool side by side on large screens -->
    <div class="grid lg:grid-cols-2 gap-4 mb-6">
      <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-5">
        <h2 class="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-4">
          Score Trend — Last {min(15, len(runs))} Runs
        </h2>
        {_trend_bars(runs)}
        <p class="text-[10px] text-slate-400 mt-5">Green ≥ 50% &nbsp;·&nbsp; Orange ≥ 25% &nbsp;·&nbsp; Red &lt; 25%</p>
      </div>
      <div class="bg-white rounded-2xl shadow-sm border border-slate-100 p-5">
        <h2 class="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-4">Latest Run — Per AI Tool</h2>
        {"".join([
            _tool_row("ChatGPT",    float((runs[-1] if runs else {}).get("gpt_score", 0))),
            _tool_row("Gemini",     float((runs[-1] if runs else {}).get("gemini_score", 0))),
            _tool_row("Perplexity", float((runs[-1] if runs else {}).get("perplexity_score", 0))),
        ]) if runs else '<p class="text-sm text-slate-400">No data yet.</p>'}
      </div>
    </div>

    <!-- Run history -->
    {_section(f"Run History — Last 25 Runs (newest first)", _runs_table(runs))}

    <!-- Blog posts -->
    {_section(f"Generated Blog Posts ({len(posts)} total)", _posts_table(posts))}

  </main>

  <footer class="text-center text-xs text-slate-400 py-6 border-t border-slate-100">
    Friends Mobiles SEO Autoresearch &nbsp;·&nbsp; Chakwal, Pakistan &nbsp;·&nbsp; Dashboard auto-generated on every run
  </footer>

</body>
</html>"""

    output_path = Path(output_file)
    output_path.write_text(html, encoding="utf-8")
    print(f"  [dashboard] Saved: {output_path.resolve()}")
    return str(output_path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    path = generate_dashboard()
    print(f"Dashboard written to: {path}")
    print("To preview: open index.html in your browser.")
