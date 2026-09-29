"""Scrybe Benchmark Datasets & Real-World Pricing Catalog.

Provides curated ground-truth datasets for B2B AI Developer Platforms & APIs:
1. Curated Golden Benchmark: Hand-verified DOM snippets + target Pydantic records.
2. Real-World Catalog: Reference pricing across top frontier and open-weights models
   (OpenAI, Anthropic, Google Vertex, Groq, Together, Mistral, Cohere, Pinecone).
3. OpenRouter API live ingestor with offline cache fallback.
"""

import json
import logging
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger("scrybe.datasets")

# ── Reference Ground-Truth AI Platform Pricing Catalog ───────────

GOLDEN_AI_PRICING_CATALOG: List[Dict[str, Any]] = [
    {
        "company_name": "OpenAI",
        "product_name": "API & Frontier Models",
        "source_url": "https://openai.com/api/pricing/",
        "pricing_tiers": [
            {
                "model_or_tier_name": "GPT-4o",
                "input_price_per_m_tokens": 2.50,
                "output_price_per_m_tokens": 10.00,
                "base_price_monthly": None,
                "seat_price_monthly": None,
            },
            {
                "model_or_tier_name": "GPT-4o mini",
                "input_price_per_m_tokens": 0.15,
                "output_price_per_m_tokens": 0.60,
                "base_price_monthly": None,
                "seat_price_monthly": None,
            },
            {
                "model_or_tier_name": "o1-preview",
                "input_price_per_m_tokens": 15.00,
                "output_price_per_m_tokens": 60.00,
                "base_price_monthly": None,
                "seat_price_monthly": None,
            },
            {
                "model_or_tier_name": "o1-mini",
                "input_price_per_m_tokens": 3.00,
                "output_price_per_m_tokens": 12.00,
                "base_price_monthly": None,
                "seat_price_monthly": None,
            },
        ],
        "enterprise_terms_mentioned": True,
        "rate_limits_summary": "Tier 5: 10,000 RPM, 30,000,000 TPM for Tier 5 accounts",
        "citation_text": "GPT-4o is $2.50 per 1M input tokens and $10.00 per 1M output tokens.",
        "sample_html_snippet": """
        <div class="pricing-table">
            <h2>GPT-4o</h2>
            <p>Our flagship model for complex, multi-step tasks.</p>
            <span class="price-input">$2.50 / 1M input tokens</span>
            <span class="price-output">$10.00 / 1M output tokens</span>
            <h2>GPT-4o mini</h2>
            <span class="price-input">$0.15 / 1M input tokens</span>
            <span class="price-output">$0.60 / 1M output tokens</span>
            <h2>o1-preview</h2>
            <span class="price-input">$15.00 / 1M input tokens</span>
            <span class="price-output">$60.00 / 1M output tokens</span>
            <h2>o1-mini</h2>
            <span class="price-input">$3.00 / 1M input tokens</span>
            <span class="price-output">$12.00 / 1M output tokens</span>
            <div class="enterprise-box">Contact sales for custom rate limits and volume discounts.</div>
        </div>
        """,
    },
    {
        "company_name": "Anthropic",
        "product_name": "Claude API",
        "source_url": "https://www.anthropic.com/pricing",
        "pricing_tiers": [
            {
                "model_or_tier_name": "Claude 3.5 Sonnet",
                "input_price_per_m_tokens": 3.00,
                "output_price_per_m_tokens": 15.00,
                "base_price_monthly": None,
                "seat_price_monthly": None,
            },
            {
                "model_or_tier_name": "Claude 3.5 Haiku",
                "input_price_per_m_tokens": 0.80,
                "output_price_per_m_tokens": 4.00,
                "base_price_monthly": None,
                "seat_price_monthly": None,
            },
            {
                "model_or_tier_name": "Claude 3 Opus",
                "input_price_per_m_tokens": 15.00,
                "output_price_per_m_tokens": 75.00,
                "base_price_monthly": None,
                "seat_price_monthly": None,
            },
        ],
        "enterprise_terms_mentioned": True,
        "rate_limits_summary": "Prompt caching reduces costs by up to 90% and latency by up to 85%",
        "citation_text": "Claude 3.5 Sonnet costs $3 per million input tokens and $15 per million output tokens.",
        "sample_html_snippet": """
        <section id="claude-pricing">
            <h3>Claude 3.5 Sonnet</h3>
            <p>Most intelligent model. Cost: $3.00 per million input tokens, $15.00 per million output tokens.</p>
            <h3>Claude 3.5 Haiku</h3>
            <p>Fastest model. Cost: $0.80 per million input tokens, $4.00 per million output tokens.</p>
            <h3>Claude 3 Opus</h3>
            <p>Deep reasoning. Cost: $15.00 per million input tokens, $75.00 per million output tokens.</p>
            <div class="feature">Prompt Caching: Write $3.75/MTok, Read $0.30/MTok</div>
        </section>
        """,
    },
    {
        "company_name": "Groq",
        "product_name": "LPU Inference Engine",
        "source_url": "https://groq.com/pricing/",
        "pricing_tiers": [
            {
                "model_or_tier_name": "Llama 3.1 8B Instant",
                "input_price_per_m_tokens": 0.05,
                "output_price_per_m_tokens": 0.08,
                "base_price_monthly": None,
                "seat_price_monthly": None,
            },
            {
                "model_or_tier_name": "Llama 3.1 70B",
                "input_price_per_m_tokens": 0.59,
                "output_price_per_m_tokens": 0.79,
                "base_price_monthly": None,
                "seat_price_monthly": None,
            },
        ],
        "enterprise_terms_mentioned": False,
        "rate_limits_summary": "Speeds up to 800 tokens/sec on LPU hardware",
        "citation_text": "Llama 3.1 8B is $0.05 per 1M input tokens and $0.08 per 1M output tokens.",
        "sample_html_snippet": """
        <table>
            <tr><th>Model</th><th>Input / 1M</th><th>Output / 1M</th></tr>
            <tr><td>Llama 3.1 8B Instant</td><td>$0.05</td><td>$0.08</td></tr>
            <tr><td>Llama 3.1 70B</td><td>$0.59</td><td>$0.79</td></tr>
        </table>
        """,
    },
    {
        "company_name": "Together AI",
        "product_name": "Inference Platform",
        "source_url": "https://www.together.ai/pricing",
        "pricing_tiers": [
            {
                "model_or_tier_name": "Llama-3.1-405B-Instruct",
                "input_price_per_m_tokens": 3.50,
                "output_price_per_m_tokens": 3.50,
                "base_price_monthly": None,
                "seat_price_monthly": None,
            },
            {
                "model_or_tier_name": "Llama-3.1-70B-Instruct",
                "input_price_per_m_tokens": 0.88,
                "output_price_per_m_tokens": 0.88,
                "base_price_monthly": None,
                "seat_price_monthly": None,
            },
        ],
        "enterprise_terms_mentioned": True,
        "rate_limits_summary": "Dedicated GPU clusters available by reservation",
        "citation_text": "Llama 3.1 405B Turbo is $3.50 per million tokens.",
        "sample_html_snippet": """
        <div class="together-card">
            <h4>Llama-3.1-405B-Instruct</h4>
            <span class="rate">$3.50 / 1M tokens</span>
            <p>Serverless inference with dedicated instances on demand.</p>
            <h4>Llama-3.1-70B-Instruct</h4>
            <span class="rate">$0.88 / 1M tokens</span>
            <p>High speed open weights inference.</p>
        </div>
        """,
    },
    {
        "company_name": "Mistral AI",
        "product_name": "La Plateforme",
        "source_url": "https://mistral.ai/technology/#pricing",
        "pricing_tiers": [
            {
                "model_or_tier_name": "Mistral Large 2",
                "input_price_per_m_tokens": 2.00,
                "output_price_per_m_tokens": 6.00,
                "base_price_monthly": None,
                "seat_price_monthly": None,
            },
            {
                "model_or_tier_name": "Codestral",
                "input_price_per_m_tokens": 0.20,
                "output_price_per_m_tokens": 0.60,
                "base_price_monthly": None,
                "seat_price_monthly": None,
            },
        ],
        "enterprise_terms_mentioned": True,
        "rate_limits_summary": "On-premise enterprise deployment via private VPC",
        "citation_text": "Mistral Large is $2.00 / 1M input tokens and $6.00 / 1M output tokens.",
        "sample_html_snippet": """
        <div class="model-row">
            <span>Mistral Large 2</span>
            <span>$2.00 / MTok input</span>
            <span>$6.00 / MTok output</span>
            <span>Codestral</span>
            <span>$0.20 / MTok input</span>
            <span>$0.60 / MTok output</span>
        </div>
        """,
    },
    {
        "company_name": "Pinecone",
        "product_name": "Vector Database",
        "source_url": "https://www.pinecone.io/pricing/",
        "pricing_tiers": [
            {
                "model_or_tier_name": "Serverless Starter",
                "input_price_per_m_tokens": None,
                "output_price_per_m_tokens": None,
                "base_price_monthly": 0.0,
                "seat_price_monthly": None,
            },
            {
                "model_or_tier_name": "Serverless Standard",
                "input_price_per_m_tokens": None,
                "output_price_per_m_tokens": None,
                "base_price_monthly": 50.0,
                "seat_price_monthly": None,
            },
        ],
        "enterprise_terms_mentioned": True,
        "rate_limits_summary": "Reads billed per 1M RCU; Writes billed per 1M WCU",
        "citation_text": "Pinecone Serverless Starter is $0/month. Standard is $50/month base commit.",
        "sample_html_snippet": """
        <div class="pricing-card">
            <h3>Serverless Starter</h3>
            <p class="cost">$0/month</p>
            <p>Up to $5 free usage per month</p>
        </div>
        <div class="pricing-card">
            <h3>Serverless Standard</h3>
            <p class="cost">$50/month base commit</p>
            <p>Dedicated support and 99.9% SLA</p>
        </div>
        """,
    }
]


class BenchmarkCatalogLoader:
    """Loads, manages, and updates ground-truth datasets for Scrybe."""

    def __init__(self, use_offline_only: bool = False):
        self.use_offline_only = use_offline_only

    def get_golden_benchmark(self) -> List[Dict[str, Any]]:
        """Return the hand-verified Golden Benchmark test suite."""
        return GOLDEN_AI_PRICING_CATALOG

    def fetch_openrouter_catalog(self, timeout_sec: float = 10.0) -> List[Dict[str, Any]]:
        """Fetch live machine-readable model pricing catalog from OpenRouter API.

        Falls back gracefully to the offline golden dataset on failure.
        """
        if self.use_offline_only:
            return self.get_golden_benchmark()

        url = "https://openrouter.ai/api/v1/models"
        try:
            with httpx.Client(timeout=timeout_sec) as client:
                res = client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    models_list = data.get("data", [])
                    return self._normalize_openrouter_models(models_list)
        except Exception as e:
            logger.warning(f"Could not reach OpenRouter API ({e}); using offline golden benchmark.")

        return self.get_golden_benchmark()

    def _normalize_openrouter_models(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize raw OpenRouter model JSON into Scrybe competitor records."""
        by_company: Dict[str, List[Dict[str, Any]]] = {}

        for m in models:
            m_id = m.get("id", "")
            if "/" not in m_id:
                continue
            provider, model_name = m_id.split("/", 1)
            company = provider.capitalize()

            pricing = m.get("pricing", {})
            # OpenRouter prices are per 1 token (e.g. 0.0000025); convert to per 1M tokens
            prompt_token = float(pricing.get("prompt", 0) or 0)
            comp_token = float(pricing.get("completion", 0) or 0)

            tier = {
                "model_or_tier_name": model_name,
                "input_price_per_m_tokens": round(prompt_token * 1_000_000, 3) if prompt_token > 0 else None,
                "output_price_per_m_tokens": round(comp_token * 1_000_000, 3) if comp_token > 0 else None,
                "base_price_monthly": None,
                "seat_price_monthly": None,
            }

            by_company.setdefault(company, []).append(tier)

        normalized_records = []
        for company, tiers in by_company.items():
            normalized_records.append({
                "company_name": company,
                "product_name": f"{company} LLM Endpoints",
                "source_url": f"https://openrouter.ai/{company.lower()}",
                "pricing_tiers": tiers[:8],  # Keep top 8 tiers
                "enterprise_terms_mentioned": False,
                "rate_limits_summary": "OpenRouter normalized proxy routing",
                "citation_text": f"{company} pricing verified via OpenRouter catalog.",
            })

        return normalized_records
