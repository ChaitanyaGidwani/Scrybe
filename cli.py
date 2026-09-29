"""Scrybe CLI Entry Point.

Provides command-line interface for running the pipeline,
starting the API server, and launching the dashboard.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def cmd_run(args):
    """Execute a full pipeline run."""
    from scrybe.logging_config import setup_logging
    from scrybe.pipeline import Pipeline

    setup_logging(args.log_level)

    pipeline = Pipeline()
    state = asyncio.run(pipeline.run(args.sources))

    print(f"\n{'='*60}")
    print(f"Pipeline Complete: {pipeline.pipeline_id}")
    print(f"{'='*60}")
    for key, value in state.execution_metrics.items():
        print(f"  {key}: {value}")
    print(f"{'='*60}\n")


def cmd_api(args):
    """Start the FastAPI server."""
    import uvicorn
    uvicorn.run(
        "scrybe.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower(),
    )


def cmd_dashboard(args):
    """Launch the Streamlit dashboard."""
    import subprocess
    dashboard_path = Path(__file__).parent / "scrybe" / "dashboard" / "app.py"
    subprocess.run(
        ["streamlit", "run", str(dashboard_path), "--server.port", str(args.port)],
        check=True,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Scrybe — Autonomous Multi-Agent Web Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Execute a full pipeline run")
    run_parser.add_argument("--sources", type=str, default=None, help="Path to sources.yaml config")
    run_parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    run_parser.set_defaults(func=cmd_run)

    # API server command
    api_parser = subparsers.add_parser("api", help="Start the FastAPI server")
    api_parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind host")
    api_parser.add_argument("--port", type=int, default=8000, help="Bind port")
    api_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    api_parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    api_parser.set_defaults(func=cmd_api)

    # Dashboard command
    dash_parser = subparsers.add_parser("dashboard", help="Launch the Streamlit dashboard")
    dash_parser.add_argument("--port", type=int, default=8501, help="Dashboard port")
    dash_parser.set_defaults(func=cmd_dashboard)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
