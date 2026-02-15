"""
Story generation inference pipeline.

Orchestrates the tokenizer and trigram model to produce tokens one at a time.
Designed to be consumed by the gRPC streaming endpoint.
"""

from __future__ import annotations

import logging
from typing import Generator

from backend.config import config
from backend.model import TrigramModel
from backend.tokenizer import BPETokenizer

logger = logging.getLogger(__name__)


class StoryGenerator:
    """Generates Urdu stories token-by-token using a trigram LM + BPE tokenizer."""

    def __init__(self) -> None:
        self.tokenizer = BPETokenizer()
        self.model = TrigramModel()
        self._ready = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load tokenizer and model artifacts from disk."""
        logger.info("Loading tokenizer from: %s", config.tokenizer_path)
        self.tokenizer.load(config.tokenizer_path)

        logger.info("Loading trigram model from: %s", config.trigram_model_path)
        self.model.load(config.trigram_model_path)

        self._ready = True
        logger.info("StoryGenerator is ready.")

    @property
    def is_ready(self) -> bool:
        return (
            self._ready
            and self.tokenizer.is_loaded
            and self.model.is_loaded
        )

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate(
        self, prefix: str, max_length: int = 0
    ) -> Generator[tuple[str, str, bool], None, None]:
        """Generate tokens one-by-one given a prefix.

        Yields:
            (token_text, full_text_so_far, is_finished)
        """
        if not self.is_ready:
            raise RuntimeError("StoryGenerator is not loaded. Call load() first.")

        if max_length <= 0:
            max_length = config.default_max_length

        # Encode the prefix to get initial context
        token_ids = self.tokenizer.encode(prefix)

        # We need at least 2 tokens for trigram context
        if len(token_ids) < 2:
            # Pad with a repeated token if prefix is too short
            while len(token_ids) < 2:
                token_ids = [token_ids[0]] + token_ids if token_ids else [0, 0]

        # Start building the full output text
        full_text = prefix

        # Determine the EOT token ID
        eot_id = self.tokenizer._vocab.get(config.eot_token)

        generated_count = 0

        while generated_count < max_length:
            # Use last two tokens as trigram context
            t1 = token_ids[-2]
            t2 = token_ids[-1]

            # Sample next token
            next_token_id = self.model.predict_next(t1, t2)
            token_ids.append(next_token_id)
            generated_count += 1

            # Decode the new token
            token_text = self.tokenizer.decode_single(next_token_id)

            # Check for end-of-text
            is_eot = eot_id is not None and next_token_id == eot_id
            if is_eot:
                yield token_text, full_text, True
                return

            # Replace special tokens with readable markers for the UI
            display_text = token_text
            if token_text == config.eos_token:
                display_text = "۔ "  # Urdu full stop
            elif token_text == config.eop_token:
                display_text = "\n\n"  # Paragraph break

            full_text += display_text

            yield display_text, full_text, False

        # Reached max length without EOT
        yield "", full_text, True
