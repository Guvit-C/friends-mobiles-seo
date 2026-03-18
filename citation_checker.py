"""
citation_checker.py
====================
Queries GPT, Gemini, and Perplexity for target queries and checks
whether the configured website is cited in their responses.

Analogous to the evaluation harness in prepare.py — this is the
"ground truth metric" module. The agent reads results but never
modifies this file.
"""

import os
import re
import time
import datetime
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CitationResult:
    ai_tool: str          # "gpt" | "gemini" | "perplexity"
    query: str
    response_text: str
    cited: bool
    citation_snippet: str = ""   # The sentence/phrase that contains the citation
    source_urls: list = field(default_factory=list)  # Perplexity returns explicit URLs
    error: Optional[str] = None


@dataclass
class CitationReport:
    run_date: str
    results: list[CitationResult] = field(default_factory=list)

    @property
    def total_checks(self) -> int:
        return len(self.results)

    @property
    def total_citations(self) -> int:
        return sum(1 for r in self.results if r.cited)

    @property
    def citation_score(self) -> float:
        """Overall citation score as a percentage."""
        if not self.results:
            return 0.0
        return (self.total_citations / self.total_checks) * 100

    def results_for_tool(self, tool: str) -> list[CitationResult]:
        return [r for r in self.results if r.ai_tool == tool]

    def score_for_tool(self, tool: str) -> float:
        results = self.results_for_tool(tool)
        if not results:
            return 0.0
        return sum(1 for r in results if r.cited) / len(results) * 100

    def uncited_queries(self) -> list[str]:
        """Return queries that were not cited by ANY of the three tools."""
        cited_by_any = set()
        for r in self.results:
            if r.cited:
                cited_by_any.add(r.query)
        all_queries = set(r.query for r in self.results)
        return list(all_queries - cited_by_any)

    def weakly_cited_queries(self) -> list[str]:
        """Return queries cited by fewer than 2 tools — opportunity targets."""
        from collections import Counter
        counts = Counter(r.query for r in self.results if r.cited)
        all_queries = set(r.query for r in self.results)
        return [q for q in all_queries if counts.get(q, 0) < 2]

    def summary_dict(self) -> dict:
        return {
            "run_date": self.run_date,
            "citation_score": round(self.citation_score, 2),
            "gpt_score": round(self.score_for_tool("gpt"), 2),
            "gemini_score": round(self.score_for_tool("gemini"), 2),
            "perplexity_score": round(self.score_for_tool("perplexity"), 2),
            "total_checks": self.total_checks,
            "total_citations": self.total_citations,
            "uncited_count": len(self.uncited_queries()),
        }


# ---------------------------------------------------------------------------
# Citation detection helpers
# ---------------------------------------------------------------------------

def _detect_citation(text: str, domain: str, aliases: list[str]) -> tuple[bool, str]:
    """
    Check if the domain or any alias appears in text.
    Returns (cited: bool, snippet: str).
    """
    text_lower = text.lower()
    domain_lower = domain.lower()

    # Build all patterns to search for (skip domain if empty)
    patterns = ([domain_lower] if domain_lower else []) + [a.lower() for a in aliases]

    for pattern in patterns:
        idx = text_lower.find(pattern)
        if idx != -1:
            # Extract a snippet of surrounding context (up to 200 chars)
            start = max(0, idx - 60)
            end = min(len(text), idx + len(pattern) + 100)
            snippet = text[start:end].strip()
            return True, snippet

    return False, ""


# ---------------------------------------------------------------------------
# GPT (OpenAI) checker — uses gpt-4o-search-preview for live web search
# ---------------------------------------------------------------------------

def check_openai(query: str, domain: str, aliases: list[str]) -> CitationResult:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

        response = client.chat.completions.create(
            model="gpt-4o-mini-search-preview",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"{query}\n\n"
                        "Please recommend the most helpful websites or sources "
                        "for further reading on this topic."
                    ),
                }
            ],
            max_tokens=1024,
        )

        text = response.choices[0].message.content or ""
        cited, snippet = _detect_citation(text, domain, aliases)

        return CitationResult(
            ai_tool="gpt",
            query=query,
            response_text=text,
            cited=cited,
            citation_snippet=snippet,
        )

    except Exception as e:
        return CitationResult(
            ai_tool="gpt",
            query=query,
            response_text="",
            cited=False,
            error=str(e),
        )


# ---------------------------------------------------------------------------
# Gemini (Google) checker — uses Google Search grounding
# ---------------------------------------------------------------------------

def check_gemini(query: str, domain: str, aliases: list[str]) -> CitationResult:
    try:
        from google import genai
        from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

        client = genai.Client(api_key=os.environ["GOOGLE_AI_API_KEY"])

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=(
                f"{query}\n\n"
                "Please recommend the most helpful websites or sources "
                "for further reading on this topic."
            ),
            config=GenerateContentConfig(
                tools=[Tool(google_search=GoogleSearch())],
                max_output_tokens=1024,
            ),
        )

        # Extract text from response
        text = ""
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text"):
                    text += part.text

        cited, snippet = _detect_citation(text, domain, aliases)

        return CitationResult(
            ai_tool="gemini",
            query=query,
            response_text=text,
            cited=cited,
            citation_snippet=snippet,
        )

    except Exception as e:
        return CitationResult(
            ai_tool="gemini",
            query=query,
            response_text="",
            cited=False,
            error=str(e),
        )


# ---------------------------------------------------------------------------
# Perplexity checker — routed via OpenRouter (web search built-in)
# ---------------------------------------------------------------------------

def check_perplexity(query: str, domain: str, aliases: list[str]) -> CitationResult:
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": domain,
                "X-Title": "SEO Autoresearch Agent",
            },
        )

        response = client.chat.completions.create(
            model="perplexity/sonar",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"{query}\n\n"
                        "Please recommend the most helpful websites or sources "
                        "for further reading on this topic."
                    ),
                }
            ],
            max_tokens=1024,
        )

        text = response.choices[0].message.content or ""

        # Perplexity may return citations in a separate field
        source_urls = []
        if hasattr(response, "citations") and response.citations:
            source_urls = list(response.citations)

        # Check response text AND explicit source URLs
        cited, snippet = _detect_citation(text, domain, aliases)
        if not cited:
            # Also check source URLs list
            domain_lower = domain.lower()
            for url in source_urls:
                if domain_lower in url.lower():
                    cited = True
                    snippet = f"[URL in sources]: {url}"
                    break

        return CitationResult(
            ai_tool="perplexity",
            query=query,
            response_text=text,
            cited=cited,
            citation_snippet=snippet,
            source_urls=source_urls,
        )

    except Exception as e:
        return CitationResult(
            ai_tool="perplexity",
            query=query,
            response_text="",
            cited=False,
            error=str(e),
        )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

CHECKER_MAP = {
    "gpt": check_openai,
    "gemini": check_gemini,
    "perplexity": check_perplexity,
}


def run_citation_check(
    queries: list[str],
    domain: str,
    aliases: list[str],
    tools: list[str] = None,
    delay_between_requests: float = 1.5,
) -> CitationReport:
    """
    Run citation checks for all queries across all AI tools.
    Returns a CitationReport with all results.
    """
    if tools is None:
        tools = ["gpt", "gemini", "perplexity"]

    run_date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    report = CitationReport(run_date=run_date)

    total = len(queries) * len(tools)
    done = 0

    for tool in tools:
        checker = CHECKER_MAP[tool]
        for query in queries:
            done += 1
            print(f"  [{done}/{total}] {tool.upper():12s} | {query[:55]}...")
            result = checker(query, domain, aliases)

            if result.error:
                print(f"    ERROR: {result.error}")
            elif result.cited:
                print(f"    CITED  ✓  snippet: {result.citation_snippet[:80]}")
            else:
                print(f"    not cited")

            report.results.append(result)

            if delay_between_requests > 0:
                time.sleep(delay_between_requests)

    return report
