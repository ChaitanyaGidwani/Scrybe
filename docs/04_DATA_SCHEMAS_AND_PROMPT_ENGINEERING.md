# 04. Data Schemas & Prompt Engineering

> **Project:** Scrybe — Autonomous Multi-Agent Web Intelligence System  
> **Status:** Production Schemas & Prompt Library  
> **Version:** 1.0.0  

---

## 1. Pydantic Core Data Schemas

Scrybe enforces strict typed data boundaries at every agent handoff. All schemas inherit from `pydantic.BaseModel` with strict validation rules.

### 1.1 Source Ingestion Configuration (`config/sources.yaml`)

```python
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from enum import Enum

class ScrapeTier(str, Enum):
    TIER1_HTTPX = "httpx"
    TIER2_CURL_CFFI = "curl_cffi"
    TIER3_PLAYWRIGHT = "playwright"

class SourceTargetConfig(BaseModel):
    id: str = Field(description="Unique identifier, e.g., 'anthropic_pricing'")
    company_name: str
    target_url: HttpUrl
    category: str = Field(default="LLM_API", description="Sub-vertical category")
    preferred_tier: ScrapeTier = Field(default=ScrapeTier.TIER1_HTTPX)
    selector_hints: Optional[List[str]] = Field(default=None, description="Optional CSS selector hints")
    enabled: bool = True
```

### 1.2 Raw Scraped Document Schema

```python
from datetime import datetime

class RawScrapedDocument(BaseModel):
    url: str
    domain: str
    status_code: int
    content_markdown: str
    content_hash: str = Field(description="SHA-256 hash of stripped content for cache checking")
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    scrape_tier_used: ScrapeTier
    pii_redacted: bool = True
    robots_compliant: bool = True
```

### 1.3 Extracted Structured Entity Schema

```python
class PricingTier(BaseModel):
    model_or_tier_name: str
    input_price_per_m_tokens: Optional[float] = Field(default=None, description="USD per 1M input tokens. Null if not listed.")
    output_price_per_m_tokens: Optional[float] = Field(default=None, description="USD per 1M output tokens. Null if not listed.")
    cache_read_price_per_m_tokens: Optional[float] = Field(default=None, description="USD per 1M cached tokens if applicable.")
    context_window_tokens: Optional[int] = Field(default=None, description="Max context tokens, e.g. 128000 or 200000.")
    fixed_monthly_price: Optional[float] = Field(default=None, description="Fixed subscription price if flat rate.")
    currency: Optional[str] = Field(default="USD")
    notable_features: List[str] = Field(default_factory=list)

class CompetitorProductRecord(BaseModel):
    company_name: str
    product_name: str
    source_url: str
    pricing_tiers: List[PricingTier] = Field(default_factory=list)
    enterprise_terms_mentioned: bool = Field(default=False)
    rate_limits_summary: Optional[str] = Field(default=None)
    extraction_confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0 to 1.0")
    citation_text: str = Field(description="Exact snippet from source confirming extraction")
```

### 1.4 Strategic Trend & Delta Schema

```python
class DeltaType(str, Enum):
    PRICE_DECREASE = "PRICE_DECREASE"
    PRICE_INCREASE = "PRICE_INCREASE"
    NEW_TIER = "NEW_TIER"
    TIER_REMOVED = "TIER_REMOVED"
    FEATURE_ADDED = "FEATURE_ADDED"

class TrendDelta(BaseModel):
    competitor_name: str
    product_name: str
    delta_type: DeltaType
    metric_name: str
    old_value: Optional[str]
    new_value: str
    percentage_change: Optional[float] = None
    strategic_severity: str = Field(description="LOW | MEDIUM | HIGH | CRITICAL")

class StrategicRecommendation(BaseModel):
    category: str = Field(description="PRICING | POSITIONING | PRODUCT_ROADMAP")
    title: str
    rationale: str
    actionable_next_step: str
    corroborating_sources: List[str] = Field(min_length=1, description="List of source URLs supporting this finding")
    corroboration_count: int = Field(ge=1)
```

---

## 2. Production Prompt Engineering Library

All prompts are saved as template files under `scrybe/agents/prompts/` to ensure modularity, versioning, and zero hardcoded strings.

### 2.1 Analyst Extraction Prompt (`analyst_extract.txt`)

```text
You are Scrybe's Lead Data Analyst Agent. Your objective is to extract structured pricing and feature information from the provided web markdown text.

STRICT ACCURACY RULES:
1. ONLY extract information that is explicitly stated in the provided text.
2. If a specific field (such as input price, context window, or currency) is NOT explicitly mentioned on the page, set its value to null. DO NOT GUESS OR ESTIMATE.
3. Normalize all token pricing to "USD per 1,000,000 (1M) tokens". 
   - Example: If the page says "$0.0025 per 1K tokens", multiply by 1,000 to get 2.50 per 1M tokens.
   - Example: If the page says "$5.00 / MTok", the value is 5.00.
4. For every tier extracted, include a direct verbatim snippet ("citation_text") of 10-30 words from the text confirming the values.
5. Provide an extraction confidence score between 0.0 and 1.0 based on clarity and completeness of the source text.

TARGET OUTPUT SCHEMA:
Respond ONLY with a valid JSON object matching this schema:
{
  "company_name": "string",
  "product_name": "string",
  "source_url": "{source_url}",
  "pricing_tiers": [
    {
      "model_or_tier_name": "string",
      "input_price_per_m_tokens": float | null,
      "output_price_per_m_tokens": float | null,
      "cache_read_price_per_m_tokens": float | null,
      "context_window_tokens": int | null,
      "fixed_monthly_price": float | null,
      "currency": "USD",
      "notable_features": ["string"]
    }
  ],
  "enterprise_terms_mentioned": boolean,
  "rate_limits_summary": string | null,
  "extraction_confidence": float,
  "citation_text": "string"
}

SOURCE MARKDOWN CONTENT:
---
{markdown_content}
---
```

### 2.2 Strategist Synthesis & Corroboration Prompt (`strategist_synthesize.txt`)

```text
You are Scrybe's Principal Competitive Strategist. Your objective is to analyze the extracted competitor pricing records, historical deltas, and market signals to create an executive-ready strategic brief.

MANDATORY RULES:
1. MULTI-SOURCE CORROBORATION: For any macro-level industry claim (e.g., "The industry is shifting towards sub-$1 reasoning models"), you MUST cite at least 2 distinct competitor sources. If only 1 competitor exhibited the behavior, describe it as an isolated move by that company.
2. ACTIONABLE & QUANTIFIED: Do not write generic advice like "optimize pricing". Write quantified recommendations such as: "Competitor A slashed batch inference rates by 50%. Recommend offering a 40% batch discount on off-peak inference to retain high-volume enterprise accounts."
3. BATTLECARD POINTS: Provide 3 clear points where our product wins vs each competitor, and 2 vulnerabilities to defend against.

INPUT DATA:
- Extracted Current Records: {extracted_records_json}
- Historical Deltas: {historical_deltas_json}
- Current Date: {current_date}

OUTPUT FORMAT:
Generate your analysis in structured JSON matching:
{
  "executive_summary": "string (3-4 crisp sentences for VP/Founders)",
  "key_market_deltas": [
    {
      "competitor_name": "string",
      "summary_of_change": "string",
      "impact_severity": "LOW | MEDIUM | HIGH | CRITICAL"
    }
  ],
  "strategic_recommendations": [
    {
      "category": "PRICING | POSITIONING | PRODUCT_ROADMAP",
      "title": "string",
      "rationale": "string",
      "actionable_next_step": "string",
      "corroborating_sources": ["url1", "url2"]
    }
  ],
  "sales_battlecard_snippets": {
    "competitor_name": {
      "our_advantages": ["string"],
      "competitor_advantages": ["string"],
      "recommended_talk_track": "string"
    }
  }
}
```

### 2.3 Self-Healing Selector Fallback Prompt (`self_healing_selector.txt`)

```text
You are Scrybe's DOM Repair & Semantic Extraction Agent.
The automated CSS selector '{failed_selector}' failed to locate the pricing table on target URL '{source_url}'.

OBJECTIVE:
1. Inspect the following semantic HTML / DOM excerpt.
2. Extract the structured pricing data regardless of selector changes.
3. Suggest a resilient, updated CSS selector or XPath for future automated runs that targets the new container.

HTML EXCERPT:
---
{dom_excerpt}
---

OUTPUT FORMAT:
{
  "healed_selector": "string (e.g., 'table.pricing-matrix, div[data-testid=\"pricing-grid\"]')",
  "confidence_in_selector": float,
  "extracted_data": { ... }
}
```

### 2.4 Reflexion Error Repair Prompt (`reflexion_repair.txt`)

```text
You are Scrybe's Reflexion Agent. An extraction or validation failure occurred during the pipeline run.

PREVIOUS EXECUTION ATTEMPT:
Agent: {agent_name}
Input Excerpt: {input_excerpt}
Error Trace / Validation Error: {error_trace}

INSTRUCTIONS:
1. Conduct a brief verbal self-critique: Explain precisely why the previous attempt failed.
2. Formulate a concrete correction strategy.
3. Produce the corrected, validated JSON output that resolves all validation errors.

OUTPUT:
{
  "critique": "string",
  "root_cause": "SCHEMA_MISMATCH | TOKEN_MULTIPLIER_ERROR | INVALID_JSON",
  "remedy": "string",
  "corrected_output": { ... }
}
```
