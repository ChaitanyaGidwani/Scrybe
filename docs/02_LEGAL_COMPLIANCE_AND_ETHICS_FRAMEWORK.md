# 02. Legal, Compliance & Ethics Framework

> **Role & Perspective:** Regulatory & Data Privacy Analyst  
> **Project:** Scrybe — Autonomous Multi-Agent Web Intelligence System  
> **Status:** Mandatory Operational Policy  

---

## 1. Executive Legal Summary

Web scraping occupies a complex legal spectrum between constitutionally protected public information gathering and prohibited data harvesting. Scrybe's competitive advantage relies on **uncompromising legal resilience**.

Unlike unauthorized data scrapers that attempt to bypass login walls or scrape personal social networks, Scrybe is designed exclusively for **public B2B product, pricing, and technical market intelligence**. Compliance is not a post-processing afterthought; it is implemented as a **First-Class Autonomous Compliance Agent** that gates both data ingestion and report distribution.

```
       [ Target URL ]
             │
             ▼
   ┌──────────────────┐
   │ COMPLIANCE AGENT │ ───► Blocked? ───► Abort & Log Audit Event
   │  Pre-Flight Gate │
   └──────────────────┘
             │ (Approved: Public, robots.txt OK, No Paywall)
             ▼
      [ Reader Agent ]
             │
             ▼
   ┌──────────────────┐
   │ COMPLIANCE AGENT │ ───► PII Detected? ───► Scrub / Mask / Discard
   │ Post-Scrape Gate │
   └──────────────────┘
             │ (Anonymized & Cleaned)
             ▼
     [ Storage / DB ]
```

---

## 2. Global Legal Precedents & Jurisdictional Analysis

### 2.1 United States Legal Precedent
* **hiQ Labs v. LinkedIn Corp. (9th Cir. 2022):** The Ninth Circuit affirmed that scraping publicly available web data does not violate the **Computer Fraud and Abuse Act (CFAA)** because accessing public pages does not constitute "without authorization" access.
* **Meta Platforms v. Bright Data (N.D. Cal. 2024):** The court ruled that scraping publicly accessible data without logging in does not breach breach-of-contract claims when the scraper does not agree to terms behind a login wall.
* **Core Takeaway for Scrybe:** As long as Scrybe operates strictly on **publicly accessible pages without logging in, bypassing paywalls, or defeating password gates**, CFAA liability is virtually eliminated.

### 2.2 European Union (GDPR) & EDPB Guidelines 03/2026
In July 2026, the European Data Protection Board adopted **Guidelines 03/2026 on Web Scraping in AI Contexts**:
1. **Public Availability Does Not Equal Exemption:** Personal data published publicly on a website is still subject to the GDPR.
2. **Legitimate Interest (Art. 6(1)(f)):** Consent (Art. 6(1)(a)) is acknowledged as impossible at scale. Scrapers must rely on **Legitimate Interest**, which requires passing a strict three-part test:
   * **Purpose Test:** Legitimate business purpose (competitive market research, transparency in software pricing).
   * **Necessity Test:** The processing must be strictly necessary for the purpose, applying data minimization.
   * **Balancing Test:** The fundamental rights and privacy interests of individuals must not be overridden.
3. **Respect for Technical Signals:** Regulators view `robots.txt`, `ai.txt`, and crawl-delay directives as explicit indicators of reasonable expectations. Respecting them is mandatory.

---

## 3. Scrybe's Non-Negotiable Compliance Guardrails

To ensure zero legal liability, Scrybe enforces seven architectural red lines:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   SCRYBE 7 COMPLIANCE DIRECTIVES                       │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Zero Login / Auth: Never scrape behind an authenticated session.   │
│ 2. Strict robots.txt: If Disallow matches, abort immediately.         │
│ 3. Zero Personal Data: Never store human names, emails, or profiles.  │
│ 4. Rate-Limit Politeness: Minimum 2-second crawl delay per domain.     │
│ 5. Full Attribution: Every fact must store source URL & timestamp.    │
│ 6. Copyright Fair Use: Store facts & metrics, synthesize all text.     │
│ 7. Audit Trail: Immutable logging of every compliance verification.    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Technical Implementation of the Compliance Agent

### 4.1 Pre-Flight Verification Gate (`compliance_preflight`)

Before the `Reader Agent` initiates any network socket or browser session, the `Compliance Agent` executes:

1. **URL Protocol Validation:** Must be `https://` only. No internal network IPs (`127.0.0.1`, `10.0.0.0/8`, `169.254.0.0/16`) to eliminate Server-Side Request Forgery (SSRF).
2. **Robots.txt & ai.txt Parsing:**
   * Fetch `https://{domain}/robots.txt` and `https://{domain}/ai.txt`.
   * Parse using Python’s `urllib.robotparser` (or `reppy`).
   * Check user-agent `Scrybe` and wildcard `*`.
   * If path is disallowed: halt execution, mark record `status: "BLOCKED_BY_ROBOTS"`, and notify orchestrator.
3. **Crawl Delay Extraction:** If `Crawl-delay: X` is defined, enforce $delay \ge X$. Default minimum delay is 2.5 seconds.

### 4.2 Bot Identification & User-Agent Standard

Scrybe does not pretend to be a deceptive headless bot. For transparent web intelligence, Scrybe broadcasts a polite, compliant User-Agent:

```http
User-Agent: Scrybe/1.0 (+https://scrybe.ai/bot; bot@scrybe.ai)
```

> **Tiered Exception Note:** If a target website serves broken JavaScript or blocks legitimate HTTP clients via over-zealous Cloudflare TLS fingerprinting on purely public pricing data, Scrybe switches to Tier 2 (`curl_cffi` browser fingerprint) only to render the public page, while maintaining identical rate politeness and respecting `robots.txt`.

### 4.3 Post-Scrape PII Filtering Pipeline (`compliance_pii_scrub`)

Raw scraped markdown or HTML can incidentally capture customer testimonials, executive names, support emails, or author bylines. Scrybe implements a multi-stage redaction pipeline:

```python
# PII Redaction Pipeline Rule
REDACTION_PATTERNS = {
    "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "PHONE": r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
    "SSN_OR_ID": r"\b\d{3}-\d{2}-\d{4}\b",
    "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
}
```

* **Step 1 (Regex Masking):** All email addresses and telephone numbers are replaced with `[REDACTED_EMAIL]` and `[REDACTED_PHONE]`.
* **Step 2 (Named Entity Recognition):** The text is passed through a lightweight NER filter (spaCy `en_core_web_sm` or regex heuristic) targeting `PERSON` entities. If person entities appear in non-corporate leadership contexts (e.g. user reviews, customer quotes), they are scrubbed.
* **Step 3 (Corporate Entity Whitelist):** Well-known corporate entity names (e.g., "OpenAI", "Anthropic", "Satya Nadella in official press release") are retained only if essential for company context.

### 4.4 Copyright, Transformative Use & Fact Doctrine

* **The Fact-Expression Dichotomy:** Under US and European copyright law, **facts, numbers, and objective metrics cannot be copyrighted** (e.g., *"GPT-4o costs $2.50 per 1M input tokens"* is an uncopyrightable factual datum).
* **Transformative Fair Use:** Scrybe never republishes large verbatim text blocks from competitor websites. It extracts raw numbers and categorical features into a structured JSON schema, and the **Strategist Agent** writes 100% original, transformative analytical commentary.
* **Exact Citations:** Every synthesized insight includes an explicit citation footnote (`[^1]: Anthropic Pricing, Accessed 2026-09-29, https://...`), upholding scholarly and journalistic fair-use standards.

---

## 5. Compliance Audit Trail Schema

Every run of Scrybe logs an auditable compliance verification event to SQLite/PostgreSQL:

```json
{
  "audit_id": "audit_88f910ab",
  "timestamp": "2026-09-29T10:15:30Z",
  "source_url": "https://openai.com/api/pricing/",
  "robots_checked": true,
  "robots_allowed": true,
  "crawl_delay_applied_seconds": 2.5,
  "pii_scrubbed_count": 0,
  "login_bypass_attempted": false,
  "compliance_status": "APPROVED",
  "compliance_officer_agent": "ScrybeComplianceGuard/v1.0"
}
```

If an external audit or inquiry ever occurs, Scrybe can prove with cryptographic certainty that all harvested data was public, complied with `robots.txt`, was stripped of personal data, and adhered to polite crawl limits.
