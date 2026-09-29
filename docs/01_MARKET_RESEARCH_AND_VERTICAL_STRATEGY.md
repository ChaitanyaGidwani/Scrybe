# 01. Market Research & Vertical Strategy

> **Role & Perspective:** Market Research Lead & Competitive Intelligence Analyst  
> **Project:** Scrybe — Autonomous Multi-Agent Web Intelligence System  
> **Status:** Approved Baseline Strategy for MVP  

---

## 1. Executive Summary

Competitive intelligence (CI) and market monitoring are undergoing a seismic transformation. Today, organizations spend hundreds of hours each quarter manually tracking competitor websites, pricing pages, documentation changes, and product announcements. The alternative—legacy enterprise CI platforms like Klue and Crayon—costs between **$20,000 and $50,000+ per year**, requiring dedicated internal analysts just to triage incoming data.

Meanwhile, entry-level website monitors (e.g., Visualping, Browse AI) trigger **catastrophic alert fatigue**: they fire raw HTML/CSS diff notifications when a banner color changes, without understanding whether a meaningful business event occurred. Consequently, **up to 40% of teams abandon CI tools within their first 12 months**.

**Scrybe solves this fundamental market mismatch.**  
Scrybe is not a raw diff monitor, nor a high-maintenance enterprise dashboard. Scrybe is an **autonomous, multi-agent market synthesis engine**. It continuously ingests public web signals, strips noise, cross-corroborates claims across independent sources, and synthesizes executive-ready, fully cited strategic briefs (pricing shifts, tier modifications, feature launches, positioning pivots).

```
   Raw HTML / RSS / Diffs             Scrybe Agentic Pipeline              Decision-Ready Output
 [ Competitor Pricing Pages ]  ───►  [ Reader & Compliance ]  ───►  [ Executive Briefs (PDF/MD) ]
 [ Documentation Updates    ]  ───►  [ Analyst Extraction   ]  ───►  [ Competitor Pricing Matrix ]
 [ Product Announcements    ]  ───►  [ Strategist Synthesis ]  ───►  [ Slack/Email Strategic Alerts]
```

---

## 2. Market Sizing & Industry Dynamics

### 2.1 TAM, SAM, and SOM Analysis

| Metric | Valuation | Scope & Definition |
| :--- | :--- | :--- |
| **TAM (Total Addressable Market)** | **$4.10 Billion** (by 2034) | Global Competitive Intelligence Tools & Automated Market Research Software Market (CAGR ~18.5%). |
| **SAM (Serviceable Addressable Market)** | **$850 Million** | B2B SaaS, Cloud Infrastructure, and AI Developer Platforms subscribing to automated pricing, packaging, and competitive tracking solutions. |
| **SOM (Serviceable Obtainable Market)** | **$24 Million** | Early-to-growth stage AI companies, developer tool startups, and mid-market SaaS providers seeking affordable ($300–$1,200/mo) autonomous intelligence. |

### 2.2 Market Macro Trends Driving Scrybe

1. **Hyper-Compressed Product Cycles:** Generative AI and open-source models have shortened competitive reaction windows from months to days. AI model providers change per-million-token prices, context window limits, and rate tiers bi-weekly.
2. **The "Alert Fatigue" Crisis:** CI managers receive 200+ raw change notifications a week. 92% of these notifications are non-actionable (styling adjustments, cookie banner changes, minor typography edits).
3. **The Rise of Autonomous AI Workflows:** Decision-makers no longer want another dashboard to log into; they demand finished, cited artifacts delivered straight to their inbox, Slack, or knowledge base.

---

## 3. Vertical Market Evaluation Matrix

To ensure Scrybe's MVP achieves immediate traction and technical feasibility, we evaluated five candidate verticals across five critical criteria:

1. **Data Accessibility:** Can we collect high-signal data from public, non-authenticated web pages without paywalls or legal grey zones?
2. **Signal Volatility:** Does pricing, packaging, or feature availability change frequently enough to warrant an ongoing subscription?
3. **Willingness to Pay (WTP):** Does missing a competitor shift cause direct revenue or customer loss?
4. **Anti-Bot & Legal Risk:** Are target websites protected by aggressive anti-bot walls (Cloudflare Turnstile, DataDome) or restrictive Terms of Service?
5. **Downstream Actionability:** Can the extracted data be synthesized into concrete pricing and feature matrices?

### 3.1 Scoring Matrix (Scale 1–5, 5 being best)

| Vertical Market | Data Accessibility | Signal Volatility | Willingness to Pay | Low Anti-Bot/Legal Risk | Downstream Value | Total Score (/25) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **B2B AI Developer Tooling & APIs** | **5** | **5** | **5** | **4** | **5** | **24 (Selected Beachhead)** |
| **General B2B SaaS (CRM, HR, MarTech)** | 4 | 3 | 4 | 4 | 4 | 19 |
| **E-Commerce Retail Pricing** | 3 | 5 | 3 | 1 (Heavy Anti-Bot) | 3 | 15 |
| **Fintech & Neo-Banking Rates** | 3 | 3 | 4 | 2 (Heavy Regulation) | 4 | 16 |
| **Healthcare / Biotech Solutions** | 2 | 2 | 5 | 3 | 3 | 15 |

---

## 4. Beachhead Selection: B2B AI Developer Tooling & API Platforms

### 4.1 Why This Beachhead Wins
1. **100% Public, Transparent Pricing:** AI model providers (OpenAI, Anthropic, Mistral, Together AI, Groq, Cohere, DeepSeek) and developer infrastructure tools (Pinecone, Supabase, Neon, LangChain, Weaviate) publish detailed, quantitative pricing tables (per 1M input/output tokens, per vector dimension hour, monthly tier limits) on public, non-authenticated pages.
2. **Aggressive Pricing & Feature Wars:** Prices drop or tiers shift every few weeks. A 20% price cut by a competitor directly impacts sales conversations and developer signups.
3. **Zero Legal Ambiguity:** The data is public technical documentation and pricing designed specifically for developer consumption, strictly avoiding personal data (GDPR compliant).
4. **High Value Density:** An AI platform’s Product Marketing Manager (PMM) or Head of Product will readily pay **$300–$1,000/month** to avoid manually compiling pricing comparison spreadsheets every Monday morning.

### 4.2 Beachhead Target Competitors for Scrybe MVP

```
Primary Ingestion Targets (M1-M3):
├── LLM & Inference Providers:
│   ├── OpenAI (Pricing, Models, API Docs, Changelog)
│   ├── Anthropic (Pricing, Claude Models, Release Notes)
│   ├── Mistral AI (API Pricing, Model Capabilities)
│   ├── Groq (Inference Pricing, Token Speeds, Limits)
│   └── Together AI (Serverless & Dedicated Endpoints)
└── AI Infrastructure & Vector Databases:
    ├── Pinecone (Serverless Vector Storage Pricing)
    └── Supabase (Compute Add-ons, Storage, Tier Matrix)
```

---

## 5. Ideal Customer Profile (ICP) & Buyer Personas

### 5.1 Persona 1: The Product Marketing Manager (PMM) — "The Primary User"
* **Title:** Director / Senior Product Marketing Manager (AI/Developer Platforms)
* **Goal:** Maintain competitive battlecards, sales enablement sheets, and positioning decks.
* **Pain Point:** Spends 6–10 hours every week manually opening 15 competitor pricing and docs pages, taking screenshots, and updating Confluence/Google Slides.
* **Scrybe Value:** Receives an automated weekly "Competitive Movement Brief" with an exact diff of competitor tiers, new feature availability, and suggested battlecard talk tracks.

### 5.2 Persona 2: The Founder / VP of Product — "The Economic Buyer"
* **Title:** Co-Founder, Chief Product Officer, VP of Strategy
* **Goal:** Protect gross margins, optimize pricing strategies, and identify feature gaps before roadmap planning.
* **Pain Point:** Blindsided when a competitor launches a cheaper tier or introduces a feature that neutralizes their main value proposition.
* **Scrybe Value:** Clear executive summaries with multi-source verified strategic recommendations and quantifiable price-per-unit comparisons.

---

## 6. Competitive Landscape & Scrybe Moat

| Dimension | Legacy CI Suites (Klue, Crayon) | Change Trackers (Visualping, Browse AI) | Manual Research (Interns / Agency) | **Scrybe (Our Agentic System)** |
| :--- | :--- | :--- | :--- | :--- |
| **Annual Cost** | $20,000 – $50,000+ | $300 – $2,000 | $40,000 – $100,000 | **$1,200 – $6,000** |
| **Output Type** | Dashboard + Manual curation | Raw HTML / Pixel diffs | Ad-hoc slide decks | **Decision-Ready Executive Briefs** |
| **Alert Fatigue** | Medium | **Extremely High** | Low (too slow) | **Zero (Synthesized Signals Only)** |
| **Source Grounding** | Variable | None | High (slow) | **Strict Multi-Source (≥2 sources)** |
| **Hallucination Control**| N/A (Mostly human) | N/A | Human error | **Deterministic Schema + Confidence Score** |
| **Setup Time** | 4–8 weeks | 10 minutes | Ongoing | **5 minutes (config/sources.yaml)** |

### 6.1 Scrybe’s Unfair Advantages (The Moat)
1. **Deterministic Verification:** Every extracted claim must trace back to a raw DOM snippet and carry a confidence score (>0.85). If confidence is below 0.6, the system flags the record for human review rather than publishing hallucinations.
2. **Synthesized Strategic Delta:** Rather than alerting *"Text changed on row 4"*, Scrybe reports: *"Anthropic reduced Claude 3.5 Sonnet prompt caching read prices by 50%, making them 25% cheaper than OpenAI GPT-4o for document analysis workloads. Strategic Recommendation: Re-evaluate our input token margins."*
3. **Tiered Stealth & Self-Healing Scraper:** Scrybe does not rely on fragile CSS selectors. It utilizes semantic HTML distillation via Crawl4AI and LLM fallback parsing.

---

## 7. Monetization & Business Model

### 7.1 Packaging Tiers (Post-MVP)

* **Starter ($249/month):**
  * Up to 5 competitor domains monitored weekly.
  * Markdown & PDF Executive Intelligence Reports.
  * Slack & Email notification digests.
* **Growth ($699/month):**
  * Up to 20 competitor domains monitored daily/event-driven.
  * Custom schema extraction (pricing, feature matrices, SLA limits).
  * Direct API access & CRM/Notion export connectors.
* **Enterprise ($1,999/month):**
  * Unlimited domains, bespoke report styling, custom compliance rules, dedicated residential proxy pool, multi-seat team dashboard.

---

## 8. Analyst Recommendations for MVP Implementation

1. **Focus Strictly on Public Web Endpoints:** Avoid login walls or authenticated portals entirely for MVP. This guarantees speed to market, zero credential liabilities, and 100% compliance with EU GDPR and US legal precedents.
2. **Implement Multi-Source Rule Immediately:** The Strategist Agent must not make industry-wide assertions without corroborating data from at least 2 distinct URLs (e.g., official pricing page + documentation or changelog).
3. **Deliver Finished Artifacts, Not Raw Data:** The output must be delivered in clean GitHub Markdown, Executive PDF (ReportLab), and structured JSON. PMMs want copy-pasteable battlecard snippets.
4. **Instrument Metrics from Day 1:** Measure field extraction accuracy (target ≥95%) and automated reduction of research time (target ≥80%).
