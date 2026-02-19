"""
Trigram Language Model module.

This module exposes the TrigramModel class with the following interface:
    - load(path: str)                           → loads a trained model from disk
    - predict_next(token1: int, token2: int)     → int  (sampled next token ID)
    - get_distribution(t1: int, t2: int)         → dict[int, float]  (full prob dist)
    - is_loaded                                  → bool (property)

Artifact format (runtime — produced by scripts/convert_model_to_sqlite.py):
    An SQLite database file (trigram_model.db) with tables:
        unigrams(t1, count)
        bigrams(t1, t2, count)
        trigrams(t1, t2, t3, count)
        metadata(key, value)   — stores lambdas, vocab_size, total_tokens

Fallback: if a .db file is not found but a .json file exists at the same path
    (with extension replaced), the model loads from JSON.  This keeps
    local development working without running the conversion script first.

The model uses deleted interpolation:
    P(t3 | t1, t2) = λ1 * P_ml(t3)
                    + λ2 * P_ml(t3 | t2)
                    + λ3 * P_ml(t3 | t1, t2)
"""

from __future__ import annotations

import json
import logging
import math
import random
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TrigramModel:
    """Interpolated Trigram Language Model for Urdu story generation."""

    def __init__(self, vocab_size: int = 250) -> None:
        self._vocab_size: int = vocab_size
        self._lambdas: tuple[float, float, float] = (0.1, 0.3, 0.6)
        self._total_unigrams: int = 0
        self._loaded: bool = False

        # SQLite connection — set by load() when using .db file
        self._conn: Optional[sqlite3.Connection] = None

        # In-memory fallback (used only when JSON is loaded directly)
        self._trigram_counts: dict[tuple[int, int, int], int] = defaultdict(int)
        self._bigram_counts:  dict[tuple[int, int], int]      = defaultdict(int)
        self._unigram_counts: dict[int, int]                  = defaultdict(int)
        self._use_sqlite: bool = False

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
        """Load a trained trigram model.

        Tries .db (SQLite, low RAM) first; falls back to .json; else stub.
        """
        db_path = Path(path).with_suffix(".db")

        if db_path.exists():
            self._load_sqlite(db_path)
        elif Path(path).exists():
            logger.warning(
                "SQLite artifact %s not found; falling back to JSON %s. "
                "RAM usage will be high — run scripts/convert_model_to_sqlite.py.",
                db_path, path,
            )
            self._load_json(Path(path))
        else:
            logger.warning(
                "Model file not found at %s (or %s) — running in STUB mode.",
                path, db_path,
            )
            self._init_stub()

    def get_distribution(self, token1: int, token2: int) -> dict[int, float]:
        """Return the interpolated probability distribution P(· | token1, token2)."""
        if not self._loaded:
            logger.warning("Model not loaded — using stub distribution.")
            vs = max(self._vocab_size, 1)
            return {i: 1.0 / vs for i in range(vs)}

        if self._use_sqlite:
            return self._get_distribution_sqlite(token1, token2)
        return self._get_distribution_memory(token1, token2)

    def predict_next(
        self,
        token1: int,
        token2: int,
        top_k: int = 10,
        temperature: float = 1.0,
    ) -> int:
        """Sample the next token from the interpolated distribution."""
        dist = self.get_distribution(token1, token2)

        if not dist:
            if self._use_sqlite and self._conn is not None:
                row = self._conn.execute(
                    "SELECT t1 FROM unigrams ORDER BY RANDOM() LIMIT 1"
                ).fetchone()
                return row[0] if row else 0
            return random.choice(list(self._unigram_counts.keys()) or [0])

        # Temperature scaling
        if temperature != 1.0:
            dist = {tid: math.pow(p, 1.0 / temperature) for tid, p in dist.items()}

        # Top-K + normalise
        sorted_dist = sorted(dist.items(), key=lambda x: x[1], reverse=True)
        top_k_dist  = sorted_dist[:top_k]
        candidates  = [item[0] for item in top_k_dist]
        weights     = [item[1] for item in top_k_dist]

        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]
            return random.choices(candidates, weights=weights, k=1)[0]

        return random.choice(candidates)

    # ------------------------------------------------------------------
    # SQLite backend
    # ------------------------------------------------------------------

    def _load_sqlite(self, db_path: Path) -> None:
        """Open SQLite DB — does NOT load data into RAM."""
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA cache_size   = -8192")   # 8 MB page cache
        self._conn.execute("PRAGMA temp_store   = MEMORY")

        meta = dict(self._conn.execute("SELECT key, value FROM metadata").fetchall())
        self._lambdas        = tuple(json.loads(meta["lambdas"]))  # type: ignore[assignment]
        self._vocab_size     = int(meta["vocab_size"])
        self._total_unigrams = int(meta["total_tokens"])
        self._use_sqlite     = True
        self._loaded         = True

        # Cache unigram counts — only ~249 rows, negligible RAM
        rows = self._conn.execute("SELECT t1, count FROM unigrams").fetchall()
        self._unigram_counts = dict(rows)

        logger.info(
            "Trigram model loaded from SQLite: vocab=%d, lambdas=%s, db=%s",
            self._vocab_size, self._lambdas, db_path,
        )

    def _get_distribution_sqlite(self, token1: int, token2: int) -> dict[int, float]:
        """Compute interpolated P(· | t1, t2) using on-demand SQL queries."""
        assert self._conn is not None
        l1, l2, l3 = self._lambdas

        row = self._conn.execute(
            "SELECT count FROM bigrams WHERE t1=? AND t2=?", (token1, token2)
        ).fetchone()
        count_t1_t2 = row[0] if row else 0

        trigram_rows = self._conn.execute(
            "SELECT t3, count FROM trigrams WHERE t1=? AND t2=?", (token1, token2)
        ).fetchall()
        trigram_map = {t3: cnt for t3, cnt in trigram_rows}

        bigram_rows = self._conn.execute(
            "SELECT t2, count FROM bigrams WHERE t1=?", (token2,)
        ).fetchall()
        bigram_map = {t2: cnt for t2, cnt in bigram_rows}
        count_t2   = self._unigram_counts.get(token2, 0)

        distribution: dict[int, float] = {}
        for w, uc in self._unigram_counts.items():
            p_uni = uc / self._total_unigrams if self._total_unigrams > 0 else 0
            p_bi  = bigram_map.get(w, 0) / count_t2 if count_t2 > 0 else 0
            p_tri = trigram_map.get(w, 0) / count_t1_t2 if count_t1_t2 > 0 else 0
            prob  = l1 * p_uni + l2 * p_bi + l3 * p_tri
            if prob > 0:
                distribution[w] = prob

        return distribution

    # ------------------------------------------------------------------
    # In-memory backend (JSON fallback)
    # ------------------------------------------------------------------

    def _load_json(self, filepath: Path) -> None:
        """Load the full JSON into Python dicts (high RAM — fallback only)."""
        logger.info("Loading JSON model into RAM from %s …", filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._unigram_counts = defaultdict(
            int, {int(k): v for k, v in data["unigram_counts"].items()}
        )
        self._bigram_counts = defaultdict(int)
        for k, v in data["bigram_counts"].items():
            t1, t2 = map(int, k.split(","))
            self._bigram_counts[(t1, t2)] = v

        self._trigram_counts = defaultdict(int)
        for k, v in data["trigram_counts"].items():
            t1, t2, t3 = map(int, k.split(","))
            self._trigram_counts[(t1, t2, t3)] = v

        self._lambdas        = tuple(data["lambdas"])  # type: ignore[assignment]
        self._vocab_size     = data.get("vocab_size", len(self._unigram_counts))
        self._total_unigrams = sum(self._unigram_counts.values())
        self._use_sqlite     = False
        self._loaded         = True

        logger.info(
            "Trigram model loaded from JSON: vocab=%d, trigrams=%d, bigrams=%d",
            self._vocab_size, len(self._trigram_counts), len(self._bigram_counts),
        )

    def _get_distribution_memory(self, token1: int, token2: int) -> dict[int, float]:
        """Compute interpolated P(· | t1, t2) from in-memory dicts."""
        l1, l2, l3 = self._lambdas
        distribution: dict[int, float] = {}

        for w in self._unigram_counts:
            p_uni = self._unigram_counts[w] / self._total_unigrams if self._total_unigrams > 0 else 0

            count_t2 = self._unigram_counts.get(token2, 0)
            p_bi     = self._bigram_counts.get((token2, w), 0) / count_t2 if count_t2 > 0 else 0

            count_t1_t2 = self._bigram_counts.get((token1, token2), 0)
            p_tri       = self._trigram_counts.get((token1, token2, w), 0) / count_t1_t2 if count_t1_t2 > 0 else 0

            prob = l1 * p_uni + l2 * p_bi + l3 * p_tri
            if prob > 0:
                distribution[w] = prob

        return distribution

    # ------------------------------------------------------------------
    # Training & Saving (used by training pipeline — not inference)
    # ------------------------------------------------------------------

    def train(self, tokenized_text: list[int]) -> None:
        """Populate n-gram counts from tokenized text."""
        self._total_unigrams += len(tokenized_text)

        for token in tokenized_text:
            self._unigram_counts[token] += 1

        for i in range(1, len(tokenized_text)):
            self._bigram_counts[(tokenized_text[i - 1], tokenized_text[i])] += 1

        for i in range(2, len(tokenized_text)):
            self._trigram_counts[
                (tokenized_text[i - 2], tokenized_text[i - 1], tokenized_text[i])
            ] += 1

        self._vocab_size = len(self._unigram_counts)
        self._loaded = True

    def deleted_interpolation(self) -> None:
        """Calculate optimal lambdas using Deleted Interpolation."""
        v1 = v2 = v3 = 0
        N = self._total_unigrams

        for trigram, count in self._trigram_counts.items():
            if count == 0:
                continue
            w1, w2, w3 = trigram

            c123    = self._trigram_counts[(w1, w2, w3)]
            c12     = self._bigram_counts[(w1, w2)]
            weight3 = (c123 - 1) / (c12 - 1) if c12 > 1 else 0

            c23     = self._bigram_counts[(w2, w3)]
            c2      = self._unigram_counts[w2]
            weight2 = (c23 - 1) / (c2 - 1) if c2 > 1 else 0

            c3      = self._unigram_counts[w3]
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

        logger.info("Deleted Interpolation lambdas: %s", self._lambdas)

    def save(self, path: str = "backend/models/trigram_model.json") -> None:
        """Save model to JSON (team schema — used by training pipeline)."""
        data = {
            "trigram_counts": {
                f"{k[0]},{k[1]},{k[2]}": v for k, v in self._trigram_counts.items()
            },
            "bigram_counts": {
                f"{k[0]},{k[1]}": v for k, v in self._bigram_counts.items()
            },
            "unigram_counts": {str(k): v for k, v in self._unigram_counts.items()},
            "lambdas":    list(self._lambdas),
            "vocab_size": self._vocab_size,
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _init_stub(self) -> None:
        """Minimal stub model for CI / unit tests when no artifact is present."""
        self._vocab_size     = 40
        self._total_unigrams = 40
        self._unigram_counts = {i: 1 for i in range(self._vocab_size)}
        self._bigram_counts  = defaultdict(int)
        self._trigram_counts = defaultdict(int)
        self._use_sqlite     = False
        self._loaded         = True
        logger.info("Stub trigram model initialised with vocab_size=%d.", self._vocab_size)
