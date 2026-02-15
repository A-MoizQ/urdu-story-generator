"""
Trigram Language Model module.

PLACEHOLDER — to be implemented by team member handling Phase III.

This module must expose the TrigramModel class with the following interface:
    - load(path: str)                           → loads a trained model from disk
    - predict_next(token1: int, token2: int)     → int  (sampled next token ID)
    - get_distribution(t1: int, t2: int)         → dict[int, float]  (full prob dist)
    - is_loaded                                  → bool (property)

Artifact format (expected at config.trigram_model_path):
    A JSON file with:
    {
        "trigram_counts": { "t1,t2,t3": count, ... },
        "bigram_counts":  { "t1,t2": count, ... },
        "unigram_counts": { "t1": count, ... },
        "lambdas": [lambda1, lambda2, lambda3],
        "vocab_size": 250
    }

The model uses deleted interpolation:
    P(t3 | t1, t2) = λ1 * P_ml(t3)
                    + λ2 * P_ml(t3 | t2)
                    + λ3 * P_ml(t3 | t1, t2)
"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path

logger = logging.getLogger(__name__)


class TrigramModel:
    """Interpolated Trigram Language Model for Urdu story generation."""

    def __init__(self) -> None:
        self._trigram_counts: dict[str, int] = {}
        self._bigram_counts: dict[str, int] = {}
        self._unigram_counts: dict[str, int] = {}
        self._lambdas: tuple[float, float, float] = (0.1, 0.3, 0.6)
        self._vocab_size: int = 0
        self._total_unigrams: int = 0
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def vocab_size(self) -> int:
        return self._vocab_size

    def load(self, path: str) -> None:
        """Load a trained trigram model from a JSON file."""
        filepath = Path(path)
        if not filepath.exists():
            logger.warning(
                "Model file not found at %s — running in STUB mode.", path
            )
            self._init_stub()
            return

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._trigram_counts = data["trigram_counts"]
        self._bigram_counts = data["bigram_counts"]
        self._unigram_counts = data["unigram_counts"]
        self._lambdas = tuple(data["lambdas"])
        self._vocab_size = data["vocab_size"]
        self._total_unigrams = sum(self._unigram_counts.values())
        self._loaded = True
        logger.info(
            "Trigram model loaded: vocab=%d, trigrams=%d, bigrams=%d, unigrams=%d",
            self._vocab_size,
            len(self._trigram_counts),
            len(self._bigram_counts),
            len(self._unigram_counts),
        )

    def get_distribution(
        self, token1: int, token2: int
    ) -> dict[int, float]:
        """Return the interpolated probability distribution P(· | token1, token2).

        TODO: Implement actual interpolation logic.
        Current stub returns uniform distribution.
        """
        if not self._loaded:
            logger.warning("Model not loaded — using stub distribution.")

        # ---------------------------------------------------------------
        # PLACEHOLDER: Replace with actual interpolated trigram logic.
        #
        # λ1 * P_unigram(t3) + λ2 * P_bigram(t3|t2) + λ3 * P_trigram(t3|t1,t2)
        #
        # Steps:
        #   1. Compute P_unigram(t3) = C(t3) / total_unigrams
        #   2. Compute P_bigram(t3|t2)  = C(t2,t3) / C(t2)
        #   3. Compute P_trigram(t3|t1,t2) = C(t1,t2,t3) / C(t1,t2)
        #   4. Interpolate with lambdas.
        #
        # For now, return uniform distribution so the pipeline works end-to-end.
        # ---------------------------------------------------------------
        vs = max(self._vocab_size, 1)
        return {i: 1.0 / vs for i in range(vs)}

    def predict_next(self, token1: int, token2: int) -> int:
        """Sample the next token from the interpolated distribution."""
        dist = self.get_distribution(token1, token2)
        tokens = list(dist.keys())
        weights = list(dist.values())
        return random.choices(tokens, weights=weights, k=1)[0]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _init_stub(self) -> None:
        """Initialize a minimal stub model for development/testing."""
        self._vocab_size = 40  # matches stub tokenizer char count
        self._total_unigrams = self._vocab_size
        self._unigram_counts = {str(i): 1 for i in range(self._vocab_size)}
        self._bigram_counts = {}
        self._trigram_counts = {}
        self._loaded = True
        logger.info("Stub trigram model initialized with vocab_size=%d.", self._vocab_size)
