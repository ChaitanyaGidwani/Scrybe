# 06. Feasibility Analysis & LLM Unit Economics

> **Project:** Scrybe — Autonomous Multi-Agent Web Intelligence System  
> **Role:** Technical Analyst & Financial Modeler  
> **Status:** Economic Validation for MVP & Scale  

---

## 1. Technical Feasibility Assessment

### 1.1 Ingestion Reliability & Anti-Bot Feasibility
Public B2B pricing and documentation pages exhibit significantly lower anti-bot friction than consumer platforms (e.g., ticket resale, social media, e-commerce sneaker drops).
* **Tier 1 (`httpx`):** Successfully resolves ~70% of static/SSR documentation and pricing pages (e.g., Markdown docs, static Hugo/Next.js pages).
* **Tier 2 (`curl_cffi`):** Bypasses Cloudflare/Fastly basic TLS/JA3 fingerprint checks with 95%+ success on public technical content.
* **Tier 3 (`Crawl4AI` + `playwright-stealth`):** Reserved for the ~5% of sites that require client-side JavaScript hydration or interactive tab clicks.
* **Expected Overall Ingestion Availability:** **> 98.5%**.

### 1.2 Storage & Memory Footprint
* **SQLite Database:** A single run tracking 10 competitors produces ~250 KB of raw cleaned text and structured JSON. 1 year of weekly runs consumes $< 150 \text{ MB}$, fitting comfortably in SQLite.
* **FAISS Vector Store:** Storing 5,000 embeddings (dimension 1536 or 384) requires $< 30 \text{ MB}$ of RAM, operating with sub-millisecond retrieval latency.

---

## 2. LLM Model Tiering Architecture

A common failure mode in agentic AI is using an expensive flagship model (e.g. Claude 3.5 Sonnet or GPT-4o) for all tasks, including high-volume ingestion filtering. Scrybe enforces a **Tiered Hybrid LLM Architecture**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TIERED MODEL STRATEGY                           │
├────────────────────────────────────────────────────────────────────────┤
│ TASK                     │ MODEL CLASS          │ INPUT / OUTPUT CPM   │
├──────────────────────────┼──────────────────────┼──────────────────────┤
│ 1. Entity Extraction     │ Fast / Cheap Tier    │ ~$0.15 / $0.60 per 1M│
│    & Schema Conformance  │ (Gemini 2.0 Flash /  │                      │
│                          │  Claude 3.5 Haiku)   │                      │
├──────────────────────────┼──────────────────────┼──────────────────────┤
│ 2. Grounding Validation  │ Fast / Cheap Tier    │ ~$0.15 / $0.60 per 1M│
│    & Anomaly Detection   │ (GPT-4o-mini /       │                      │
│                          │  Gemini 2.0 Flash)   │                      │
├──────────────────────────┼──────────────────────┼──────────────────────┤
│ 3. Strategist Synthesis, │ Frontier Reasoning   │ ~$3.00 / $15.00      │
│    SWOT & Battlecards    │ (Claude 3.5 Sonnet / │ per 1M tokens        │
│                          │  GPT-4o)             │                      │
└──────────────────────────┴──────────────────────┴──────────────────────┘
```

---

## 3. Token Consumption & Cost Model (Per Intelligence Run)

Assuming a typical intelligence cycle monitoring **5 major competitor platforms** (e.g. OpenAI, Anthropic, Mistral, Groq, Together AI):

### 3.1 Token Consumption Table

| Pipeline Stage | Agent | Input Tokens | Output Tokens | Model Used | Estimated Cost |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Extraction (5 sites)** | Analyst | 75,000 | 5,000 | Gemini 2.0 Flash / Haiku | **$0.015** |
| **Grounding Verification**| Analyst | 25,000 | 2,500 | Gemini 2.0 Flash / Haiku | **$0.005** |
| **Vector Delta Check** | Memory | 10,000 | 0 | text-embedding-3-small | **$0.0002** |
| **Strategic Synthesis** | Strategist | 18,000 | 3,500 | Claude 3.5 Sonnet | **$0.106** |
| **Executive Formatting**| Formatter | 12,000 | 3,000 | Gemini 2.0 Flash / Haiku | **$0.004** |
| **Total Per Pipeline Run**| — | **140,000** | **14,000** | **Hybrid Pipeline** | **~$0.130** |

> **Key Financial Takeaway:** An end-to-end multi-agent intelligence run covering 5 complex competitor pricing ecosystems costs approximately **$0.13 to $0.25** in total model compute!

---

## 4. Customer Unit Economics & ROI

### 4.1 Monthly COGS per Subscribed Customer (Growth Tier)
* Monitoring 10 competitors on a **Daily Delta Check + Weekly Deep Synthesis** schedule:
  * 30 Daily delta checks (cheap hash/embedding check): $30 \times \$0.02 = \$0.60$
  * 4 Weekly Deep Strategic Reports: $4 \times \$0.35 = \$1.40$
  * Shared Residential Proxy Pool allocation: ~$12.00
  * Cloud Server / Redis overhead allocation: ~$4.00
  * **Total Monthly COGS per Customer:** **~$18.00**

### 4.2 Gross Margin Analysis

| Metric | Starter Tier ($249/mo) | Growth Tier ($699/mo) | Enterprise ($1,999/mo) |
| :--- | :---: | :---: | :---: |
| **Monthly Revenue** | $249.00 | $699.00 | $1,999.00 |
| **Monthly COGS** | $12.00 | $18.00 | $65.00 |
| **Gross Profit** | **$237.00** | **$681.00** | **$1,934.00** |
| **Gross Margin (%)** | **95.2%** | **97.4%** | **96.7%** |

### 4.3 Customer ROI Justification
* **The Traditional Cost:** A Senior Product Marketing Manager or Market Research Associate earning $120,000/year spends ~25 hours per month manually tracking competitors, compiling spreadsheets, and updating battlecards.
  * Loaded hourly rate: $80/hr.
  * Monthly labor cost: $25 \times \$80 = \mathbf{\$2,000/month}$.
* **The Scrybe Alternative:**
  * Monthly Subscription: **$699/month**.
  * Analyst time reduced from 25 hours to 2 hours (reviewing verified briefs).
  * **Net Monthly Savings for Customer:** $\mathbf{\$1,140/month}$ + zero blind spots.
  * **Customer ROI:** **~160% in Month 1**, expanding as more competitors are tracked.

---

## 5. Risk Mitigation Matrix

| Potential Risk | Likelihood | Impact | Built-in Mitigation Mechanism |
| :--- | :---: | :---: | :--- |
| **Target Website Redesign** | High | Medium | Tiered scraping falls back to semantic LLM extraction (`self_healing_selector`). |
| **Aggressive IP Rate-Limiting** | Medium | Medium | Polite crawl delays (2.5s jittered), exponential backoff, circuit breaker cooldowns. |
| **Model Hallucination** | Low | High | Pydantic schema validation, strict `null` prompt rule, and verbatim DOM citation check. |
| **Runaway Token Costs** | Low | Medium | FAISS semantic delta check skips LLM synthesis when content has $>0.995$ similarity. |
| **GDPR Inquiries** | Very Low | High | Pre-flight `robots.txt` enforcement + automated regex/NER PII redactor + immutable audit log. |
