"""A2A Agent Wrappers — Wrap each Scrybe agent as an A2A-compliant service.

Each wrapper:
1. Defines an Agent Card with skills, capabilities, and endpoint
2. Implements an async handler that processes A2A Tasks
3. Translates between A2A Messages/Artifacts and agent-specific types

These wrappers make every Scrybe agent discoverable and invocable
via the A2A protocol without modifying the original agent code.
"""

import json
from typing import Any, Dict, Optional

from scrybe.a2a.models import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    Artifact,
    DataPart,
    Message,
    Task,
    TextPart,
)
from scrybe.a2a.server import A2AServer
from scrybe.logging_config import get_agent_logger

logger = get_agent_logger("a2a_wrappers")


# ── Agent Card Definitions ───────────────────────────────────────

COMPLIANCE_CARD = AgentCard(
    name="compliance",
    description=(
        "Compliance Agent — Enforces ethical scraping rules. "
        "Checks robots.txt, filters PII, blocks SSRF, and produces audit records."
    ),
    url="http://localhost:8010",
    capabilities=AgentCapabilities(streaming=False),
    skills=[
        AgentSkill(
            id="preflight_check",
            name="Compliance Preflight Check",
            description="Validate a URL against robots.txt, SSRF, and compliance rules.",
            tags=["compliance", "robots", "ssrf", "pii"],
        ),
        AgentSkill(
            id="scrub_pii",
            name="PII Scrubbing",
            description="Remove personally identifiable information from text.",
            tags=["compliance", "pii", "privacy"],
        ),
    ],
)

READER_CARD = AgentCard(
    name="reader",
    description=(
        "Reader Agent — Tiered web scraper (httpx → curl_cffi → Playwright). "
        "Fetches and cleans web content with compliance-first design."
    ),
    url="http://localhost:8011",
    capabilities=AgentCapabilities(streaming=True),
    skills=[
        AgentSkill(
            id="scrape_sources",
            name="Web Scraping",
            description="Scrape configured web sources with tiered escalation.",
            tags=["scraping", "web", "http", "playwright"],
            examples=["Scrape pricing data from openai.com"],
        ),
    ],
)

ANALYST_CARD = AgentCard(
    name="analyst",
    description=(
        "Analyst Agent — LLM-based structured data extraction with "
        "zero-hallucination guardrails and Reflexion self-repair."
    ),
    url="http://localhost:8012",
    capabilities=AgentCapabilities(streaming=True),
    skills=[
        AgentSkill(
            id="extract_structured_data",
            name="Structured Data Extraction",
            description="Extract typed pricing/feature records from cleaned web content.",
            tags=["extraction", "llm", "validation", "pricing"],
        ),
    ],
)

MEMORY_CARD = AgentCard(
    name="memory",
    description=(
        "Memory Agent — Coordinates rolling buffer, Reflexion loop, "
        "and FAISS vector store for semantic delta detection."
    ),
    url="http://localhost:8013",
    capabilities=AgentCapabilities(streaming=False),
    skills=[
        AgentSkill(
            id="detect_deltas",
            name="Delta Detection",
            description="Compare current extractions against historical data to detect changes.",
            tags=["memory", "delta", "vector", "faiss"],
        ),
    ],
)

STRATEGIST_CARD = AgentCard(
    name="strategist",
    description=(
        "Strategist Agent — Competitive analysis, pricing delta synthesis, "
        "and strategic recommendation generation with ≥2-source corroboration."
    ),
    url="http://localhost:8014",
    capabilities=AgentCapabilities(streaming=True),
    skills=[
        AgentSkill(
            id="synthesize_strategy",
            name="Strategic Synthesis",
            description="Generate executive summary, market deltas, recommendations, and battlecards.",
            tags=["strategy", "analysis", "recommendations", "battlecards"],
        ),
    ],
)

FORMATTER_CARD = AgentCard(
    name="formatter",
    description=(
        "Formatter Agent — Compiles intelligence into Markdown reports, "
        "PDF briefs, and structured JSON payloads."
    ),
    url="http://localhost:8015",
    capabilities=AgentCapabilities(streaming=False),
    skills=[
        AgentSkill(
            id="generate_reports",
            name="Report Generation",
            description="Generate executive Markdown/PDF reports with citations.",
            tags=["reports", "markdown", "pdf", "formatting"],
        ),
    ],
)

ALL_AGENT_CARDS = [
    COMPLIANCE_CARD,
    READER_CARD,
    ANALYST_CARD,
    MEMORY_CARD,
    STRATEGIST_CARD,
    FORMATTER_CARD,
]


# ── Handler Factories ────────────────────────────────────────────

def create_compliance_handler(settings=None):
    """Create the A2A handler for the Compliance Agent."""
    from scrybe.agents.compliance import ComplianceAgent

    agent = ComplianceAgent()

    async def handler(task: Task) -> Task:
        message = task.messages[-1] if task.messages else None
        if not message:
            task.fail("No message provided")
            return task

        data = message.get_data() or {}
        action = data.get("action", "preflight_check")

        if action == "preflight_check":
            url = data.get("url", "")
            if not url:
                task.fail("No URL provided for preflight check")
                return task

            audit = agent.check_preflight(url)
            artifact = Artifact(name="compliance_audit")
            artifact.add_data(audit.model_dump(mode="json"))
            task.add_artifact(artifact)
            task.complete(f"Compliance check complete for {url}")

        elif action == "scrub_pii":
            text = data.get("text", "") or message.get_text()
            cleaned, count = agent.scrub_pii(text)
            artifact = Artifact(name="pii_scrubbed")
            artifact.add_data({"cleaned_text": cleaned, "pii_count": count})
            task.add_artifact(artifact)
            task.complete(f"PII scrubbing complete: {count} items redacted")

        return task

    return handler


def create_reader_handler(settings=None):
    """Create the A2A handler for the Reader Agent."""
    from scrybe.agents.compliance import ComplianceAgent
    from scrybe.agents.reader import ReaderAgent
    from scrybe.memory.buffer import RollingBuffer
    from config.settings import load_sources

    compliance = ComplianceAgent()
    buffer = RollingBuffer()
    agent = ReaderAgent(compliance_agent=compliance, buffer=buffer)

    async def handler(task: Task) -> Task:
        message = task.messages[-1] if task.messages else None
        if not message:
            task.fail("No message provided")
            return task

        data = message.get_data() or {}
        sources_path = data.get("sources_config_path")

        # Load sources
        sources = load_sources(sources_path)
        if not sources:
            task.fail("No sources configured")
            return task

        task.start_work(f"Scraping {len(sources)} sources...")

        # Execute scraping
        documents = await agent.run(sources)

        # Package results as artifact
        artifact = Artifact(name="scraped_documents")
        artifact.add_data({
            "documents": [doc.model_dump(mode="json") for doc in documents],
            "count": len(documents),
            "sources_attempted": len(sources),
        })
        task.add_artifact(artifact)
        task.complete(f"Scraped {len(documents)}/{len(sources)} sources")
        return task

    return handler


def create_analyst_handler(settings=None):
    """Create the A2A handler for the Analyst Agent."""
    from scrybe.agents.analyst import AnalystAgent
    from scrybe.memory.buffer import RollingBuffer
    from scrybe.storage.models import RawScrapedDocument
    from scrybe.tools.llm_client import LLMClient
    from config.settings import settings as default_settings

    active_settings = settings or default_settings
    llm_client = None
    if active_settings and (active_settings.openai_api_key or active_settings.anthropic_api_key or active_settings.google_api_key):
        llm_client = LLMClient(
            openai_api_key=active_settings.openai_api_key,
            anthropic_api_key=active_settings.anthropic_api_key,
            google_api_key=active_settings.google_api_key,
        )

    buffer = RollingBuffer()
    agent = AnalystAgent(
        llm_client=llm_client,
        extraction_model=active_settings.extraction_model if active_settings else "gpt-4o-mini",
        confidence_threshold=active_settings.confidence_threshold if active_settings else 0.60,
        buffer=buffer,
    )

    async def handler(task: Task) -> Task:
        message = task.messages[-1] if task.messages else None
        if not message:
            task.fail("No message provided")
            return task

        data = message.get_data() or {}
        raw_docs_data = data.get("documents", [])

        if not raw_docs_data:
            task.fail("No documents provided for extraction")
            return task

        # Reconstruct RawScrapedDocument objects
        documents = [RawScrapedDocument(**doc) for doc in raw_docs_data]
        task.start_work(f"Extracting data from {len(documents)} documents...")

        validated, flagged = agent.run(documents)

        artifact = Artifact(name="extracted_records")
        artifact.add_data({
            "validated_records": [r.model_dump(mode="json") for r in validated],
            "flagged_records": flagged,
            "validated_count": len(validated),
            "flagged_count": len(flagged),
        })
        task.add_artifact(artifact)
        task.complete(f"Extracted {len(validated)} validated, {len(flagged)} flagged")
        return task

    return handler


def create_memory_handler(settings=None):
    """Create the A2A handler for the Memory Agent."""
    from scrybe.agents.memory import MemoryAgent
    from scrybe.memory.buffer import RollingBuffer
    from scrybe.memory.vector_store import VectorStore
    from scrybe.storage.models import CompetitorProductRecord

    buffer = RollingBuffer()
    vector_store = VectorStore(
        index_path=settings.faiss_index_path if settings else None,
        dimension=384,
    )
    agent = MemoryAgent(buffer=buffer, vector_store=vector_store)

    async def handler(task: Task) -> Task:
        message = task.messages[-1] if task.messages else None
        if not message:
            task.fail("No message provided")
            return task

        data = message.get_data() or {}
        records_data = data.get("records", [])

        if not records_data:
            task.fail("No records provided for delta detection")
            return task

        records = [CompetitorProductRecord(**r) for r in records_data]
        deltas, unchanged = agent.run(records)

        artifact = Artifact(name="delta_detection")
        artifact.add_data({
            "deltas": [d.model_dump(mode="json") for d in deltas],
            "unchanged_companies": unchanged,
            "deltas_count": len(deltas),
        })
        task.add_artifact(artifact)

        # Save the index for next run
        agent.save_index()

        task.complete(f"Detected {len(deltas)} deltas, {len(unchanged)} unchanged")
        return task

    return handler


def create_strategist_handler(settings=None):
    """Create the A2A handler for the Strategist Agent."""
    from scrybe.agents.strategist import StrategistAgent
    from scrybe.memory.buffer import RollingBuffer
    from scrybe.storage.models import CompetitorProductRecord, TrendDelta
    from scrybe.tools.llm_client import LLMClient
    from config.settings import settings as default_settings

    active_settings = settings or default_settings
    llm_client = None
    if active_settings and (active_settings.openai_api_key or active_settings.anthropic_api_key or active_settings.google_api_key):
        llm_client = LLMClient(
            openai_api_key=active_settings.openai_api_key,
            anthropic_api_key=active_settings.anthropic_api_key,
            google_api_key=active_settings.google_api_key,
        )

    buffer = RollingBuffer()
    agent = StrategistAgent(
        llm_client=llm_client,
        reasoning_model=active_settings.reasoning_model if active_settings else "gpt-4o",
        min_corroboration=active_settings.multi_source_min_count if active_settings else 2,
        buffer=buffer,
    )

    async def handler(task: Task) -> Task:
        message = task.messages[-1] if task.messages else None
        if not message:
            task.fail("No message provided")
            return task

        data = message.get_data() or {}
        records_data = data.get("records", [])
        deltas_data = data.get("deltas", [])

        records = [CompetitorProductRecord(**r) for r in records_data]
        deltas = [TrendDelta(**d) for d in deltas_data]

        task.start_work("Synthesizing strategic analysis...")
        result = agent.run(records, deltas)

        artifact = Artifact(name="strategic_analysis")
        artifact.add_data(result)
        task.add_artifact(artifact)
        task.complete(f"Generated {len(result.get('strategic_recommendations', []))} recommendations")
        return task

    return handler


def create_formatter_handler(settings=None):
    """Create the A2A handler for the Formatter Agent."""
    from scrybe.agents.formatter import FormatterAgent
    from scrybe.memory.buffer import RollingBuffer
    from scrybe.storage.models import CompetitorProductRecord, TrendDelta

    buffer = RollingBuffer()
    agent = FormatterAgent(
        output_dir=settings.output_dir if settings else "output",
        buffer=buffer,
    )

    async def handler(task: Task) -> Task:
        message = task.messages[-1] if task.messages else None
        if not message:
            task.fail("No message provided")
            return task

        data = message.get_data() or {}
        pipeline_id = data.get("pipeline_id", "unknown")
        records_data = data.get("records", [])
        deltas_data = data.get("deltas", [])
        strategy_result = data.get("strategy_result", {})

        records = [CompetitorProductRecord(**r) for r in records_data]
        deltas = [TrendDelta(**d) for d in deltas_data]

        task.start_work("Generating reports...")
        result = agent.run(
            pipeline_id=pipeline_id,
            records=records,
            deltas=deltas,
            strategy_result=strategy_result,
        )

        artifact = Artifact(name="intelligence_reports")
        artifact.add_data({
            "report_markdown": result.get("report_markdown"),
            "report_markdown_path": result.get("report_markdown_path"),
            "report_pdf_path": result.get("report_pdf_path"),
            "report_data": result.get("report_data"),
        })
        task.add_artifact(artifact)
        task.complete("Reports generated successfully")
        return task

    return handler


# ── Server Factory ───────────────────────────────────────────────

def create_all_agent_servers(settings=None) -> Dict[str, A2AServer]:
    """Create A2A servers for all Scrybe agents.

    Returns:
        Dict mapping agent names to their A2AServer instances.
    """
    servers = {}

    card_handler_pairs = [
        (COMPLIANCE_CARD, create_compliance_handler(settings)),
        (READER_CARD, create_reader_handler(settings)),
        (ANALYST_CARD, create_analyst_handler(settings)),
        (MEMORY_CARD, create_memory_handler(settings)),
        (STRATEGIST_CARD, create_strategist_handler(settings)),
        (FORMATTER_CARD, create_formatter_handler(settings)),
    ]

    for card, handler_fn in card_handler_pairs:
        servers[card.name] = A2AServer(
            agent_card=card,
            handler=handler_fn,
        )

    return servers
