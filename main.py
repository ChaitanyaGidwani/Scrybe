#!/usr/bin/env python3
"""Scrybe Main Application Entry Point.

Provides an intuitive, unified interface to run:
- Live multi-agent pipeline (A2A Protocol / sequential)
- Instant offline presentation demo (Golden Benchmark)
- Competitor pricing matrix inspection
- Intelligence report previews
- API server & React Dashboard hosting
- System health checks and agent discovery
"""

import argparse
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import helper


def run_pipeline_action(mode: str = "in_process", sources_path: str = None) -> None:
    """Run the live multi-agent pipeline."""
    print(f"\n🚀 Launching Scrybe A2A Multi-Agent Pipeline (mode={mode})...")
    from scrybe.a2a.orchestrator import run_a2a_pipeline
    from scrybe.logging_config import setup_logging
    setup_logging()

    def progress_printer(agent, event, data):
        msg = data.get("message", "")
        print(f"  [{agent.upper():<10}] {event}: {msg}")

    try:
        state = run_a2a_pipeline(
            sources_config_path=sources_path,
            mode=mode,
            progress_callback=progress_printer,
        )
        metrics = state.execution_metrics
        print(f"\n✅ Pipeline Complete in {metrics.get('total_seconds', 'N/A')}s")
        print(f"   Sources scraped: {metrics.get('sources_scraped', 0)}")
        print(f"   Records extracted: {metrics.get('records_extracted', 0)}")
        print(f"   Deltas detected: {metrics.get('deltas_detected', 0)}")
        print(f"   Recommendations: {metrics.get('recommendations_generated', 0)}")
        if state.report_markdown:
            print(f"   Report: {state.report_pdf_path or 'Markdown generated'}")
    except Exception as e:
        print(f"\n❌ Pipeline execution encountered an error: {e}")


def start_server_action(host: str = "0.0.0.0", port: int = 8001) -> None:
    """Start the FastAPI backend and serve the Web Dashboard."""
    import uvicorn
    print(f"\n🌐 Hosting Scrybe API Server & Web Dashboard on http://localhost:{port}...")
    print(f"   • Dashboard: http://localhost:{port}")
    print(f"   • API Docs : http://localhost:{port}/docs")
    print(f"   • Health   : http://localhost:{port}/health\n")
    uvicorn.run("scrybe.api.main:app", host=host, port=port, reload=False)


def interactive_menu() -> None:
    """Display an interactive CLI menu when run without arguments."""
    helper.print_banner()

    menu = """
Select an action:
  [1] 🚀 Run Live Multi-Agent Pipeline (A2A Protocol)
  [2] 🧪 Run Instant Offline Demo (Golden Benchmark — Fast & Zero API key)
  [3] 📊 View Competitor Pricing Matrix
  [4] 📑 View Latest Intelligence Reports
  [5] 📖 Read Executive Brief Preview
  [6] 🌐 Start API Server & Web Dashboard
  [7] 🤖 View Agent Roster & A2A Topology
  [8] 🩺 Run System Diagnostics & Health Check
  [9] 🚪 Exit
"""

    while True:
        print(menu)
        try:
            choice = input("Enter choice [1-9]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Exiting Scrybe.")
            break

        if choice == "1":
            print("\nSelect execution mode:")
            print("  1. In-process (Direct handler calls, recommended for local)")
            print("  2. Remote (Decoupled HTTP microservices)")
            sub = input("Choose mode [1 or 2, default 1]: ").strip()
            mode = "remote" if sub == "2" else "in_process"
            run_pipeline_action(mode=mode)

        elif choice == "2":
            helper.run_demo_pipeline()
            helper.print_pricing_matrix()

        elif choice == "3":
            helper.print_pricing_matrix()

        elif choice == "4":
            helper.print_reports_summary()

        elif choice == "5":
            helper.preview_report()

        elif choice == "6":
            port_input = input("Enter port [default: 8001]: ").strip()
            port = int(port_input) if port_input.isdigit() else 8001
            try:
                start_server_action(port=port)
            except KeyboardInterrupt:
                print("\n🛑 Server stopped.")

        elif choice == "7":
            helper.print_agent_roster()

        elif choice == "8":
            helper.check_environment()

        elif choice == "9":
            print("👋 Goodbye!")
            break
        else:
            print("⚠️  Invalid option. Please enter a number between 1 and 9.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrybe — Autonomous Multi-Agent Web Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--run",
        action="store_true",
        help="Run the multi-agent pipeline",
    )
    parser.add_argument(
        "--mode",
        choices=["in_process", "remote"],
        default="in_process",
        help="Pipeline execution mode (default: in_process)",
    )
    parser.add_argument(
        "--sources",
        type=str,
        default=None,
        help="Path to custom sources.yaml configuration",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run instant offline demo using Golden Benchmark catalog",
    )
    parser.add_argument(
        "--matrix",
        action="store_true",
        help="Display extracted competitor pricing matrix",
    )
    parser.add_argument(
        "--reports",
        action="store_true",
        help="List recent intelligence reports",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview latest generated intelligence brief in terminal",
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Start the FastAPI server & Web Dashboard",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for API server & dashboard (default: 8001)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host address for API server (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--agents",
        action="store_true",
        help="Display 6-agent A2A topology roster",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Run system and environment diagnostic checks",
    )

    args = parser.parse_args()

    # Route based on flags
    if args.run:
        helper.print_banner()
        run_pipeline_action(mode=args.mode, sources_path=args.sources)
    elif args.demo:
        helper.print_banner()
        helper.run_demo_pipeline()
        helper.print_pricing_matrix()
    elif args.matrix:
        helper.print_pricing_matrix()
    elif args.reports:
        helper.print_reports_summary()
    elif args.preview:
        helper.preview_report()
    elif args.agents:
        helper.print_agent_roster()
    elif args.health:
        helper.check_environment()
    elif args.api:
        start_server_action(host=args.host, port=args.port)
    else:
        # Default to interactive menu if no flags provided
        interactive_menu()


if __name__ == "__main__":
    main()
