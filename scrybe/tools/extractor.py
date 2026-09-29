"""Scrybe HTML → Clean Markdown Extractor.

Strips scripts, styles, SVG, navigation, footers, and tracking pixels,
preserving semantic structure (tables, headings, lists, paragraphs).
Then invokes an LLM to extract structured JSON conforming to
CompetitorProductRecord.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

from scrybe.exceptions import ExtractionError, LLMError
from scrybe.logging_config import get_agent_logger

logger = get_agent_logger("extractor")

# ── HTML → Clean Text Stripping ──

# Tags whose entire content (including children) should be removed
STRIP_TAGS_WITH_CONTENT = re.compile(
    r"<\s*(script|style|svg|noscript|iframe|object|embed)[^>]*>.*?</\s*\1\s*>",
    re.DOTALL | re.IGNORECASE,
)

# Navigation and footer wrappers
STRIP_NAV_FOOTER = re.compile(
    r"<\s*(nav|footer|header|aside)[^>]*>.*?</\s*\1\s*>",
    re.DOTALL | re.IGNORECASE,
)

# HTML comments
STRIP_COMMENTS = re.compile(r"<!--.*?-->", re.DOTALL)

# Generic tags (keep content)
STRIP_TAGS = re.compile(r"<[^>]+>")

# Collapse whitespace
COLLAPSE_WHITESPACE = re.compile(r"\n{3,}")
COLLAPSE_SPACES = re.compile(r"[ \t]{2,}")


def clean_html_to_text(raw_html: str) -> str:
    """Strip HTML boilerplate and return clean, token-efficient text.

    Preserves table content, headings, and list items as plain text.
    Strips scripts, styles, navigation, SVGs, and tracking pixels.

    Args:
        raw_html: Raw HTML string from a scraped page.

    Returns:
        Cleaned text suitable for LLM extraction prompts.
    """
    text = raw_html

    # Remove script/style/svg blocks entirely
    text = STRIP_TAGS_WITH_CONTENT.sub("", text)

    # Remove nav/footer/header/aside blocks
    text = STRIP_NAV_FOOTER.sub("", text)

    # Remove HTML comments
    text = STRIP_COMMENTS.sub("", text)

    # Convert some semantic HTML to text markers
    text = re.sub(r"<h([1-6])[^>]*>", r"\n### ", text, flags=re.IGNORECASE)
    text = re.sub(r"</h[1-6]>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "\n• ", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<tr[^>]*>", "\n| ", text, flags=re.IGNORECASE)
    text = re.sub(r"<t[dh][^>]*>", " | ", text, flags=re.IGNORECASE)
    text = re.sub(r"<p[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)

    # Strip remaining HTML tags
    text = STRIP_TAGS.sub("", text)

    # Decode common HTML entities
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&nbsp;", " ")
    text = text.replace("&#39;", "'")
    text = text.replace("&quot;", '"')
    text = text.replace("&mdash;", "—")
    text = text.replace("&ndash;", "–")

    # Collapse excessive whitespace
    text = COLLAPSE_SPACES.sub(" ", text)
    text = COLLAPSE_WHITESPACE.sub("\n\n", text)

    return text.strip()


def build_extraction_prompt(
    markdown_content: str,
    source_url: str,
    prompt_template_path: Optional[str] = None,
) -> str:
    """Build the LLM extraction prompt by loading the template and filling in variables.

    Args:
        markdown_content: Cleaned text from the scraped page.
        source_url: The URL the content was scraped from.
        prompt_template_path: Optional override path to the prompt template.

    Returns:
        The formatted prompt string ready for LLM invocation.
    """
    if prompt_template_path:
        template = Path(prompt_template_path).read_text(encoding="utf-8")
    else:
        default_path = Path(__file__).resolve().parent.parent / "agents" / "prompts" / "analyst_extract.txt"
        template = default_path.read_text(encoding="utf-8")

    return template.format(source_url=source_url, markdown_content=markdown_content)


def parse_llm_json_response(raw_response: str) -> Dict[str, Any]:
    """Parse and extract JSON from an LLM response that may contain markdown fences.

    Args:
        raw_response: Raw text output from the LLM.

    Returns:
        Parsed dictionary.

    Raises:
        ExtractionError: If JSON parsing fails.
    """
    text = raw_response.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        # Remove opening fence (with optional language specifier)
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)

    # Try to find JSON object boundaries
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ExtractionError(f"Failed to parse LLM JSON response: {e}\nRaw: {raw_response[:500]}")
