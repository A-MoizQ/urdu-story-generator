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

import math
import json
import logging
import random
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


class TrigramModel:
    """Interpolated Trigram Language Model for Urdu story generation."""

    def __init__(self, vocab_size: int = 250) -> None:
        # Internal counts using tuples for fast lookup (t1, t2, t3)
        self._trigram_counts: dict[tuple[int, int, int], int] = defaultdict(int)
        self._bigram_counts: dict[tuple[int, int], int] = defaultdict(int)
        self._unigram_counts: dict[int, int] = defaultdict(int)
        
        self._lambdas: tuple[float, float, float] = (0.1, 0.3, 0.6)
        self._vocab_size: int = vocab_size
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

        # Parse JSON string keys back to fast tuple/int keys
        self._unigram_counts = defaultdict(int, {int(k): v for k, v in data["unigram_counts"].items()})
        
        self._bigram_counts = defaultdict(int)
        for k, v in data["bigram_counts"].items():
            self._bigram_counts[tuple(map(int, k.split(',')))] = v
            
        self._trigram_counts = defaultdict(int)
        for k, v in data["trigram_counts"].items():
            self._trigram_counts[tuple(map(int, k.split(',')))] = v

        self._lambdas = tuple(data["lambdas"])
        self._vocab_size = data.get("vocab_size", len(self._unigram_counts))
        self._total_unigrams = sum(self._unigram_counts.values())
        
        self._loaded = True
        logger.info(
            "Trigram model loaded: vocab=%d, trigrams=%d, bigrams=%d, unigrams=%d",
            self._vocab_size,
            len(self._trigram_counts),
            len(self._bigram_counts),
            len(self._unigram_counts),
        )

    def get_distribution(self, token1: int, token2: int) -> dict[int, float]:
        """Return the interpolated probability distribution P(· | token1, token2)."""
        if not self._loaded:
            logger.warning("Model not loaded — using stub distribution.")
            vs = max(self._vocab_size, 1)
            return {i: 1.0 / vs for i in range(vs)}

        distribution = {}
        known_vocab = list(self._unigram_counts.keys())
        
        l1, l2, l3 = self._lambdas
        
        for w in known_vocab:
            # 1. Unigram: P(w)
            p_uni = self._unigram_counts[w] / self._total_unigrams if self._total_unigrams > 0 else 0
            
            # 2. Bigram: P(w | t2)
            count_t2 = self._unigram_counts[token2]
            p_bi = self._bigram_counts[(token2, w)] / count_t2 if count_t2 > 0 else 0
            
            # 3. Trigram: P(w | t1, t2)
            count_t1_t2 = self._bigram_counts[(token1, token2)]
            p_tri = self._trigram_counts[(token1, token2, w)] / count_t1_t2 if count_t1_t2 > 0 else 0
            
            # Linear Interpolation
            prob = (l1 * p_uni) + (l2 * p_bi) + (l3 * p_tri)
                   
            if prob > 0:
                distribution[w] = prob

        return distribution

    def predict_next(self, token1: int, token2: int, top_k: int = 10, temperature: float = 1.0) -> int:
        """Sample the next token from the interpolated distribution with Top-K and Temperature."""
        dist = self.get_distribution(token1, token2)
        
        if not dist:
            # Fallback if no distribution is found
            return random.choice(list(self._unigram_counts.keys()))

        # Apply Temperature Scaling: p = p^(1/T)
        if temperature != 1.0:
            for token_id in dist:
                dist[token_id] = math.pow(dist[token_id], 1.0 / temperature)

        # Normalize & Top-K Filtering
        sorted_dist = sorted(dist.items(), key=lambda x: x[1], reverse=True)
        top_k_dist = sorted_dist[:top_k]
        
        candidates = [item[0] for item in top_k_dist]
        weights = [item[1] for item in top_k_dist]
        
        sum_weights = sum(weights)
        if sum_weights > 0:
            weights = [w / sum_weights for w in weights]
            return random.choices(candidates, weights=weights, k=1)[0]
        
        return random.choice(candidates)
    
    # ------------------------------------------------------------------
    # Training & Saving (Phase II Logic)
    # ------------------------------------------------------------------

    def train(self, tokenized_text: list[int]) -> None:
        """Populates the n-gram counts from the provided tokenized text."""
        self._total_unigrams += len(tokenized_text)

        for token in tokenized_text:
            self._unigram_counts[token] += 1

        for i in range(1, len(tokenized_text)):
            bigram = (tokenized_text[i-1], tokenized_text[i])
            self._bigram_counts[bigram] += 1

        for i in range(2, len(tokenized_text)):
            trigram = (tokenized_text[i-2], tokenized_text[i-1], tokenized_text[i])
            self._trigram_counts[trigram] += 1
            
        self._vocab_size = len(self._unigram_counts)
        self._loaded = True

    def deleted_interpolation(self) -> None:
        """Calculates optimal lambdas using the Deleted Interpolation algorithm."""
        v1 = v2 = v3 = 0
        N = self._total_unigrams

        for trigram, count in self._trigram_counts.items():
            if count == 0: continue
            
            w1, w2, w3 = trigram
            
            c123 = self._trigram_counts[(w1, w2, w3)]
            c12  = self._bigram_counts[(w1, w2)]
            weight3 = (c123 - 1) / (c12 - 1) if c12 > 1 else 0

            c23 = self._bigram_counts[(w2, w3)]
            c2  = self._unigram_counts[w2]
            weight2 = (c23 - 1) / (c2 - 1) if c2 > 1 else 0

            c3 = self._unigram_counts[w3]
            weight1 = (c3 - 1) / (N - 1) if N > 1 else 0

            max_w = max(weight1, weight2, weight3)
            
            if max_w == weight3:
                v3 += count
            elif max_w == weight2:
                v2 += count
            else:
                v1 += count

        total_v = v1 + v2 + v3
        if total_v > 0:
            self._lambdas = (v1 / total_v, v2 / total_v, v3 / total_v)
        
        logger.info("Deleted Interpolation optimized lambdas to: %s", self._lambdas)

    def save(self, path: str = "backend/models/trigram_model.json") -> None:
        """Saves the model to match the required team JSON schema."""
        data = {
            "trigram_counts": {f"{k[0]},{k[1]},{k[2]}": v for k, v in self._trigram_counts.items()},
            "bigram_counts": {f"{k[0]},{k[1]}": v for k, v in self._bigram_counts.items()},
            "unigram_counts": {str(k): v for k, v in self._unigram_counts.items()},
            "lambdas": self._lambdas,
            "vocab_size": self._vocab_size
        }
        
        # Ensure directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

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
