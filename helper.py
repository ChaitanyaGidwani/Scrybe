"""Scrybe Helper Utilities.

Provides convenience functions for Scrybe:
- Environment & API key validation
- Competitor pricing matrix formatting
- Benchmark and offline demo runner
- Report discovery and previews
- Agent topology and health checks
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from scrybe.storage.db import DatabaseManager


def get_db() -> DatabaseManager:
    """Get an initialized DatabaseManager instance."""
    return DatabaseManager(database_url=settings.database_url)


def print_banner() -> None:
    """Print the Scrybe ASCII banner and executive overview."""
    banner = r"""
  ____                  _             🦅
 / ___|  ___ _ __ _   _| |__   ___ 
 \___ \ / __| '__| | | | '_ \ / _ \
  ___) | (__| |  | |_| | |_) |  __/
 |____/ \___|_|   \__, |_.__/ \___|
                  |___/             
 Autonomous Multi-Agent Web Intelligence & Market Synthesis
 Protocol: A2A v1.0 | 6-Agent Pipeline | Zero Hallucinations
"""
    print(banner)


def check_environment() -> Dict[str, Any]:
    """Check Python version, required dependencies, and API keys.

    Returns a summary dict and prints a clean diagnostic overview.
    """
    results: Dict[str, Any] = {
        "python_version": sys.version.split()[0],
        "python_compatible": sys.version_info >= (3, 11),
        "api_keys": {},
        "packages": {},
        "database": False,
    }

    # Check key environment variables
    keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]
    for k in keys:
        val = os.getenv(k) or getattr(settings, k.lower(), None)
        results["api_keys"][k] = bool(val)

    # Check core packages
    packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "httpx",
        "sqlalchemy",
        "faiss",
        "reportlab",
    ]
    for pkg in packages:
        try:
            __import__(pkg)
            results["packages"][pkg] = True
        except ImportError:
            results["packages"][pkg] = False

    # Check database
    try:
        db = get_db()
        db.get_reports(limit=1)
        results["database"] = True
    except Exception as e:
        results["database"] = False
        results["db_error"] = str(e)

    print("\n🩺 Scrybe System Diagnostics:")
    print("=" * 60)
    py_ok = "✅" if results["python_compatible"] else "❌"
    print(f"  {py_ok} Python Version: {results['python_version']} (>= 3.11 required)")

    print("\n  📦 Core Packages:")
    for pkg, ok in results["packages"].items():
        icon = "✅" if ok else "⚠️ "
        status = "Installed" if ok else "Missing"
        print(f"     {icon} {pkg:<14}: {status}")

    print("\n  🔑 LLM Provider Keys (at least 1 recommended for live AI synthesis):")
    for key, present in results["api_keys"].items():
        icon = "✅" if present else "⚪"
        status = "Configured" if present else "Not Set (Offline/Fallback mode)"
        print(f"     {icon} {key:<18}: {status}")

    db_ok = "✅" if results["database"] else "❌"
    print(f"\n  {db_ok} Database Engine: {settings.database_url}")
    print("=" * 60 + "\n")

    return results


def print_agent_roster() -> None:
    """Print the 6-agent A2A topology and port mappings."""
    roster = [
        ("1. Compliance Agent", "8010", "robots.txt, PII redactor, ethical guardrails"),
        ("2. Reader Agent",     "8011", "Tiered web scraper (httpx -> curl_cffi -> Playwright)"),
        ("3. Analyst Agent",    "8012", "Pydantic schema extraction & DOM grounding"),
        ("4. Memory Agent",     "8013", "FAISS delta vector store & Reflexion self-repair"),
        ("5. Strategist Agent", "8014", "≥2-source trend corroboration & sales battlecards"),
        ("6. Formatter Agent",  "8015", "Executive Markdown & PDF publication engine"),
    ]
    print("\n🤖 Scrybe Autonomous Agent Roster (A2A Protocol):")
    print("-" * 75)
    print(f"{'Agent':<24} | {'Port':<6} | {'Core Responsibility'}")
    print("-" * 75)
    for name, port, resp in roster:
        print(f"{name:<24} | {port:<6} | {resp}")
    print("-" * 75 + "\n")


def get_pricing_matrix_data() -> List[Dict[str, Any]]:
    """Retrieve competitor pricing records from DB, falling back to Golden Benchmark."""
    db = get_db()
    reports = db.get_reports(limit=1)
    records: List[Dict[str, Any]] = []

    if reports:
        latest_pipeline_id = reports[0].get("pipeline_id", "")
        records = db.get_extracted_records(latest_pipeline_id)

    # Fallback to Golden Benchmark catalog if database has no runs yet
    if not records:
        from scrybe.tools.benchmark_catalog import BenchmarkCatalogLoader
        loader = BenchmarkCatalogLoader()
        records = loader.get_golden_benchmark()

    return records


def print_pricing_matrix(records: Optional[List[Dict[str, Any]]] = None) -> None:
    """Pretty-print a tabular competitor pricing matrix."""
    if records is None:
        records = get_pricing_matrix_data()

    if not records:
        print("\nℹ️  No competitor pricing records found. Run the pipeline first.")
        return

    print("\n📊 Competitor Pricing & Feature Matrix:")
    print("=" * 85)
    header = f"{'Company':<15} | {'Model / Tier':<16} | {'Input ($/1M)':<14} | {'Output ($/1M)':<14} | {'Monthly'}"
    print(header)
    print("-" * 85)

    for item in records:
        company = item.get("company_name", "Unknown")
        tiers = item.get("pricing_tiers", [])
        if not tiers:
            print(f"{company:<15} | {'(No tiers)':<16} | {'-':<14} | {'-':<14} | {'-'}")
            continue

        for idx, tier in enumerate(tiers):
            name = tier.get("model_or_tier_name") or tier.get("tier_name") or "Standard"
            in_p = tier.get("input_price_per_m_tokens")
            out_p = tier.get("output_price_per_m_tokens")
            mo_p = tier.get("base_price_monthly")

            in_str = f"${in_p:.2f}" if in_p is not None else "N/A"
            out_str = f"${out_p:.2f}" if out_p is not None else "N/A"
            mo_str = f"${mo_p:.2f}" if mo_p is not None else "Pay-as-you-go"

            comp_display = company if idx == 0 else ""
            print(f"{comp_display:<15} | {name:<16} | {in_str:<14} | {out_str:<14} | {mo_str}")

    print("=" * 85 + "\n")


def get_latest_reports(limit: int = 5) -> List[Dict[str, Any]]:
    """Get the most recent reports from DB and filesystem."""
    db = get_db()
    reports = db.get_reports(limit=limit)

    # Also check data/reports directory
    reports_dir = PROJECT_ROOT / "data" / "reports"
    file_reports: List[Dict[str, Any]] = []
    if reports_dir.exists():
        for file in sorted(reports_dir.glob("*.md"), key=os.path.getmtime, reverse=True)[:limit]:
            file_reports.append({
                "title": file.stem.replace("_", " ").title(),
                "report_id": file.stem,
                "markdown_path": str(file),
                "generated_at": datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc).isoformat(),
            })

    return reports or file_reports


def print_reports_summary() -> None:
    """Print a list of recent reports and their locations."""
    reports = get_latest_reports(limit=5)
    if not reports:
        print("\nℹ️  No reports generated yet. Run the pipeline to produce one.")
        return

    print("\n📑 Recent Market Intelligence Reports:")
    print("-" * 75)
    for idx, r in enumerate(reports, 1):
        title = r.get("title", "Market Intelligence Report")
        dt = r.get("generated_at", "N/A")
        md_path = r.get("markdown_path") or r.get("report_path") or "Generated in DB"
        pdf_path = r.get("pdf_path", "N/A")
        print(f" [{idx}] {title}")
        print(f"     Generated: {dt}")
        print(f"     Markdown : {md_path}")
        if pdf_path and pdf_path != "N/A":
            print(f"     PDF      : {pdf_path}")
        print()
    print("-" * 75)


def preview_report(report_path: Optional[str] = None, max_lines: int = 40) -> None:
    """Preview markdown report in the terminal."""
    target_path: Optional[Path] = None

    if report_path:
        target_path = Path(report_path)
    else:
        # Find latest report from DB or output/ directory
        reports = get_latest_reports(limit=1)
        if reports:
            cand = reports[0].get("markdown_path") or reports[0].get("report_path")
            if cand:
                target_path = Path(cand)
        
        if not target_path or not target_path.exists():
            output_dir = PROJECT_ROOT / "output"
            if output_dir.exists():
                md_files = sorted(output_dir.glob("*.md"), key=os.path.getmtime, reverse=True)
                if md_files:
                    target_path = md_files[0]

    if not target_path or not target_path.exists():
        print("\nℹ️  No report file found to preview. Run the pipeline or demo first.")
        return

    print(f"\n📖 Previewing Report: {target_path.name}")
    print("=" * 75)
    try:
        content = target_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        for line in lines[:max_lines]:
            print(line)
        if len(lines) > max_lines:
            print(f"\n... [{len(lines) - max_lines} more lines in {target_path}] ...")
    except Exception as e:
        print(f"Error reading report: {e}")
    print("=" * 75 + "\n")



def run_demo_pipeline() -> Dict[str, Any]:
    """Execute an instant offline demo using the Golden Benchmark dataset.

    Simulates the 6-agent workflow without requiring live network calls
    or external API keys. Ideal for presentations.
    """
    print("\n🧪 Running Scrybe Offline Presentation Demo...")
    print("=" * 65)

    from scrybe.tools.benchmark_catalog import BenchmarkCatalogLoader
    from scrybe.storage.models import ScrybeState, CompetitorProductRecord, PricingTier
    from scrybe.agents.memory import MemoryAgent
    from scrybe.agents.strategist import StrategistAgent
    from scrybe.agents.formatter import FormatterAgent

    # Step 1: Ingest ground-truth benchmark records
    print("  [1/4] 🛡️ Compliance & Ingestion: Ingesting Golden AI Benchmark Catalog...")
    loader = BenchmarkCatalogLoader()
    benchmark_data = loader.get_golden_benchmark()

    pipeline_id = f"demo_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    state = ScrybeState(
        pipeline_id=pipeline_id,
        target_vertical="B2B_AI_DEVELOPER_PLATFORMS",
    )

    # Step 2: Convert to typed competitor records
    print("  [2/4] 🔍 Analyst Agent: Validating structured schemas & DOM grounding...")
    for item in benchmark_data:
        tiers = [PricingTier(**t) for t in item.get("pricing_tiers", [])]
        record = CompetitorProductRecord(
            company_name=item["company_name"],
            product_name=item["product_name"],
            source_url=item["source_url"],
            pricing_tiers=tiers,
            enterprise_terms_mentioned=item.get("enterprise_terms_mentioned", False),
            rate_limits_summary=item.get("rate_limits_summary"),
            citation_text=item.get("citation_text", ""),
            extraction_confidence=0.95,
        )
        state.extracted_records.append(record)

    # Step 3: Memory delta detection & Strategist synthesis
    print("  [3/4] 🧠 Memory & Strategist: Evaluating multi-source corroboration...")
    memory_agent = MemoryAgent()
    state.historical_deltas, unchanged = memory_agent.run(state.extracted_records)

    strategist_agent = StrategistAgent()
    strategy_result = strategist_agent.run(state.extracted_records, state.historical_deltas)

    # Step 4: Formatter Agent
    print("  [4/4] 📑 Formatter Agent: Compiling executive brief & PDF...")
    formatter_agent = FormatterAgent()
    formatter_result = formatter_agent.run(
        pipeline_id=pipeline_id,
        records=state.extracted_records,
        deltas=state.historical_deltas,
        strategy_result=strategy_result,
    )
    state.report_markdown = formatter_result.get("report_markdown")
    state.report_pdf_path = formatter_result.get("report_pdf_path")
    report_markdown_path = formatter_result.get("report_markdown_path")

    # Persist to database
    db = get_db()
    db.create_run(pipeline_id, sources_count=len(benchmark_data))
    for r in state.extracted_records:
        db.save_extracted_record(pipeline_id, r.model_dump())
    
    if "report_data" in formatter_result:
        db.save_report(formatter_result["report_data"])

    db.complete_run(
        pipeline_id=pipeline_id,
        status="COMPLETED",
        records_extracted=len(state.extracted_records),
        report_path=report_markdown_path,
        metrics={"mode": "demo", "records": len(state.extracted_records)},
    )

    print("=" * 65)
    print("✅ Demo Pipeline Completed Successfully!")
    print(f"   Pipeline ID : {pipeline_id}")
    print(f"   Competitors : {len(state.extracted_records)} verified")
    print(f"   Report File : {report_markdown_path}")
    print("=" * 65 + "\n")

    return {
        "pipeline_id": pipeline_id,
        "records_count": len(state.extracted_records),
        "report_path": report_markdown_path,
    }
