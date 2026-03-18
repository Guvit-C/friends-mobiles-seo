"""
blogger_publisher.py
=====================
Publishes generated blog posts to Google Blogger via the Blogger API v3.

Auth flow: OAuth2 with a refresh token (one-time setup via blogger_setup.py).
The refresh token is stored as a GitHub Secret and never expires unless revoked.

Blogger is chosen over Medium because Google crawls its own platform first,
which means Gemini indexes these posts faster than any other hosting option.

API docs: https://developers.google.com/blogger/docs/3.0/posts/insert
"""

import os
import re
import json
import urllib.request
import urllib.parse
import urllib.error
from dataclasses import dataclass
from typing import Optional


BLOGGER_API_BASE  = "https://www.googleapis.com/blogger/v3"
GOOGLE_TOKEN_URL  = "https://oauth2.googleapis.com/token"


@dataclass
class BloggerPost:
    url: str
    post_id: str
    title: str
    status: str   # "LIVE" | "DRAFT"


# ---------------------------------------------------------------------------
# OAuth2 — exchange refresh token for a short-lived access token
# ---------------------------------------------------------------------------

def _get_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    data = urllib.parse.urlencode({
        "client_id":     client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type":    "refresh_token",
    }).encode()

    req = urllib.request.Request(GOOGLE_TOKEN_URL, data=data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["access_token"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Token refresh failed {e.code}: {e.read().decode()}") from e


# ---------------------------------------------------------------------------
# Markdown → HTML (Blogger needs HTML content)
# ---------------------------------------------------------------------------

def _md_to_html(markdown: str) -> str:
    """
    Convert markdown to basic HTML for Blogger.
    Uses the `markdown` package if available, falls back to simple regex.
    """
    try:
        import markdown as md_lib
        html = md_lib.markdown(
            markdown,
            extensions=["tables", "fenced_code", "nl2br"],
        )
        # Blogger applies no default CSS to tables — inject inline styles so
        # cells have visible borders and don't collapse into each other.
        html = html.replace(
            "<table>",
            '<table style="border-collapse:collapse;width:100%;margin:16px 0">'
        )
        html = html.replace(
            "<th>",
            '<th style="border:1px solid #ddd;padding:8px 12px;background:#f5f5f5;text-align:left">'
        )
        html = html.replace(
            "<td>",
            '<td style="border:1px solid #ddd;padding:8px 12px">'
        )
        return html
    except ImportError:
        # Fallback: basic regex conversion
        html = markdown
        # Strip YAML front matter
        html = re.sub(r"^---\n.*?\n---\n", "", html, flags=re.DOTALL)
        # Headers
        html = re.sub(r"^#### (.+)$", r"<h4>\1</h4>", html, flags=re.MULTILINE)
        html = re.sub(r"^### (.+)$",  r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$",   r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$",    r"<h1>\1</h1>", html, flags=re.MULTILINE)
        # Bold / italic
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*",     r"<em>\1</em>", html)
        # Blockquotes
        html = re.sub(r"^> (.+)$", r"<blockquote>\1</blockquote>", html, flags=re.MULTILINE)
        # Unordered lists (basic)
        html = re.sub(r"^[-*] (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
        html = re.sub(r"(<li>.*</li>\n?)+", r"<ul>\g<0></ul>", html, flags=re.DOTALL)
        # Paragraphs
        html = re.sub(r"\n\n+", "</p><p>", html)
        html = f"<p>{html}</p>"
        return html


# ---------------------------------------------------------------------------
# Front matter parser
# ---------------------------------------------------------------------------

def _parse_front_matter(markdown: str) -> tuple[dict, str]:
    meta = {}
    body = markdown
    fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", markdown, re.DOTALL)
    if fm:
        body = markdown[fm.end():]
        for line in fm.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, body


def _extract_labels(meta: dict) -> list[str]:
    """Extract up to 20 labels/tags from front matter (Blogger limit)."""
    raw = meta.get("tags", "")
    return [t.strip() for t in raw.split(",") if t.strip()][:20]


# ---------------------------------------------------------------------------
# Blogger API call
# ---------------------------------------------------------------------------

def _api_post(blog_id: str, payload: dict, access_token: str, is_draft: bool) -> dict:
    url = f"{BLOGGER_API_BASE}/blogs/{blog_id}/posts/"
    if is_draft:
        url += "?isDraft=true"

    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization",  f"Bearer {access_token}")
    req.add_header("Content-Type",   "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Blogger API {e.code}: {e.read().decode()}") from e


# ---------------------------------------------------------------------------
# Main publish function
# ---------------------------------------------------------------------------

def publish_to_blogger(
    markdown_content: str,
    blog_id: str,
    status: str = "live",
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    refresh_token: Optional[str] = None,
) -> BloggerPost:
    """
    Publish a markdown post to Google Blogger.

    Args:
        markdown_content: Full post markdown including YAML front matter.
        blog_id: Blogger blog ID (from dashboard).
        status: "live" or "draft".
        client_id/client_secret/refresh_token: OAuth2 credentials.
            Fall back to env vars BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET,
            BLOGGER_REFRESH_TOKEN if not provided.

    Returns:
        BloggerPost with URL and ID.
    """
    client_id     = client_id     or os.environ["BLOGGER_CLIENT_ID"]
    client_secret = client_secret or os.environ["BLOGGER_CLIENT_SECRET"]
    refresh_token = refresh_token or os.environ["BLOGGER_REFRESH_TOKEN"]

    access_token = _get_access_token(client_id, client_secret, refresh_token)

    meta, body_md = _parse_front_matter(markdown_content)
    title  = meta.get("title", "Friends Mobiles Chakwal")
    labels = _extract_labels(meta)

    body_html = _md_to_html(body_md)

    payload = {
        "kind":    "blogger#post",
        "title":   title,
        "content": body_html,
        "labels":  labels,
    }

    is_draft = status.lower() == "draft"
    result   = _api_post(blog_id, payload, access_token, is_draft)

    return BloggerPost(
        url     = result.get("url", ""),
        post_id = result.get("id", ""),
        title   = result.get("title", title),
        status  = result.get("status", status.upper()),
    )


# ---------------------------------------------------------------------------
# File-based wrapper (called from seo_agent.py)
# ---------------------------------------------------------------------------

def publish_post_file(
    file_path: str,
    blog_id: str,
    status: str = "live",
) -> Optional[BloggerPost]:
    """Read a generated markdown file and publish it to Blogger."""
    try:
        import pathlib
        content = pathlib.Path(file_path).read_text(encoding="utf-8")
        post = publish_to_blogger(
            markdown_content=content,
            blog_id=blog_id,
            status=status,
        )
        return post
    except Exception as e:
        print(f"  Blogger publish failed: {e}")
        return None
