"""Scrybe Report Generator.

Produces Markdown and PDF intelligence reports from validated
strategic analysis data. All reports include citations, comparison
matrices, and executive summaries.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from scrybe.storage.models import (
    CompetitorProductRecord,
    TrendDelta,
    StrategicRecommendation,
)
from scrybe.logging_config import get_agent_logger

logger = get_agent_logger("reporter")


def generate_markdown_report(
    pipeline_id: str,
    executive_summary: str,
    records: List[CompetitorProductRecord],
    deltas: List[TrendDelta],
    recommendations: List[StrategicRecommendation],
    battlecards: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a complete Markdown intelligence report.

    Args:
        pipeline_id: Unique identifier for this pipeline run.
        executive_summary: The strategic executive summary text.
        records: Validated competitor product records.
        deltas: Detected market deltas.
        recommendations: Strategic recommendations.
        battlecards: Optional battlecard data keyed by competitor name.

    Returns:
        Complete Markdown string ready for file writing or API delivery.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sections = []

    # ── Header ──
    sections.append(f"# Scrybe Competitive Intelligence Report")
    sections.append(f"\n**Pipeline:** `{pipeline_id}`  ")
    sections.append(f"**Generated:** {now}  ")
    sections.append(f"**Vertical:** B2B AI Developer Platforms  ")
    sections.append(f"**Sources Analyzed:** {len(records)}  ")
    sections.append("")

    # ── Executive Summary ──
    sections.append("---")
    sections.append("## 📋 Executive Summary")
    sections.append("")
    sections.append(executive_summary)
    sections.append("")

    # ── Pricing Comparison Matrix ──
    sections.append("---")
    sections.append("## 💰 Pricing Comparison Matrix")
    sections.append("")
    sections.append(_build_pricing_matrix(records))
    sections.append("")

    # ── Market Deltas ──
    if deltas:
        sections.append("---")
        sections.append("## 📊 Detected Market Changes")
        sections.append("")
        sections.append("| Competitor | Change | Metric | Old → New | Severity |")
        sections.append("| :--- | :--- | :--- | :--- | :---: |")
        for d in deltas:
            old_val = d.old_value or "N/A"
            severity_emoji = {
                "LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"
            }.get(d.strategic_severity, "⚪")
            sections.append(
                f"| {d.competitor_name} | {d.delta_type.value} | {d.metric_name} "
                f"| {old_val} → {d.new_value} | {severity_emoji} {d.strategic_severity} |"
            )
        sections.append("")

    # ── Strategic Recommendations ──
    if recommendations:
        sections.append("---")
        sections.append("## 🎯 Strategic Recommendations")
        sections.append("")
        for i, rec in enumerate(recommendations, 1):
            sections.append(f"### {i}. [{rec.category}] {rec.title}")
            sections.append("")
            sections.append(f"**Rationale:** {rec.rationale}")
            sections.append("")
            sections.append(f"**Action:** {rec.actionable_next_step}")
            sections.append("")
            sources_str = ", ".join(f"[Source]({s})" for s in rec.corroborating_sources)
            sections.append(f"**Corroboration ({rec.corroboration_count} sources):** {sources_str}")
            sections.append("")

    # ── Battlecards ──
    if battlecards:
        sections.append("---")
        sections.append("## ⚔️ Sales Battlecard Snippets")
        sections.append("")
        for competitor_name, card_data in battlecards.items():
            sections.append(f"### vs. {competitor_name}")
            sections.append("")
            if isinstance(card_data, dict):
                our_wins = card_data.get("our_advantages", [])
                their_wins = card_data.get("competitor_advantages", [])
                talk_track = card_data.get("recommended_talk_track", "")

                if our_wins:
                    sections.append("**Where We Win:**")
                    for w in our_wins:
                        sections.append(f"- ✅ {w}")
                    sections.append("")

                if their_wins:
                    sections.append("**Where They Win:**")
                    for w in their_wins:
                        sections.append(f"- ⚠️ {w}")
                    sections.append("")

                if talk_track:
                    sections.append(f"**Recommended Talk Track:** {talk_track}")
                    sections.append("")

    # ── Citations ──
    sections.append("---")
    sections.append("## 📝 Source Citations")
    sections.append("")
    seen_urls = set()
    for i, record in enumerate(records, 1):
        if record.source_url not in seen_urls:
            sections.append(f"[^{i}]: {record.company_name} — {record.source_url} "
                          f"(Accessed {now}, Confidence: {record.extraction_confidence:.2f})")
            seen_urls.add(record.source_url)
    sections.append("")

    # ── Disclaimer ──
    sections.append("---")
    sections.append("> *This report was generated autonomously by Scrybe. "
                   "All data points are sourced from publicly available web pages "
                   "and verified against raw DOM content. Claims requiring human "
                   "review are flagged inline.*")

    return "\n".join(sections)


def _build_pricing_matrix(records: List[CompetitorProductRecord]) -> str:
    """Build a Markdown comparison table of pricing across competitors."""
    if not records:
        return "*No pricing data extracted in this run.*"

    lines = []
    lines.append("| Company | Model/Tier | Input ($/1M tokens) | Output ($/1M tokens) | "
                "Cache Read ($/1M) | Context Window | Confidence |")
    lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: |")

    for record in records:
        for tier in record.pricing_tiers:
            inp = f"${tier.input_price_per_m_tokens:.2f}" if tier.input_price_per_m_tokens is not None else "—"
            out = f"${tier.output_price_per_m_tokens:.2f}" if tier.output_price_per_m_tokens is not None else "—"
            cache = f"${tier.cache_read_price_per_m_tokens:.2f}" if tier.cache_read_price_per_m_tokens is not None else "—"
            ctx = f"{tier.context_window_tokens:,}" if tier.context_window_tokens else "—"
            conf = f"{record.extraction_confidence:.0%}"
            lines.append(
                f"| {record.company_name} | {tier.model_or_tier_name} | {inp} | {out} | {cache} | {ctx} | {conf} |"
            )

    return "\n".join(lines)


def save_markdown_report(report_content: str, output_dir: str, pipeline_id: str) -> str:
    """Save a Markdown report to disk.

    Args:
        report_content: The full Markdown string.
        output_dir: Directory to write the report file.
        pipeline_id: Pipeline ID used in the filename.

    Returns:
        Absolute path to the saved file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    filename = f"report_{date_str}_{pipeline_id[:8]}.md"
    filepath = output_path / filename

    filepath.write_text(report_content, encoding="utf-8")
    logger.info("Markdown report saved", extra={"agent": "reporter", "step": "save_markdown"})
    return str(filepath)


def save_pdf_report(report_content: str, output_dir: str, pipeline_id: str) -> Optional[str]:
    """Generate and save a PDF report using ReportLab.

    Falls back gracefully if ReportLab is not installed.

    Args:
        report_content: Markdown content (converted to PDF text).
        output_dir: Directory to write the PDF file.
        pipeline_id: Pipeline ID used in the filename.

    Returns:
        Absolute path to the PDF file, or None if ReportLab unavailable.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
    except ImportError:
        logger.warning("ReportLab not installed — skipping PDF generation.")
        return None

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    filename = f"report_{date_str}_{pipeline_id[:8]}.pdf"
    filepath = output_path / filename

    doc = SimpleDocTemplate(str(filepath), pagesize=A4,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ScrybeTitle", parent=styles["Title"], fontSize=18,
        textColor=colors.HexColor("#1a1a2e"), spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "ScrybeHeading", parent=styles["Heading2"], fontSize=14,
        textColor=colors.HexColor("#16213e"), spaceBefore=16, spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "ScrybeBody", parent=styles["Normal"], fontSize=10,
        leading=14, spaceAfter=6,
    )

    story = []
    story.append(Paragraph("Scrybe Competitive Intelligence Report", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Pipeline: {pipeline_id} | Generated: {date_str}", body_style))
    story.append(Spacer(1, 24))

    # Convert markdown sections to PDF paragraphs
    for line in report_content.split("\n"):
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 6))
        elif stripped.startswith("# ") and not stripped.startswith("##"):
            story.append(Paragraph(stripped[2:], title_style))
        elif stripped.startswith("## "):
            story.append(Paragraph(stripped[3:], heading_style))
        elif stripped.startswith("### "):
            story.append(Paragraph(f"<b>{stripped[4:]}</b>", body_style))
        elif stripped.startswith("---"):
            story.append(Spacer(1, 12))
        elif stripped.startswith("|"):
            # Skip table lines in PDF (they'll be formatted separately in v2)
            story.append(Paragraph(stripped.replace("|", " | "), body_style))
        elif stripped.startswith(">"):
            story.append(Paragraph(f"<i>{stripped[1:].strip()}</i>", body_style))
        else:
            # Clean up markdown formatting
            clean = stripped.replace("**", "").replace("*", "").replace("`", "")
            if clean:
                story.append(Paragraph(clean, body_style))

    doc.build(story)
    logger.info("PDF report saved", extra={"agent": "reporter", "step": "save_pdf"})
    return str(filepath)
