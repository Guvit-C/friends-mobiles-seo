# SEO / AEO / GEO Autoresearch System — Progress Log

## Goal
Make AI tools (ChatGPT, Gemini, Perplexity) cite **Friends Mobiles** when anyone asks about buying or repairing phones in Chakwal, Pakistan. Competitors Ali Links and KMC already rank on ChatGPT — this system builds entity authority to appear alongside and eventually above them.

---

## Shop Entity (NAP — never change these)
- **Name:** Friends Mobiles
- **Owner:** Talal Maqsood
- **Address:** Ammer Baghwalia Market, Bhoun Chowk Chakwal, Chakwal, Pakistan, 48800
- **WhatsApp:** 03065479656
- **Facebook:** https://www.facebook.com/p/Friends-Mobiles-100063786832336/
- **Established:** 2018 (7+ years)
- **Price range:** PKR 10,000 (used) → Samsung S24 (brand new)
- **Brands:** Samsung, iPhone, Xiaomi, Oppo, Vivo, Tecno, Infinix, Nokia, Realme, OnePlus, Huawei, Honor
- **Services:** Sales (new + used), accessories, screen replacement, battery replacement, charging port repair, water damage repair, trade-in

---

## Architecture — Autoresearch Pattern Applied to SEO

Directly adapted from Andrej Karpathy's autoresearch framework:

| autoresearch (Karpathy) | This system |
|------------------------|-------------|
| `prepare.py` — fixed, never modified | `seo_config.py` — shop facts, base queries |
| `train.py` — agent modifies this | `seo_strategy.py` — strategy agent rewrites this |
| The AI agent | `strategy_agent.py` — GPT-4o analyzes results, rewrites strategy |
| `val_bpb` metric | `citation_score` — % of (query × AI tool) pairs where Friends Mobiles is cited |
| `results.tsv` | `citations.tsv` — full run history |
| `program.md` | `seo_program.md` — human-readable instructions |
| 5-minute budget | ~$0.22 per run budget |
| Loops forever | Loops every 3 days via GitHub Actions |

---

## Files

| File | Role | Modifiable by |
|------|------|---------------|
| `seo_config.py` | Fixed constants: shop NAP, base query list, Blogger config | Human only |
| `seo_strategy.py` | Current strategy: post type, focus angle, priority queries | **GPT-4o strategy agent** (every run) |
| `seo_agent.py` | Main orchestrator — runs the full cycle | Human only |
| `citation_checker.py` | Queries GPT/Gemini/Perplexity, detects citations | Human only |
| `content_generator.py` | Generates blog posts via Claude Sonnet | Human only |
| `strategy_agent.py` | Analyzes citations.tsv, rewrites seo_strategy.py | Human only |
| `blogger_publisher.py` | Publishes posts to Google Blogger via OAuth2 | Human only |
| `blogger_setup.py` | One-time OAuth2 setup script (run locally once) | Human runs once |
| `seo_program.md` | Agent instructions and strategy guide | Human edits |
| `seo_requirements.txt` | Python dependencies | Human only |
| `.github/workflows/seo_autoresearch.yml` | GitHub Actions — runs every 3 days | Human only |
| `.env` | API credentials (never committed) | Human fills in |
| `citations.tsv` | Run history log | Auto-updated each run |
| `posts/` | Generated blog posts (markdown) | Auto-generated |
| `seo_strategy.py.bak` | Backup before each strategy overwrite | Auto-generated |

---

## Models Used

| Task | Model | Via | Cost/run est. |
|------|-------|-----|--------------|
| GPT citation check (5 queries) | `gpt-4o-mini-search-preview` | Direct OpenAI | ~$0.07 |
| Gemini citation check (5 queries) | `gemini-2.0-flash` + Search grounding | Direct Google | ~$0.03 |
| Perplexity citation check (5 queries) | `perplexity/sonar` | OpenRouter | ~$0.04 |
| Blog post generation (1 post) | `anthropic/claude-sonnet-4-5` | OpenRouter | ~$0.06 |
| Strategy analysis (1 call) | `gpt-4o` | Direct OpenAI | ~$0.02 |
| **Total** | | | **~$0.22/run** |

---

## Citation Queries (25 total, 5 per run rotating)

1. Best mobile shop in Chakwal
2. Where to buy phone in Chakwal
3. Mobile repair Chakwal
4. Mobile shops in Chakwal
5. Cheapest mobile shop Chakwal
6. Phone screen replacement Chakwal
7. Mobile dealers Chakwal
8. Where to fix phone in Chakwal
9. Mobile accessories Chakwal
10. Samsung price in Chakwal
11. iPhone price in Chakwal
12. Xiaomi phones Chakwal
13. Ali Links vs KMC vs Friends Mobiles
14. Mobile shop near Tehsil Plaza
15. Original phone check Chakwal
16. Battery replacement Chakwal
17. Mobile warranty service Chakwal
18. Best phone under 50000 Chakwal
19. Oppo phones Chakwal
20. Mobile shop Chakwal location
21. Water damage repair Chakwal
22. Trade-in old phone Chakwal
23. Mobile charging port repair Chakwal
24. Student phone deals Chakwal
25. 5G phones available in Chakwal

---

## Citation Prompt (same for all 3 AI tools)

```
{query}

Please recommend the most helpful websites or sources for further reading on this topic.
```

Detection: checks AI response for "Friends Mobiles", "friends mobiles", "friendsmobiles", "Friends Mobiles Chakwal", "Ammer Baghwalia Market, Bhoun Chowk Chakwal", "Bhoun Chowk", "Ammer Baghwalia".

---

## Blog Post Generation

### How topic is chosen
1. 5 queries checked this run (rotating)
2. `strategy_agent.py` (GPT-4o) rewrites `seo_strategy.py` — sets `PRIORITY_QUERIES`
3. Content generator intersects PRIORITY_QUERIES with uncited queries
4. Falls back to uncited → weakly-cited if no overlap

### Post types (auto-selected by query keywords)
| Type | Trigger | AEO Impact |
|------|---------|-----------|
| `comparison` | "vs", "compare" in queries | Highest — AI tools cite comparisons for recommendation queries |
| `listicle` | Default | High — "Best X in Chakwal" format |
| `service_guide` | repair/fix/battery/screen/port keywords | Medium — captures intent queries |
| `brand_local` | Samsung/iPhone/Xiaomi/5G keywords | Medium — brand+location queries |

### Blog post prompt structure (sent to Claude Sonnet)
1. Objective statement (cite Friends Mobiles for Chakwal queries)
2. Shop entity block (exact NAP, WhatsApp, Facebook, owner, brands, USPs)
3. Target queries block (5 uncited queries)
4. Post format instructions (comparison/listicle/service/brand — whichever selected)
5. AEO/GEO structure rules (opening para → Quick Answer box → H2/H3 → table → 6-question FAQ)
6. Entity density rules ("Friends Mobiles" every 200 words, address 3×, WhatsApp 2×)
7. Writing rules (local Chakwal tone, PKR prices, landmarks)
8. Performance history block (from citations.tsv — which post types got better scores)
9. YAML front matter format

---

## The Autoresearch Loop (every 3 days)

```
Step 1 — Load previous best citation_score from citations.tsv
Step 2 — Rotate 5 queries, run citation checks (5 × 3 tools = 15 API calls)
Step 3 — Determine status: baseline / keep / watch
Step 4 — Strategy agent (GPT-4o) reads citations.tsv + post history
          → rewrites seo_strategy.py with new PRIORITY_QUERIES, PREFERRED_POST_TYPE,
            FOCUS_ANGLE, STRATEGY_GUIDELINES_ADDON, STRATEGY_NOTES
          → seo_strategy.py committed to git (full history of every strategy tried)
Step 5 — Generate 1 blog post using merged guidelines (base + strategy addon)
          → post type chosen by strategy or keyword classifier
          → performance history injected into prompt (Claude adapts style)
Step 6 — Publish to Google Blogger (live or draft per config)
Step 7 — Log to citations.tsv (date, scores, strategy version, post URL)
Step 8 — GitHub Actions commits: citations.tsv + seo_strategy.py + posts/
```

---

## Strategy Agent Logic (GPT-4o)

Reads: `citations.tsv` (last 8 runs), `seo_strategy.py` (current), `posts/` (recent post types)

Decision rules:
- GPT score lagging → prioritise comparison/listicle (GPT cites structured comparisons)
- Gemini score lagging → push local address + landmark content (Google favours geo-specific)
- Perplexity score lagging → shift to service/repair guides (Perplexity favours intent)
- 2+ consecutive "watch" runs → major pivot (different post type + different focus angle)
- Score improving → keep same post type, refine focus angle only

Outputs: complete replacement `seo_strategy.py` with incremented version number

---

## Publishing — Google Blogger

Chosen over Medium because:
- Google crawls its own platform first → Gemini indexes faster
- Free custom domain (friendsmobiles.blogspot.com)
- Direct publish (no draft review delay if desired)

Auth: OAuth2 with refresh token (one-time setup via `blogger_setup.py`)
Format: Markdown → HTML via `markdown` Python package

### One-time Blogger setup
1. Google Cloud Console → enable Blogger API v3
2. Create OAuth 2.0 Client ID (Desktop app type)
3. Fill `CLIENT_ID` and `CLIENT_SECRET` into `blogger_setup.py`
4. Run `python blogger_setup.py` → get refresh token
5. Fill `.env` with all 3 Blogger values
6. Set `BLOGGER_BLOG_ID` in `seo_config.py`

---

## GitHub Secrets Required

| Secret | Used for |
|--------|---------|
| `OPENAI_API_KEY` | GPT-4o-mini citation checks + GPT-4o strategy agent |
| `GOOGLE_AI_API_KEY` | Gemini 2.0 Flash citation checks |
| `OPENROUTER_API_KEY` | Perplexity Sonar + Claude Sonnet (content) |
| `BLOGGER_CLIENT_ID` | Blogger OAuth2 |
| `BLOGGER_CLIENT_SECRET` | Blogger OAuth2 |
| `BLOGGER_REFRESH_TOKEN` | Blogger OAuth2 |

---

## Schedule

GitHub Actions cron: `0 7 */3 * *`
= 07:00 UTC on day 1, 4, 7, 10, 13, 16, 19, 22, 25, 28 of each month
≈ every 3 days

---

## AEO/GEO Strategy Principles Applied

From https://airankchecker.net/blog/how-to-rank-in-ai-search/

1. **Listicle strategy** — "Best mobile shops in Chakwal" distributed across Blogger
2. **Comparison pages** — "Friends Mobiles vs Ali Links vs KMC" (highest impact since competitors already rank)
3. **Entity consistency** — exact same NAP in every post, every run
4. **FAQ sections** — minimum 6 Q&As per post, using exact query phrasing
5. **Quick Answer boxes** — extractable one-sentence answers at top of every post
6. **Phrase-level tracking** — 25 specific local queries monitored per tool
7. **Iterative loop** — track → analyse → generate → distribute → recheck

---

## To-Do / Not Yet Done

- [ ] Fill `BLOGGER_BLOG_ID` and `BLOGGER_BLOG_URL` in `seo_config.py`
- [ ] Run `blogger_setup.py` to get OAuth2 refresh token
- [ ] Add all 6 secrets to GitHub repository
- [ ] Create a Blogger blog at friendsmobiles.blogspot.com (or custom domain)
- [ ] Set `FORCE_FIRST_POST_TYPE = None` in `seo_config.py` after first comparison post is published
- [ ] Consider adding Google Business Profile link to `SHOP_GOOGLE_MAPS` in `seo_config.py` when available
- [ ] Consider posting to LinkedIn articles as third distribution channel (high Perplexity citation rate)
