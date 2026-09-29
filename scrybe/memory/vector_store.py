"""Scrybe FAISS Vector Store.

Stores dense embeddings of previous extraction records for:
1. Semantic delta detection (skip synthesis when content unchanged).
2. Historical record retrieval for trend analysis.
3. Deduplication of near-identical scrapes.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from scrybe.logging_config import get_agent_logger

logger = get_agent_logger("vector_store")

# FAISS is optional — degrade gracefully
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not installed — vector store features disabled. Install with: pip install faiss-cpu")


class VectorStore:
    """Lightweight FAISS-backed vector store for semantic delta detection.

    Stores embeddings alongside metadata (company, URL, timestamp).
    Supports cosine similarity search for finding near-duplicate extractions.
    """

    def __init__(
        self,
        index_path: Optional[str] = None,
        dimension: int = 384,
        similarity_threshold: float = 0.995,
    ):
        self.index_path = index_path
        self.dimension = dimension
        self.similarity_threshold = similarity_threshold
        self.metadata: List[Dict[str, Any]] = []  # Parallel metadata array
        self._index = None

        if FAISS_AVAILABLE:
            self._init_index()

    def _init_index(self) -> None:
        """Initialize or load the FAISS index."""
        if not FAISS_AVAILABLE:
            return

        if self.index_path and Path(self.index_path).exists():
            try:
                self._index = faiss.read_index(self.index_path)
                # Try to load metadata
                meta_path = self.index_path + ".meta.json"
                if Path(meta_path).exists():
                    with open(meta_path, "r") as f:
                        self.metadata = json.load(f)
                logger.info(f"Loaded FAISS index with {self._index.ntotal} vectors")
            except Exception as e:
                logger.warning(f"Failed to load FAISS index: {e}, creating new")
                self._index = faiss.IndexFlatIP(self.dimension)
        else:
            # Inner Product for cosine similarity (vectors must be L2-normalized)
            self._index = faiss.IndexFlatIP(self.dimension)

    def add(self, embedding: np.ndarray, metadata: Dict[str, Any]) -> None:
        """Add a vector with metadata to the index.

        Args:
            embedding: Dense vector (will be L2-normalized).
            metadata: Associated metadata (company_name, url, timestamp, etc.).
        """
        if not FAISS_AVAILABLE or self._index is None:
            return

        # L2 normalize for cosine similarity via inner product
        vec = embedding.astype(np.float32).reshape(1, -1)
        faiss.normalize_L2(vec)

        self._index.add(vec)
        self.metadata.append(metadata)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """Search for the most similar vectors.

        Args:
            query_embedding: The query vector.
            top_k: Number of results to return.

        Returns:
            List of (similarity_score, metadata) tuples, sorted by similarity desc.
        """
        if not FAISS_AVAILABLE or self._index is None or self._index.ntotal == 0:
            return []

        vec = query_embedding.astype(np.float32).reshape(1, -1)
        faiss.normalize_L2(vec)

        k = min(top_k, self._index.ntotal)
        distances, indices = self._index.search(vec, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                results.append((float(dist), self.metadata[idx]))
        return results

    def is_duplicate(self, embedding: np.ndarray, company_name: str = "") -> Tuple[bool, float]:
        """Check if a near-duplicate embedding already exists.

        Args:
            embedding: The embedding to check.
            company_name: Optional filter to match only same-company entries.

        Returns:
            Tuple of (is_duplicate, highest_similarity_score).
        """
        if not FAISS_AVAILABLE or self._index is None or self._index.ntotal == 0:
            return False, 0.0

        results = self.search(embedding, top_k=3)

        for score, meta in results:
            if company_name and meta.get("company_name") != company_name:
                continue
            if score >= self.similarity_threshold:
                logger.info(
                    f"Duplicate detected: similarity={score:.4f} >= {self.similarity_threshold} "
                    f"for {company_name}",
                    extra={"agent": "vector_store", "step": "dedup_check"},
                )
                return True, score

        best_score = results[0][0] if results else 0.0
        return False, best_score

    def save(self) -> None:
        """Persist the index and metadata to disk."""
        if not FAISS_AVAILABLE or self._index is None or not self.index_path:
            return

        Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, self.index_path)

        meta_path = self.index_path + ".meta.json"
        with open(meta_path, "w") as f:
            json.dump(self.metadata, f, default=str)

        logger.info(f"FAISS index saved: {self._index.ntotal} vectors")

    @property
    def size(self) -> int:
        if self._index is not None:
            return self._index.ntotal
        return 0


def text_to_embedding_simple(text: str, dimension: int = 384) -> np.ndarray:
    """Generate a simple deterministic embedding from text using hashing.

    This is a fallback when no embedding model is available.
    For production, replace with a proper embedding model
    (e.g., sentence-transformers all-MiniLM-L6-v2 or OpenAI text-embedding-3-small).

    Args:
        text: Input text to embed.
        dimension: Output vector dimension.

    Returns:
        Normalized numpy array of shape (dimension,).
    """
    # Use SHA-512 repeatedly to fill the dimension
    hashes = []
    current = text.encode("utf-8")
    while len(hashes) * 64 < dimension * 4:  # 4 bytes per float32
        h = hashlib.sha512(current).digest()
        hashes.append(h)
        current = h

    raw_bytes = b"".join(hashes)[: dimension * 4]
    vec = np.frombuffer(raw_bytes, dtype=np.float32)[:dimension].copy()

    # L2 normalize
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec
