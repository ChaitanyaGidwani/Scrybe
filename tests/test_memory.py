"""Unit tests for Scrybe memory subsystems (buffer, reflexion, vector store)."""

import pytest
import numpy as np
from scrybe.memory.buffer import RollingBuffer
from scrybe.memory.reflection import ReflexionLoop, build_reflexion_prompt
from scrybe.memory.vector_store import text_to_embedding_simple, VectorStore


class TestRollingBuffer:
    """Tests for the rolling action buffer."""

    def test_records_and_retrieves_actions(self):
        buffer = RollingBuffer(max_size=5)
        buffer.record(agent="reader", action="scraped_openai", status="OK")
        buffer.record(agent="analyst", action="extracted_data", status="OK")

        recent = buffer.get_recent(5)
        assert len(recent) == 2
        assert recent[0]["agent"] == "reader"
        assert recent[1]["agent"] == "analyst"

    def test_rolling_eviction(self):
        buffer = RollingBuffer(max_size=3)
        buffer.record(agent="a1", action="act1")
        buffer.record(agent="a2", action="act2")
        buffer.record(agent="a3", action="act3")
        buffer.record(agent="a4", action="act4")  # Should evict act1

        recent = buffer.get_recent(5)
        assert len(recent) == 3
        assert recent[0]["agent"] == "a2"  # act1 was evicted

    def test_error_filtering(self):
        buffer = RollingBuffer()
        buffer.record(agent="reader", action="scraped", status="OK")
        buffer.record(agent="analyst", action="failed", status="ERROR", error="Parse error")
        buffer.record(agent="reader", action="scraped2", status="OK")

        errors = buffer.get_recent_errors()
        assert len(errors) == 1
        assert errors[0]["error"] == "Parse error"

    def test_context_string_generation(self):
        buffer = RollingBuffer()
        buffer.record(agent="reader", action="scraped", status="OK", source_url="https://openai.com")
        context = buffer.get_context_string()
        assert "reader" in context
        assert "openai.com" in context

    def test_empty_buffer(self):
        buffer = RollingBuffer()
        assert buffer.size == 0
        assert buffer.get_recent() == []
        assert "No recent actions" in buffer.get_context_string()


class TestReflexionLoop:
    """Tests for the Reflexion self-correction loop."""

    def test_retry_counting(self):
        loop = ReflexionLoop(max_retries=2)
        assert loop.should_retry()

        loop.record_attempt("analyst", "Error 1")
        assert loop.should_retry()

        loop.record_attempt("analyst", "Error 2")
        assert not loop.should_retry()  # Max retries exhausted

    def test_history_summary(self):
        loop = ReflexionLoop(max_retries=3)
        loop.record_attempt("analyst", "Parse error", {"root_cause": "INVALID_JSON", "remedy": "Fix braces"})
        summary = loop.get_history_summary()
        assert "INVALID_JSON" in summary
        assert "Fix braces" in summary

    def test_prompt_generation(self):
        prompt = build_reflexion_prompt(
            agent_name="analyst",
            input_excerpt="Some extracted text...",
            error_trace="ValidationError: field required",
        )
        assert "analyst" in prompt
        assert "ValidationError" in prompt


class TestVectorStore:
    """Tests for FAISS-based vector store (using fallback hash embeddings)."""

    def test_hash_embedding_generation(self):
        emb = text_to_embedding_simple("OpenAI GPT-4o pricing", dimension=384)
        assert emb.shape == (384,)
        # Should be L2-normalized
        norm = np.linalg.norm(emb)
        assert abs(norm - 1.0) < 0.01

    def test_deterministic_embedding(self):
        emb1 = text_to_embedding_simple("Same text", dimension=128)
        emb2 = text_to_embedding_simple("Same text", dimension=128)
        np.testing.assert_array_equal(emb1, emb2)

    def test_different_texts_different_embeddings(self):
        emb1 = text_to_embedding_simple("OpenAI pricing", dimension=128)
        emb2 = text_to_embedding_simple("Anthropic pricing", dimension=128)
        # They should not be identical
        assert not np.array_equal(emb1, emb2)
