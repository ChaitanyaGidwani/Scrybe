"""Scrybe Streamlit Dashboard.

Provides an interactive UI for:
- Triggering pipeline runs
- Viewing competitor pricing matrices
- Browsing intelligence reports
- Downloading Markdown/PDF reports
"""

import json
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

st.set_page_config(
    page_title="Scrybe — Competitive Intelligence",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_db():
    """Initialize database connection."""
    from scrybe.storage.db import DatabaseManager
    return DatabaseManager()


def main():
    # ── Sidebar ──
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/eagle--v1.png", width=64)
        st.title("Scrybe 🦅")
        st.caption("Autonomous Market Intelligence")
        st.divider()

        page = st.radio(
            "Navigate",
            ["📊 Dashboard", "📋 Reports", "💰 Pricing Matrix", "⚙️ Run Pipeline"],
            index=0,
        )

        st.divider()
        st.caption("v0.1.0 — Powered by Multi-Agent AI")

    # ── Main Content ──
    if page == "📊 Dashboard":
        render_dashboard()
    elif page == "📋 Reports":
        render_reports()
    elif page == "💰 Pricing Matrix":
        render_pricing_matrix()
    elif page == "⚙️ Run Pipeline":
        render_run_pipeline()


def render_dashboard():
    """Main dashboard with overview metrics."""
    st.title("📊 Intelligence Dashboard")
    st.markdown("---")

    db = get_db()
    reports = db.get_reports(limit=10)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Reports", len(reports))
    with col2:
        latest = reports[0] if reports else None
        st.metric("Latest Report", latest["title"][:30] + "..." if latest else "None")
    with col3:
        st.metric("Pipeline Status", "✅ Ready")
    with col4:
        st.metric("Sources Configured", "5")

    st.markdown("---")

    if reports:
        st.subheader("Recent Intelligence Reports")
        for report in reports[:5]:
            with st.expander(f"📄 {report.get('title', 'Untitled')} — {report.get('generated_at', '')}"):
                summary = report.get("executive_summary")
                if summary:
                    st.markdown(summary)

                md_content = report.get("markdown_content")
                if md_content:
                    st.download_button(
                        "📥 Download Markdown",
                        data=md_content,
                        file_name=f"report_{report.get('report_id', 'unknown')}.md",
                        mime="text/markdown",
                    )
    else:
        st.info("No reports generated yet. Run the pipeline to generate your first intelligence report.")


def render_reports():
    """Report browser with full markdown rendering."""
    st.title("📋 Intelligence Reports")
    st.markdown("---")

    db = get_db()
    reports = db.get_reports(limit=20)

    if not reports:
        st.info("No reports available. Run the pipeline first.")
        return

    report_options = {
        f"{r.get('title', 'Untitled')} ({r.get('generated_at', '')})": r.get("report_id")
        for r in reports
    }

    selected = st.selectbox("Select a report", list(report_options.keys()))
    report_id = report_options[selected]
    report = db.get_report_by_id(report_id)

    if report:
        st.subheader(report.get("title", ""))
        st.caption(f"Pipeline: {report.get('pipeline_id')} | Generated: {report.get('generated_at')}")

        md_content = report.get("markdown_content", "")
        if md_content:
            st.markdown(md_content)

            st.download_button(
                "📥 Download Full Report (Markdown)",
                data=md_content,
                file_name=f"report_{report_id}.md",
                mime="text/markdown",
            )


def render_pricing_matrix():
    """Interactive competitor pricing comparison table."""
    st.title("💰 Competitor Pricing Matrix")
    st.markdown("---")

    db = get_db()
    reports = db.get_reports(limit=1)

    if not reports:
        st.info("No pricing data available. Run the pipeline first.")
        return

    pipeline_id = reports[0].get("pipeline_id", "")
    records = db.get_extracted_records(pipeline_id)

    if not records:
        st.warning("No extracted records found for the latest pipeline run.")
        return

    st.subheader(f"Latest Data (Pipeline: {pipeline_id})")

    # Build pricing table
    rows = []
    for record in records:
        tiers = record.get("pricing_tiers", [])
        for tier in tiers:
            rows.append({
                "Company": record.get("company_name", ""),
                "Model/Tier": tier.get("model_or_tier_name", ""),
                "Input ($/1M)": tier.get("input_price_per_m_tokens"),
                "Output ($/1M)": tier.get("output_price_per_m_tokens"),
                "Cache Read ($/1M)": tier.get("cache_read_price_per_m_tokens"),
                "Context Window": tier.get("context_window_tokens"),
                "Confidence": f"{record.get('extraction_confidence', 0):.0%}",
            })

    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No pricing tiers found in the latest extraction.")


def render_run_pipeline():
    """Pipeline execution trigger."""
    st.title("⚙️ Run Pipeline")
    st.markdown("---")

    st.markdown("""
    Click the button below to trigger a full Scrybe intelligence pipeline run.
    This will:
    1. **Scrape** all configured competitor sources
    2. **Extract** structured pricing data with LLM verification
    3. **Detect** changes since the last run
    4. **Synthesize** strategic recommendations
    5. **Generate** a cited executive intelligence report
    """)

    config_path = st.text_input(
        "Sources config path (optional)",
        value="",
        help="Leave blank to use the default config/sources.yaml",
    )

    if st.button("🚀 Launch Pipeline Run", type="primary"):
        with st.spinner("Pipeline running... This may take a few minutes."):
            try:
                from scrybe.pipeline import Pipeline
                import asyncio

                pipeline = Pipeline()
                state = asyncio.run(pipeline.run(config_path or None))

                st.success(f"✅ Pipeline complete! ID: {pipeline.pipeline_id}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Sources Scraped", state.execution_metrics.get("sources_scraped", 0))
                with col2:
                    st.metric("Records Extracted", state.execution_metrics.get("records_extracted", 0))
                with col3:
                    st.metric("Deltas Detected", state.execution_metrics.get("deltas_detected", 0))

                if state.report_markdown:
                    st.subheader("Generated Report")
                    st.markdown(state.report_markdown[:3000])
                    if len(state.report_markdown) > 3000:
                        st.info("Report truncated. View full report in the Reports tab.")

            except Exception as e:
                st.error(f"Pipeline failed: {str(e)}")
                st.exception(e)


if __name__ == "__main__":
    main()
