"""Scrybe CLI Entry Point.

Provides command-line interface for running the pipeline,
starting the API server, and launching the dashboard.
Supports both legacy sequential and A2A protocol modes.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))


def cmd_run(args):
    """Execute a full pipeline run."""
    if args.a2a:
        # A2A protocol mode
        from scrybe.a2a.orchestrator import run_a2a_pipeline
        from scrybe.logging_config import setup_logging
        setup_logging()

        def progress_printer(agent, event, data):
            print(f"  [{agent}] {event}: {data.get('message', '')}")

        print(f"🚀 Starting Scrybe A2A pipeline (mode={args.mode})...")
        state = run_a2a_pipeline(
            sources_config_path=args.sources or None,
            mode=args.mode,
            progress_callback=progress_printer,
        )
    else:
        # Legacy sequential mode
        from scrybe.pipeline import run_pipeline
        from scrybe.logging_config import setup_logging
        setup_logging()
        print("🚀 Starting Scrybe pipeline (sequential mode)...")
        state = run_pipeline(args.sources or None)

    metrics = state.execution_metrics
    print(f"\n✅ Pipeline complete in {metrics.get('total_seconds', 'N/A')}s")
    print(f"   Sources scraped: {metrics.get('sources_scraped', 0)}")
    print(f"   Records extracted: {metrics.get('records_extracted', 0)}")
    print(f"   Deltas detected: {metrics.get('deltas_detected', 0)}")
    print(f"   Recommendations: {metrics.get('recommendations_generated', 0)}")
    if args.a2a:
        print(f"   Protocol: {metrics.get('protocol', 'N/A')}")


def cmd_api(args):
    """Start the FastAPI server."""
    import uvicorn
    print(f"🌐 Starting Scrybe API server on port {args.port}...")
    uvicorn.run(
        "scrybe.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def cmd_dashboard(args):
    """Launch the Scrybe dashboard (React or Streamlit)."""
    import subprocess
    if args.type == "streamlit":
        dashboard_path = Path(__file__).parent / "scrybe" / "dashboard" / "app.py"
        print("📊 Launching Scrybe Streamlit legacy dashboard...")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(dashboard_path),
            "--server.port", str(args.port),
        ])
    else:
        frontend_dir = Path(__file__).parent / "frontend"
        print(f"📊 Launching Scrybe Modern React Dashboard on port {args.port}...")
        subprocess.run(["npm", "run", "dev", "--", "--port", str(args.port)], cwd=str(frontend_dir))


def cmd_dataset(args):
    """Inspect benchmark datasets or export fine-tuning JSONL."""
    from scrybe.tools.benchmark_catalog import BenchmarkCatalogLoader
    from scrybe.tools.finetuning import FineTuningPipeline

    loader = BenchmarkCatalogLoader()

    if args.fetch_openrouter:
        print("🌐 Ingesting live model catalog from OpenRouter API...")
        items = loader.fetch_openrouter_catalog()
        print(f"✅ Ingested {len(items)} providers from OpenRouter.")
    else:
        items = loader.get_golden_benchmark()

    if args.catalog or (not args.export_finetuning and not args.fetch_openrouter):
        print(f"\n📚 Scrybe Ground-Truth Benchmark Catalog ({len(items)} Competitors):")
        for item in items:
            tiers = item.get("pricing_tiers", [])
            print(f"  • {item['company_name']} ({item['product_name']}): {len(tiers)} tiers | {item['source_url']}")
            for t in tiers[:4]:
                inp = f"${t['input_price_per_m_tokens']}" if t['input_price_per_m_tokens'] is not None else "—"
                out = f"${t['output_price_per_m_tokens']}" if t['output_price_per_m_tokens'] is not None else "—"
                print(f"      - {t['model_or_tier_name']}: In {inp}/1M, Out {out}/1M")

    if args.export_finetuning:
        pipeline = FineTuningPipeline()
        out_path = Path(args.output or "data/training/scrybe_finetuning.jsonl")
        count = pipeline.export_dataset(
            items, 
            out_path, 
            format_type=args.format, 
            include_negatives=not args.no_negatives
        )
        print(f"\n✅ Exported {count} training samples to {out_path} (format={args.format})")

        script_path = out_path.parent / "train_unsloth_lora.py"
        script_code = pipeline.generate_unsloth_train_script(str(out_path))
        script_path.write_text(script_code, encoding="utf-8")
        print(f"   Generated Unsloth QLoRA fine-tuning script: {script_path}")


def cmd_evaluate(args):
    """Run the evaluation benchmark harness."""
    from scrybe.tools.benchmark_catalog import BenchmarkCatalogLoader
    from scrybe.tools.evaluation_harness import EvaluationHarness

    print("🔬 Running Scrybe Golden Benchmark Evaluation Harness...")
    loader = BenchmarkCatalogLoader()
    benchmark = loader.get_golden_benchmark()

    harness = EvaluationHarness(price_tolerance=args.tolerance)
    metrics = harness.run_benchmark(benchmark)

    report_md = harness.generate_markdown_report(metrics)
    print("\n" + report_md)

    if args.output:
        Path(args.output).write_text(report_md, encoding="utf-8")
        print(f"💾 Report saved to {args.output}")


def main():
    parser = argparse.ArgumentParser(
        description="Scrybe — Autonomous Multi-Agent Web Intelligence System (A2A Protocol)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── run ──
    run_parser = subparsers.add_parser("run", help="Execute a full pipeline run")
    run_parser.add_argument("--sources", type=str, default="", help="Path to sources.yaml")
    run_parser.add_argument("--a2a", action="store_true", help="Use A2A protocol for agent communication")
    run_parser.add_argument("--mode", choices=["in_process", "remote"], default="in_process",
                           help="A2A execution mode (in_process or remote)")
    run_parser.set_defaults(func=cmd_run)

    # ── api ──
    api_parser = subparsers.add_parser("api", help="Start the FastAPI server")
    api_parser.add_argument("--host", type=str, default="0.0.0.0")
    api_parser.add_argument("--port", type=int, default=8000)
    api_parser.add_argument("--reload", action="store_true")
    api_parser.set_defaults(func=cmd_api)

    # ── dashboard ──
    dash_parser = subparsers.add_parser("dashboard", help="Launch the Scrybe dashboard")
    dash_parser.add_argument("--port", type=int, default=3000)
    dash_parser.add_argument("--type", choices=["react", "streamlit"], default="react",
                            help="Dashboard interface type (react or streamlit)")
    dash_parser.set_defaults(func=cmd_dashboard)

    # ── dataset ──
    data_parser = subparsers.add_parser("dataset", help="Manage benchmark datasets and export fine-tuning JSONL")
    data_parser.add_argument("--catalog", action="store_true", help="Display golden benchmark catalog")
    data_parser.add_argument("--fetch-openrouter", action="store_true", help="Fetch live OpenRouter model pricing")
    data_parser.add_argument("--export-finetuning", action="store_true", help="Export dataset for model fine-tuning")
    data_parser.add_argument("--format", choices=["chatml", "alpaca"], default="chatml", help="Export training format")
    data_parser.add_argument("--output", type=str, default="", help="Output filepath for exported dataset")
    data_parser.add_argument("--no-negatives", action="store_true", help="Omit adversarial negative samples")
    data_parser.set_defaults(func=cmd_dataset)

    # ── evaluate ──
    eval_parser = subparsers.add_parser("evaluate", help="Run quantitative evaluation harness")
    eval_parser.add_argument("--tolerance", type=float, default=0.05, help="Price matching tolerance")
    eval_parser.add_argument("--output", type=str, default="", help="Filepath to write evaluation markdown report")
    eval_parser.set_defaults(func=cmd_evaluate)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
