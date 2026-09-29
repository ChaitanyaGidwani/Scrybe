# context.md

> **Purpose:** This file gives any developer or AI assistant the minimum context needed to work on Scrybe productively. Read this first before touching the codebase.

---

## What is Scrybe?

Scrybe is an autonomous, multi-agent web intelligence system. It scrapes public web sources, extracts structured data, validates it, analyzes trends, and generates cited market intelligence reports—with minimal human intervention.

**One-liner:**  
*Scrybe turns raw web data into decision-ready market intelligence, automatically.*

---

## Core Problem

**Surface:** Web data is dynamic, messy, and market reports are manual.  
**Core:** How to autonomously scrape, extract, validate, analyze, and generate actionable market intelligence from unstructured web sources—while ensuring accuracy, compliance, and continuous adaptation.

---

## Why This Project Exists

- Manual market research is slow, expensive, and error-prone.
- Existing scrapers break when websites change.
- LLM-based extraction hallucinates without guardrails.
- Businesses need fresh, cited, decision-ready intelligence—not raw dumps.

---

## Architecture at a Glance

```
Input → Reader Agent → Analyst Agent → Strategist Agent → Formatter Agent → Output
         ↓                ↓                ↓                 ↓
    Data Collection   Trend Analysis   Strategy Planning   Report Generation
```

**Six agents, each with one job:**

| Agent | Job |
|-------|-----|
| **Reader** | Scrape, fetch APIs, filter content, store raw data |
| **Analyst** | Clean, validate, deduplicate, analyze |
| **Strategist** | Derive recommendations and risks |
| **Formatter** | Generate reports, charts, exports |
| **Memory** | Rolling buffer, reflection, vector store |
| **Compliance** | robots.txt, PII filtering, GDPR checks |

Agents communicate sequentially via a shared state object. Each agent can call tools (scrapers, LLM, DB, vector store).

---

## Tech Stack (Locked Decisions)

| Layer | Choice | Why |
|-------|--------|-----|
| Language | **Python 3.11+** | Ecosystem for AI/scraping |
| Agent Framework | **CrewAI (MVP) → LangGraph (later)** | CrewAI for speed; LangGraph when we need conditional edges |
| Scraping | **Crawl4AI** + **Playwright** + **curl_cffi** | Crawl4AI for LLM-ready output; Playwright only for JS-heavy sites; curl_cffi for TLS impersonation |
| Stealth | **playwright-stealth** | Patches `navigator.webdriver` etc. |
| Storage | **SQLite (dev) → PostgreSQL (prod)** | Fast iteration, then scale |
| Vector Store | **FAISS** | Lightweight, local, fast |
| Cache/Queue | **Redis** | Async jobs, dedup, rate limiting |
| API | **FastAPI + Uvicorn** | Async, typed, fast |
| Frontend | **Streamlit (MVP) → Next.js (later)** | Ship fast, polish later |
| Reporting | **ReportLab, python-docx, Plotly** | PDF, DOCX, charts |
| Deployment | **Docker + Docker Compose + Caddy** | Reproducible, simple reverse proxy |
| Scheduling | **APScheduler (MVP) → Celery (scale)** | Simple first |
| Monitoring | **Structured logs → Prometheus + Grafana** | Start simple |

---

## Key Design Decisions & Rationale

### 1. Multi-agent, not monolithic
Each agent has one job, one prompt, one set of tools. This makes debugging, testing, and swapping components trivial.

### 2. Sequential pipeline, not free-for-all
Agents run in order: Reader → Analyst → Strategist → Formatter. No agent negotiation loops in MVP. This keeps latency and cost predictable.

### 3. Hallucination control is non-negotiable
- Every extraction prompt includes: *"Use null if the value is not on the page. Do not guess."*
- Every derived insight carries a confidence score.
- Claims require ≥2 independent sources.
- Low-confidence reports flag for human review.

### 4. Compliance is a first-class agent
The Compliance Agent runs before storage and before publishing. It checks robots.txt, filters PII, and logs audit trails.

### 5. Stealth is tiered, not default
- **Tier 1:** Plain HTTP (`httpx`) — fastest, works for most sites.
- **Tier 2:** `curl_cffi` with Chrome impersonation — bypasses TLS fingerprinting.
- **Tier 3:** Playwright + stealth — only when JS rendering is required.

Never jump to Tier 3 without trying Tier 1 and 2.

### 6. Self-healing selectors
When a selector fails, the agent falls back to LLM-based extraction using the page's semantic structure, then records the fix for next time.

### 7. Memory is layered
- **Short-term:** Rolling buffer of last N actions (for error recovery).
- **Reflection:** Verbal self-critique after failures (Reflexion pattern).
- **Long-term:** FAISS vector store of past extractions (avoids re-scraping unchanged pages).

---

## Project Structure (Planned)

```
scrybe/
├── agents/
│   ├── reader.py
│   ├── analyst.py
│   ├── strategist.py
│   ├── formatter.py
│   ├── memory.py
│   └── compliance.py
├── tools/
│   ├── scraper.py          # Crawl4AI + Playwright + curl_cffi
│   ├── extractor.py        # LLM-based structured extraction
│   ├── validator.py        # Grounding + consistency scoring
│   └── reporter.py         # PDF/DOCX/Markdown generation
├── memory/
│   ├── buffer.py           # Rolling buffer
│   ├── reflection.py       # Reflexion
│   └── vector_store.py     # FAISS
├── storage/
│   ├── db.py               # SQLite/Postgres
│   └── models.py           # Pydantic schemas
├── api/
│   ├── main.py             # FastAPI app
│   └── routes.py
├── dashboard/
│   └── app.py              # Streamlit
├── config/
│   ├── sources.yaml        # Target sites
│   ├── schemas/            # JSON extraction schemas
│   └── settings.py
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── context.md              # ← you are here
```

---

## Data Schema (Core)

Every extracted record must conform to:

```json
{
  "source_url": "string",
  "extracted_at": "ISO8601",
  "product_name": "string",
  "price": "number | null",
  "currency": "string | null",
  "features": ["string"],
  "confidence": "0.0–1.0",
  "raw_text": "string"
}
```

**Rules:**
- Missing values → `null`, never guessed.
- Confidence < 0.6 → flag for review.
- Every record stores its source URL for citation.

---

## Environment Variables

```env
# LLM
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
LLM_MODEL=claude-sonnet-4-20250514

# Scraping
PROXY_URL=...
USER_AGENT=Scrybe/1.0 (+https://scrybe.ai/bot)
MAX_CONCURRENT_SCRAPES=5

# Storage
DATABASE_URL=sqlite:///scrybe.db
FAISS_INDEX_PATH=./data/faiss.index
REDIS_URL=redis://localhost:6379

# API
API_KEY=...
LOG_LEVEL=INFO

# Compliance
RESPECT_ROBOTS_TXT=true
PII_FILTER_ENABLED=true
```

Never commit `.env`. Use `.env.example` as the template.

---

## Coding Conventions

- **Python:** Black + Ruff + isort. Type hints everywhere. Pydantic for all data models.
- **Naming:** `snake_case` for files/functions, `PascalCase` for classes.
- **Agents:** Each agent is a class with a `run(state) -> state` method.
- **Prompts:** Stored in `agents/prompts/` as `.txt` files. Never inline long prompts.
- **Errors:** Use custom exceptions in `exceptions.py`. Never swallow errors silently.
- **Logging:** Structured JSON logs. Include `agent`, `step`, `source_url`, `confidence`.
- **Tests:** Every tool and agent has unit tests. Pipeline has integration tests.

---

## What NOT to Do

- ❌ Don't scrape personal data (names, emails, profiles) without a lawful basis.
- ❌ Don't ignore `robots.txt`.
- ❌ Don't let the LLM guess missing values — always allow `null`.
- ❌ Don't publish a report without citations.
- ❌ Don't jump to Playwright before trying plain HTTP.
- ❌ Don't hardcode source URLs — use `config/sources.yaml`.
- ❌ Don't call LLMs in loops without caching.
- ❌ Don't commit secrets, proxies, or API keys.

---

## Current Status

| Phase | Status |
|-------|--------|
| 1. Scraping Layer | 🟡 Not started |
| 2. Analysis & Report Layer | 🟡 Not started |
| 3. Memory & Context | 🟡 Not started |
| 4. Deployment & Ops | 🟡 Not started |

**MVP Target:** 6 weeks, narrow market, 3–5 sources.

---

## MVP Milestones

- [ ] **M1:** Scrape 3 static sources → SQLite with schema validation.
- [ ] **M2:** Add Playwright for 1 JS-rendered source.
- [ ] **M3:** CrewAI pipeline (Reader + Analyst) producing validated JSON.
- [ ] **M4:** Formatter generates Markdown report with citations.
- [ ] **M5:** Memory layer (buffer + FAISS) working.
- [ ] **M6:** Dockerized, scheduled, deployed with monitoring.

---

## Success Metrics (MVP)

- **Accuracy:** ≥95% of extracted fields match source.
- **Coverage:** ≥90% of target sources scraped successfully.
- **Automation:** ≥80% reduction in manual research time.
- **Compliance:** 0 GDPR violations, 100% robots.txt compliance.
- **User Satisfaction:** ≥4.5/5 from analyst feedback.

---

## Key References

- Crawl4AI: https://crawl4ai.com
- CrewAI: https://crewai.com
- LangGraph: https://langchain-ai.github.io/langgraph/
- Reflexion paper: arXiv:2303.11366
- EDPB Guidelines 03/2026 (web scraping & GDPR)
- Scry (agentic scraper): self-healing, IR-based architecture

---

## Open Questions

1. Which vertical market do we target first? (SaaS pricing? E-commerce? Fintech?)
2. Do we self-host LLMs for cost, or use API providers?
3. How do we handle sources that require login?
4. What's the SLA for report freshness?
5. Do we open-source the core or keep it proprietary?

---

## How to Contribute

1. Read this file end-to-end.
2. Read `requirements.md` for full spec.
3. Pick an open milestone from the list above.
4. Follow conventions in this file.
5. Write tests before opening a PR.
6. Update this file if you make an architectural decision.

---

*This file is the single source of truth for project context. Update it whenever architecture, stack, or scope changes.*