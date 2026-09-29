"""Unit tests for Scrybe HTML extractor and JSON parser."""

import pytest
from scrybe.tools.extractor import clean_html_to_text, parse_llm_json_response, build_extraction_prompt
from scrybe.exceptions import ExtractionError


class TestCleanHtmlToText:
    """Tests for HTML → clean text stripping."""

    def test_strips_scripts_and_styles(self):
        html = '<html><script>var x=1;</script><style>.red{color:red}</style><p>Hello</p></html>'
        result = clean_html_to_text(html)
        assert "var x" not in result
        assert "color:red" not in result
        assert "Hello" in result

    def test_strips_nav_and_footer(self):
        html = '<nav><a href="/">Home</a></nav><main><p>Pricing: $5.00</p></main><footer>Copyright</footer>'
        result = clean_html_to_text(html)
        assert "Home" not in result
        assert "Copyright" not in result
        assert "$5.00" in result

    def test_preserves_table_content(self):
        html = '<table><tr><td>GPT-4o</td><td>$2.50</td></tr></table>'
        result = clean_html_to_text(html)
        assert "GPT-4o" in result
        assert "$2.50" in result

    def test_converts_headings(self):
        html = '<h1>API Pricing</h1><h2>Models</h2><p>Details</p>'
        result = clean_html_to_text(html)
        assert "API Pricing" in result
        assert "Models" in result

    def test_handles_empty_input(self):
        assert clean_html_to_text("") == ""

    def test_strips_html_comments(self):
        html = '<p>Visible</p><!-- Secret comment --><p>Also visible</p>'
        result = clean_html_to_text(html)
        assert "Visible" in result
        assert "Secret comment" not in result

    def test_decodes_html_entities(self):
        html = '<p>Tom &amp; Jerry &lt;3 &quot;fun&quot;</p>'
        result = clean_html_to_text(html)
        assert "Tom & Jerry" in result


class TestParseLlmJsonResponse:
    """Tests for LLM JSON response parsing."""

    def test_parses_clean_json(self):
        response = '{"company_name": "OpenAI", "confidence": 0.95}'
        result = parse_llm_json_response(response)
        assert result["company_name"] == "OpenAI"
        assert result["confidence"] == 0.95

    def test_parses_json_with_markdown_fences(self):
        response = '```json\n{"company_name": "Anthropic"}\n```'
        result = parse_llm_json_response(response)
        assert result["company_name"] == "Anthropic"

    def test_parses_json_with_surrounding_text(self):
        response = 'Here is the result:\n{"company_name": "Mistral"}\nDone.'
        result = parse_llm_json_response(response)
        assert result["company_name"] == "Mistral"

    def test_raises_on_invalid_json(self):
        with pytest.raises(ExtractionError, match="Failed to parse"):
            parse_llm_json_response("This is not JSON at all")

    def test_parses_nested_json(self):
        response = '{"tiers": [{"name": "Pro", "price": 20.0}]}'
        result = parse_llm_json_response(response)
        assert result["tiers"][0]["name"] == "Pro"


class TestBuildExtractionPrompt:
    """Tests for prompt template building."""

    def test_prompt_contains_source_url(self):
        prompt = build_extraction_prompt(
            markdown_content="GPT-4o costs $2.50 per 1M input tokens.",
            source_url="https://openai.com/api/pricing/",
        )
        assert "https://openai.com/api/pricing/" in prompt
        assert "GPT-4o" in prompt

    def test_prompt_contains_accuracy_rules(self):
        prompt = build_extraction_prompt(
            markdown_content="Test content",
            source_url="https://example.com",
        )
        assert "null" in prompt.lower() or "NULL" in prompt
        assert "ONLY extract" in prompt or "explicitly stated" in prompt
