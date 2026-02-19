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
import os
import collections
import re
import unicodedata
from pathlib import Path

logger = logging.getLogger(__name__)


class BPETokenizer:
    """Byte Pair Encoding tokenizer for Urdu text."""

    def __init__(self, vocab_size: int = 250) -> None:
        self.target_vocab_size = vocab_size
        self._vocab: dict[str, int] = {}
        self._inverse_vocab: dict[int, str] = {}
        self._merges: list[tuple[str, str]] = []
        self._loaded: bool = False
        
        # Internal dictionary for fast encoding: {(id1, id2): new_id}
        self._merge_dict: dict[tuple[int, int], int] = {}
        
        # Mapping special tokens to "unused" Unicode bytes (Private Use Area)
        self.special_map = {
            "<BOS>": "\ue000",
            "<EOS>": "\ue001",
            "<PARA>": "\ue002",
            "<UNK>": "\ue005"
        }
        self.special_tokens = list(self.special_map.keys())
        self.space_char = "\u2581"

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
        self._inverse_vocab = {int(v): k for k, v in self._vocab.items()}
        self._merges = [tuple(m) for m in data["merges"]]
        
        # Reconstruct the fast merge dictionary for the encode() loop
        self._merge_dict = {}
        for p1_str, p2_str in self._merges:
            if p1_str in self._vocab and p2_str in self._vocab:
                p1_id = self._vocab[p1_str]
                p2_id = self._vocab[p2_str]
                combined_str = p1_str + p2_str
                if combined_str in self._vocab:
                    self._merge_dict[(p1_id, p2_id)] = self._vocab[combined_str]

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
        
        text = self._preprocess(text)
        unk_id = self._vocab.get(self.special_map["<UNK>"], 0)
        ids = [self._vocab.get(char, unk_id) for char in text]

        while True:
            stats = self._get_stats(ids)
            best_pair = None
            min_merge_id = float('inf')
            
            for pair in stats:
                if pair in self._merge_dict:
                    if self._merge_dict[pair] < min_merge_id:
                        min_merge_id = self._merge_dict[pair]
                        best_pair = pair
                        
            if best_pair is None: 
                break
                
            ids = self._merge_ids(ids, best_pair, self._merge_dict[best_pair])
            
        return ids

    def decode(self, ids: list[int]) -> str:
        """Decode a list of token IDs back into text."""
        return "".join(self.decode_single(i) for i in ids)

    def decode_single(self, token_id: int) -> str:
        """Decode a single token ID into its text representation."""
        if not self._loaded:
            return chr(token_id) if 0 <= token_id < 0x110000 else "?"
        token_str = self._inverse_vocab.get(token_id, self.special_map["<UNK>"])
        
        # Reverse PUA mapping
        for token_name, pua in self.special_map.items():
            token_str = token_str.replace(pua, token_name)
            
        # Reverse space mapping
        token_str = token_str.replace(self.space_char, " ")
        
        return token_str
    
    # ------------------------------------------------------------------
    # Training & Saving (Phase II Logic)
    # ------------------------------------------------------------------

    def train(self, corpus_text: str) -> None:
        """Trains the BPE tokenizer on a provided text corpus."""
        next_id = 0
        for st_name, pua_code in self.special_map.items():
            self._vocab[pua_code] = next_id
            self._inverse_vocab[next_id] = pua_code
            next_id += 1

        text = self._preprocess(corpus_text)
        tokens = list(text)
        unique_chars = sorted(list(set(tokens)))
        
        for char in unique_chars:
            if char not in self._vocab:
                self._vocab[char] = next_id
                self._inverse_vocab[next_id] = char
                next_id += 1

        if len(self._vocab) > self.target_vocab_size:
            logger.warning("Base vocab (%d) exceeds target (%d).", len(self._vocab), self.target_vocab_size)
            return

        train_ids = [self._vocab[t] for t in tokens]
        self._merge_dict = {}
        self._merges = []

        logger.info("Training BPE (Vocab Target: %d)...", self.target_vocab_size)
        
        while len(self._vocab) < self.target_vocab_size:
            stats = self._get_stats(train_ids)
            if not stats: break

            pua_values = set(self.special_map.values())
            valid_pairs = {
                p: f for p, f in stats.items()
                if self._inverse_vocab[p[0]] not in pua_values and 
                   self._inverse_vocab[p[1]] not in pua_values
            }
            
            if not valid_pairs: break

            best_pair = max(valid_pairs, key=valid_pairs.get)
            p1_str = self._inverse_vocab[best_pair[0]]
            p2_str = self._inverse_vocab[best_pair[1]]
            new_token_str = p1_str + p2_str
            
            new_id = next_id
            self._vocab[new_token_str] = new_id
            self._inverse_vocab[new_id] = new_token_str
            self._merge_dict[best_pair] = new_id
            
            # Store as list of strings for the required artifact schema
            self._merges.append((p1_str, p2_str))
            
            next_id += 1
            train_ids = self._merge_ids(train_ids, best_pair, new_id)
        
        self._loaded = True

    def save(self, path: str = "backend/models/bpe_tokenizer.json") -> None:
        """Saves the tokenizer matching the strictly required team artifact format."""
        data = {
            "vocab": self._vocab,
            "merges": [list(m) for m in self._merges]
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _clean_urdu(self, text: str) -> str:
        """اردو متن سے اعراب ہٹانا تاکہ وکیبلری سائز بچ سکے"""
        text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
        text = unicodedata.normalize('NFKC', text)
        return text

    def _preprocess(self, text: str) -> str:
        for token, pua in self.special_map.items():
            text = text.replace(token, pua)
        text = self._clean_urdu(text)
        text = text.replace(" ", self.space_char)
        text = re.sub(r'[a-zA-Z]', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.replace(" ", self.space_char)
        return text

    def _get_stats(self, ids: list[int]) -> dict[tuple[int, int], int]:
        counts = collections.defaultdict(int)
        for i in range(len(ids) - 1):
            counts[(ids[i], ids[i+1])] += 1
        return counts

    def _merge_ids(self, ids: list[int], pair: tuple[int, int], new_id: int) -> list[int]:
        new_ids = []
        i = 0
        while i < len(ids):
            if i < len(ids) - 1 and ids[i] == pair[0] and ids[i+1] == pair[1]:
                new_ids.append(new_id)
                i += 2
            else:
                new_ids.append(ids[i])
                i += 1
        return new_ids

    def _init_stub(self) -> None:
        """Initialize a minimal stub tokenizer for development/testing."""
        # Create a tiny vocab of Urdu characters + special tokens
        stub_chars = list("ابپتٹثجچحخدڈذرڑزژسشصضطظعغفقکگلمنوہھیے ")
        self._vocab = {ch: i for i, ch in enumerate(stub_chars)}
        self._inverse_vocab = {i: ch for ch, i in self._vocab.items()}
        self._merges = []
        self._loaded = True
        logger.info("Stub tokenizer initialized with %d chars.", self.vocab_size)
