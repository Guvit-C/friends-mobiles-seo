"""
medium_publisher.py
====================
Publishes generated blog posts to Medium via the Medium REST API.

Posts are created as DRAFTS by default — review and publish manually
from your Medium dashboard.

API docs: https://github.com/Medium/medium-api-docs
"""

import os
import re
import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional


MEDIUM_API_BASE = "https://api.medium.com/v1"


@dataclass
class MediumPost:
    url: str          # Canonical URL of the draft on Medium
    post_id: str
    title: str
    status: str       # "draft" | "public" | "unlisted"


# ---------------------------------------------------------------------------
# API helpers (stdlib only — no extra dependencies)
# ---------------------------------------------------------------------------

def _api_request(method: str, path: str, token: str, body: dict = None) -> dict:
    url = f"{MEDIUM_API_BASE}{path}"
    data = json.dumps(body).encode("utf-8") if body else None

    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise RuntimeError(f"Medium API {e.code}: {body}") from e


def get_author_id(token: str) -> str:
    """Return the authenticated user's Medium author ID."""
    resp = _api_request("GET", "/me", token)
    return resp["data"]["id"]


# ---------------------------------------------------------------------------
# Markdown front matter parser
# ---------------------------------------------------------------------------

def _parse_front_matter(markdown: str) -> tuple[dict, str]:
    """
    Split YAML front matter from body.
    Returns (meta dict, body string).
    """
    meta = {}
    body = markdown

    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", markdown, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        body = markdown[fm_match.end():]
        for line in fm_text.splitlines():
            if ":" in line:
                key, _, val = line.partition(":")
                meta[key.strip()] = val.strip().strip('"').strip("'")

    return meta, body


def _extract_tags(meta: dict) -> list[str]:
    """Extract up to 5 tags from front matter (Medium limit)."""
    raw = meta.get("tags", "")
    tags = [t.strip() for t in raw.split(",") if t.strip()]
    return tags[:5]


# ---------------------------------------------------------------------------
# Main publish function
# ---------------------------------------------------------------------------

def publish_to_medium(
    markdown_content: str,
    publish_status: str = "draft",
    canonical_url: Optional[str] = None,
    token: Optional[str] = None,
) -> MediumPost:
    """
    Publish a markdown blog post to Medium.

    Args:
        markdown_content: Full markdown including YAML front matter.
        publish_status: "draft" (default), "public", or "unlisted".
        canonical_url: Optional canonical URL (set to your website's post URL
                       so Medium signals it as a cross-post, not original).
        token: Medium Integration Token. Falls back to MEDIUM_API_TOKEN env var.

    Returns:
        MediumPost with the draft URL and ID.
    """
    token = token or os.environ.get("MEDIUM_API_TOKEN")
    if not token:
        raise RuntimeError(
            "MEDIUM_API_TOKEN not set. Add it as a GitHub Secret and env var."
        )

    meta, body = _parse_front_matter(markdown_content)
    title = meta.get("title", "Untitled Post")
    tags = _extract_tags(meta)

    author_id = get_author_id(token)

    payload = {
        "title": title,
        "contentFormat": "markdown",
        "content": markdown_content,   # send full content including front matter stripped version
        "tags": tags,
        "publishStatus": publish_status,
    }

    # Setting canonicalUrl tells Medium this content lives elsewhere first,
    # which avoids duplicate-content penalties for your main website.
    if canonical_url:
        payload["canonicalUrl"] = canonical_url

    resp = _api_request("POST", f"/users/{author_id}/posts", token, payload)
    data = resp["data"]

    return MediumPost(
        url=data.get("url", ""),
        post_id=data.get("id", ""),
        title=data.get("title", title),
        status=data.get("publishStatus", publish_status),
    )


def publish_post_file(
    file_path: str,
    website_url: str,
    publish_status: str = "draft",
) -> Optional[MediumPost]:
    """
    Read a generated markdown post file and publish it to Medium.
    Returns MediumPost or None on failure.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Build canonical URL from website + slug derived from filename
        import os.path
        slug = os.path.basename(file_path).replace(".md", "")
        # Strip leading date prefix (2025-03-18-title → title)
        slug_clean = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", slug)
        canonical = f"{website_url.rstrip('/')}/blog/{slug_clean}"

        post = publish_to_medium(
            markdown_content=content,
            publish_status=publish_status,
            canonical_url=canonical,
        )
        return post

    except Exception as e:
        print(f"  Medium publish failed: {e}")
        return None
