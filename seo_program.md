# SEO Autoresearch — Agent Program

*Adapted from the autoresearch pattern by @karpathy. Instead of optimizing val_bpb
on a small LLM, we optimize AI citation frequency across GPT, Gemini, and Perplexity.*

---

## What is this?

This is an autonomous SEO research agent that:

1. **Measures** how often your website is cited by AI tools (ChatGPT, Gemini, Perplexity)
   when users ask questions related to your niche.
2. **Analyzes** which queries are not getting citations — these are opportunities.
3. **Generates** new blog posts optimized specifically for AI citation.
4. **Tracks** progress over time in `citations.tsv`.
5. **Repeats** every 24 hours via GitHub Actions.

The key metric is **citation_score**: the percentage of (query × AI tool) pairs
where your website was cited. Higher is better. The goal is to reach 40%+.

---

## Files

| File | Role | Edit? |
|------|------|-------|
| `seo_config.py` | Fixed constants: website URL, target queries, strategy settings | Human edits |
| `seo_program.md` | This file — agent instructions and strategy | Human edits |
| `seo_agent.py` | Main orchestrator — runs each 24h cycle | Do not modify |
| `citation_checker.py` | Citation detection module (ground truth metric) | Do not modify |
| `content_generator.py` | Blog post generation module | Do not modify |
| `citations.tsv` | Results log (tab-separated, not tracked by git) | Auto-updated |
| `posts/` | Generated blog posts (pushed to repo) | Auto-generated |

---

## How to read citations.tsv

```
date    citation_score  gpt_score  gemini_score  perplexity_score  ...  status  description
2025-03-18  12.50       20.00      10.00         7.50              ...  baseline  Baseline run
2025-03-19  18.33       26.67      16.67         12.00             ...  keep      Score improved by 5.8pp
2025-03-20  16.67       23.33      13.33         13.33             ...  watch     No significant improvement
```

- `keep` — citation score improved by ≥2 percentage points (configurable)
- `watch` — score didn't improve; content may need more time to be indexed
- `baseline` — first run, establishes starting point
- `crash` — API failures prevented a full run

---

## Content Strategy

Generated posts are saved to `posts/YYYY-MM-DD-title.md`. To publish them:
1. Copy the markdown to your CMS (WordPress, Ghost, etc.)
2. Review and edit as needed (add images, internal links)
3. Publish and wait for indexing (typically 1–7 days)
4. The next run will check if the new content is being cited

### What makes content AI-citable?

AI tools cite content that:
- **Directly answers the query** in the first paragraph (clear, specific answers)
- **Has structured data**: comparison tables, numbered lists, clear headings
- **Is authoritative**: includes specs, prices, model names, use cases
- **Has FAQ sections**: AI tools love question-answer format content
- **Is comprehensive**: covers the topic thoroughly without padding
- **Has good E-E-A-T signals**: shows expertise, experience, authority, trust

---

## Human Intervention Guide

### If citation_score is stuck (no improvement for 3+ days):
1. Check `citations.tsv` — which AI tool has the lowest score?
2. Read the generated posts in `posts/` — are they high quality?
3. Verify posts are published and indexed on your website
4. Add new, more specific queries to `TARGET_QUERIES` in `seo_config.py`
5. Update `CONTENT_GUIDELINES` to improve content quality

### If citation_score is improving:
- Let the agent run autonomously
- Review generated posts before publishing
- Focus on promoting published content (backlinks, social sharing)

### To add new target queries:
Edit `seo_config.py` → `TARGET_QUERIES`. Think like your audience:
- What questions do budget phone buyers ask?
- What would a student type into Perplexity?
- What would a senior citizen ask ChatGPT about phones?

---

## API Keys Required

Set these as GitHub Actions Secrets (or local environment variables for testing):

| Secret | Used For |
|--------|----------|
| `OPENAI_API_KEY` | GPT-4o with web search |
| `GOOGLE_AI_API_KEY` | Gemini with Google Search grounding |
| `PERPLEXITY_API_KEY` | Perplexity Sonar (web search built-in) |
| `ANTHROPIC_API_KEY` | Claude (content generation) |

---

## Estimated Costs Per Run

| API | Queries | Est. Cost |
|-----|---------|-----------|
| OpenAI GPT-4o Search | 15 queries | ~$0.30 |
| Google Gemini 2.0 Flash | 15 queries | ~$0.05 |
| Perplexity Sonar | 15 queries | ~$0.08 |
| Anthropic Claude (content gen) | 1 post | ~$0.20 |
| **Total per day** | | **~$0.63** |

Monthly cost: ~$19 for daily runs.

---

## The Experiment Loop (what happens every 24 hours)

```
LOOP EVERY 24 HOURS (GitHub Actions):

1. Load seo_config.py — website, queries, strategy
2. Load previous best citation_score from citations.tsv
3. Query GPT, Gemini, Perplexity for all TARGET_QUERIES
4. Detect citations (domain/brand mentioned in responses)
5. Calculate citation_score = (cited / total) × 100
6. If improved ≥ IMPROVEMENT_THRESHOLD → status: keep
   Else → status: watch (new content may not be indexed yet)
7. Select top 5 uncited queries as content targets
8. Generate 1 new blog post with Claude (targeting those queries)
9. Save post to posts/YYYY-MM-DD-title.md
10. Log all results to citations.tsv
11. Git commit and push (GitHub Actions handles this)
12. Print summary block

The agent runs indefinitely. You wake up to new content and citation trends.
```
