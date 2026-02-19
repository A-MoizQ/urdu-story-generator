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

        # Encode the prefix to get initial context.
        # Prepend a space so word-initial tokens get the ▁ marker that
        # matches how the training corpus was tokenised (e.g. "ایک" →
        # [▁ایک] not [ا,ی,ک]).  Strip the synthetic leading token after.
        token_ids = self.tokenizer.encode(" " + prefix)

        # Drop the leading ▁-space token that was only added for context
        if len(token_ids) > 1:
            token_ids = token_ids[1:]

        # We need at least 2 tokens for trigram context
        if len(token_ids) < 2:
            while len(token_ids) < 2:
                token_ids = [token_ids[0]] + token_ids if token_ids else [0, 0]

        # Start building the full output text
        full_text = prefix

        # Resolve stop-token IDs from the tokenizer's own special map
        # <EOS>  = sentence boundary → display as "۔ "
        # <PARA> = paragraph break   → display as "\n\n"
        # <BOS>  = story boundary    → stop generation only after a
        #          minimum number of tokens have already been generated,
        #          to avoid stopping immediately on out-of-distribution
        #          prefix context.
        eos_id  = self.tokenizer.special_token_id("<EOS>")
        para_id = self.tokenizer.special_token_id("<PARA>")
        bos_id  = self.tokenizer.special_token_id("<BOS>")

        MIN_TOKENS_BEFORE_BOS_STOP = 10
        generated_count = 0

        while generated_count < max_length:
            # Use last two tokens as trigram context
            t1 = token_ids[-2]
            t2 = token_ids[-1]

            # Sample next token
            next_token_id = self.model.predict_next(t1, t2)
            token_ids.append(next_token_id)
            generated_count += 1

            # BOS mid-generation = story boundary.
            # Only stop if we've already generated enough content;
            # otherwise treat it as an invisible token and keep going.
            if bos_id is not None and next_token_id == bos_id:
                if generated_count >= MIN_TOKENS_BEFORE_BOS_STOP:
                    yield "", full_text, True
                    return
                # Too early — skip this token silently and continue
                continue

            # Decode via the tokenizer (handles PUA → display mapping)
            display_text = self.tokenizer.decode_single(next_token_id)

            full_text += display_text

            yield display_text, full_text, False

        # Reached max_length — emit a final finished event
        yield "", full_text, True
