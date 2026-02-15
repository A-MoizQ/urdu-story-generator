"""
BPE Tokenizer module.

PLACEHOLDER — to be implemented by team member handling Phase II.

This module must expose the BPETokenizer class with the following interface:
    - load(path: str)           → loads a trained tokenizer from disk
    - encode(text: str)         → list[int]   (token IDs)
    - decode(ids: list[int])    → str         (decoded text)
    - decode_single(id: int)    → str         (single token → text)
    - vocab_size                → int         (property)
    - is_loaded                 → bool        (property)

Artifact format (expected at config.tokenizer_path):
    A JSON file with at least:
    {
        "vocab": { "<token_string>": <int_id>, ... },
        "merges": [ ["<pair_a>", "<pair_b>"], ... ]
    }
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class BPETokenizer:
    """Byte Pair Encoding tokenizer for Urdu text."""

    def __init__(self) -> None:
        self._vocab: dict[str, int] = {}
        self._inverse_vocab: dict[int, str] = {}
        self._merges: list[tuple[str, str]] = []
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def vocab_size(self) -> int:
        return len(self._vocab)

    def load(self, path: str) -> None:
        """Load a trained BPE tokenizer from a JSON file.

        Expected JSON schema:
        {
            "vocab": { "token": id, ... },
            "merges": [ ["a", "b"], ... ]
        }
        """
        filepath = Path(path)
        if not filepath.exists():
            logger.warning(
                "Tokenizer file not found at %s — running in STUB mode.", path
            )
            self._init_stub()
            return

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._vocab = data["vocab"]
        self._inverse_vocab = {v: k for k, v in self._vocab.items()}
        self._merges = [tuple(m) for m in data["merges"]]
        self._loaded = True
        logger.info(
            "Tokenizer loaded: vocab_size=%d, merges=%d",
            self.vocab_size,
            len(self._merges),
        )

    def encode(self, text: str) -> list[int]:
        """Encode text into a list of token IDs.

        TODO: Implement BPE encoding algorithm.
        Current stub returns character-level token IDs.
        """
        if not self._loaded:
            logger.warning("Tokenizer not loaded — using stub encode.")
            return [ord(c) % max(self.vocab_size, 1) for c in text]

        # ---------------------------------------------------------------
        # PLACEHOLDER: Replace with actual BPE encoding logic.
        # Steps:
        #   1. Split text into characters (pre-tokenization).
        #   2. Iteratively apply learned merges in priority order.
        #   3. Map resulting subword tokens to IDs via self._vocab.
        #
        # For now, fall back to character-level encoding using vocab.
        # This allows the full pipeline to work end-to-end in stub mode.
        # ---------------------------------------------------------------
        ids = []
        for ch in text:
            if ch in self._vocab:
                ids.append(self._vocab[ch])
            else:
                # Unknown character — map to first vocab entry
                ids.append(0)
        return ids

    def decode(self, ids: list[int]) -> str:
        """Decode a list of token IDs back into text."""
        return "".join(self.decode_single(i) for i in ids)

    def decode_single(self, token_id: int) -> str:
        """Decode a single token ID into its text representation."""
        if not self._loaded:
            return chr(token_id) if 0 <= token_id < 0x110000 else "?"
        return self._inverse_vocab.get(token_id, "?")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _init_stub(self) -> None:
        """Initialize a minimal stub tokenizer for development/testing."""
        # Create a tiny vocab of Urdu characters + special tokens
        stub_chars = list("ابپتٹثجچحخدڈذرڑزژسشصضطظعغفقکگلمنوہھیے ")
        self._vocab = {ch: i for i, ch in enumerate(stub_chars)}
        self._inverse_vocab = {i: ch for ch, i in self._vocab.items()}
        self._merges = []
        self._loaded = True
        logger.info("Stub tokenizer initialized with %d chars.", self.vocab_size)
