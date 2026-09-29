# 05. Implementation Blueprint & Execution Roadmap

> **Project:** Scrybe — Autonomous Multi-Agent Web Intelligence System  
> **Status:** Step-by-Step Engineering Execution Plan  
> **Target MVP Completion:** 6 Weeks  

---

## 1. Phased Milestone Roadmap

The implementation is broken down into 6 discrete, testable milestones designed for progressive de-risking:

```
[ Week 1 ]  M1: Ingestion Foundation & Compliance Guard (HTTPX + robots.txt + PII + SQLite)
    │
[ Week 2 ]  M2: Tiered Scraping (curl_cffi + Crawl4AI/Playwright + Self-Healing Parser)
    │
[ Week 3 ]  M3: Analyst Agent & Schema Extraction (Pydantic + Confidence Scoring)
    │
[ Week 4 ]  M4: Strategist Agent & Publication Engine (Multi-Source + Markdown/PDF Reports)
    │
[ Week 5 ]  M5: Memory & Reflexion Layer (Rolling Buffer + Reflexion + FAISS Deltas)
    │
[ Week 6 ]  M6: API, Dashboard & Containerized Deployment (FastAPI + Streamlit + Docker)
```

---

## 2. Milestone Details & Verification Criteria

### Milestone 1 (M1): Ingestion Foundation & Compliance Guard
* **Timeline:** Week 1
* **Deliverables:**
  * `scrybe/agents/compliance.py`: Pre-flight `robots.txt` / `ai.txt` checker + post-scrape PII redactor.
  * `scrybe/tools/scraper.py`: Tier 1 `httpx` async fetcher with polite headers and rate limiting.
  * `scrybe/storage/db.py`: SQLite engine with table definitions for `raw_documents`, `compliance_audits`, and `runs`.
  * `config/sources.yaml`: Initial configuration containing 3 public AI developer pricing targets (e.g. OpenAI, Anthropic, Mistral).
* **Acceptance Criteria & Verification:**
  * Running `pytest tests/test_compliance.py` verifies blocked paths raise `RobotsDisallowedException`.
  * Running `pytest tests/test_scraper.py` verifies HTML is successfully fetched and stripped of PII.
  * DB audit table logs timestamps, HTTP status codes, and crawl delays.

### Milestone 2 (M2): Advanced Tiered Scraping & Self-Healing
* **Timeline:** Week 2
* **Deliverables:**
  * Integration of Tier 2 (`curl_cffi`) with Chrome TLS fingerprint impersonation.
  * Integration of Tier 3 (`Crawl4AI` + `playwright-stealth`) for client-rendered Single-Page Applications (SPAs).
  * Implementation of `scrybe/tools/extractor.py` DOM cleaner: Strips scripts, styles, SVG, navigation, and modal clutter while preserving tables.
  * Self-healing selector fallback: When a selector fails, fall back to LLM semantic extraction.
* **Acceptance Criteria & Verification:**
  * System can render and fetch pricing data from a JavaScript-heavy SPA (e.g., dynamic pricing calculator) without getting blocked.
  * Automatic tier escalation: Fails Tier 1 $\rightarrow$ escalates to Tier 2 $\rightarrow$ escalates to Tier 3.

### Milestone 3 (M3): Analyst Agent & Zero-Hallucination Extraction
* **Timeline:** Week 3
* **Deliverables:**
  * `scrybe/agents/analyst.py`: Implements LLM extraction using structured JSON outputs conforming to `PricingTier` and `CompetitorProductRecord`.
  * `scrybe/tools/validator.py`: Grounding validator that checks whether extracted prices exist verbatim in the source markdown.
  * Confidence scoring calculation ($Confidence \ge 0.6$ gate).
* **Acceptance Criteria & Verification:**
  * Evaluated against 10 historical pricing web pages with ground-truth labels.
  * Field extraction accuracy $\ge 95\%$.
  * Zero hallucination: Missing fields must output `null`, never fabricated numbers.

### Milestone 4 (M4): Strategist Agent & Publication Engine
* **Timeline:** Week 4
* **Deliverables:**
  * `scrybe/agents/strategist.py`: Cross-corroborator enforcing the $\ge 2$ independent sources rule for macro trends.
  * Calculates pricing deltas (e.g., "Anthropic input price is 33% lower than OpenAI").
  * Generates sales battlecard talking points and risk warnings.
  * `scrybe/agents/formatter.py`: Compiles results into clean GitHub Markdown and a publication-quality PDF via `ReportLab`.
* **Acceptance Criteria & Verification:**
  * End-to-end execution generates a verified, cited Markdown report (`output/report_YYYYMMDD.md`) and styled PDF (`output/report_YYYYMMDD.pdf`).
  * Every metric contains a valid citation footnote (`[^1]`).

### Milestone 5 (M5): Memory, Reflexion & Delta Tracking
* **Timeline:** Week 5
* **Deliverables:**
  * `scrybe/memory/buffer.py`: Rolling buffer tracking the last 5 pipeline actions.
  * `scrybe/memory/reflection.py`: Reflexion self-critique loop that catches validation errors and repairs payloads.
  * `scrybe/memory/vector_store.py`: FAISS vector index storing dense embeddings of previous extractions to detect semantic deltas.
* **Acceptance Criteria & Verification:**
  * When fed identical website content on consecutive runs, the system flags `DELTA_NONE` and skips downstream synthesis, saving 80% of LLM tokens.
  * Synthetic schema error test triggers Reflexion loop and automatically repairs the JSON payload within 1 retry.

### Milestone 6 (M6): API, Dashboard & Operations
* **Timeline:** Week 6
* **Deliverables:**
  * `scrybe/api/main.py`: FastAPI server with endpoints:
    * `POST /api/v1/run`: Trigger manual pipeline run.
    * `GET /api/v1/reports`: List past generated intelligence briefs.
    * `GET /api/v1/reports/{id}`: Fetch Markdown / PDF report.
    * `GET /api/v1/matrix`: Get latest normalized pricing matrix.
  * `scrybe/dashboard/app.py`: Streamlit dashboard displaying competitor comparison tables, trend graphs, and download buttons.
  * `docker-compose.yml`: Multi-container setup (Scrybe API, Streamlit dashboard, Redis, SQLite volume).
  * Automated cron scheduler via `APScheduler` or Celery.
* **Acceptance Criteria & Verification:**
  * `docker compose up` brings up all services cleanly.
  * User can view pricing comparisons in the Streamlit UI and trigger on-demand competitor scrapes via FastAPI.

---

## 3. Engineering Conventions & Code Quality Standards

* **Language & Runtime:** Python 3.11 or Python 3.12.
* **Typing:** Strict type hints across all function signatures and class definitions (`mypy` compliant).
* **Data Validation:** 100% Pydantic models for internal and external payloads.
* **Testing:** Pytest with minimum 85% branch test coverage.
* **Mocking:** Network calls in tests must use VCR.py or `unittest.mock` fixtures to avoid live web calls during automated test suites.
* **Linting & Formatting:** `ruff check .` and `ruff format .`.
