"""
One-time conversion script: trigram_model.json → trigram_model.db (SQLite)

Why: The 40MB JSON file loads ~350MB of Python dicts into RAM.
     SQLite keeps data on disk and queries only what's needed → ~5MB RAM.

Usage (from project root):
    python backend/scripts/convert_model_to_sqlite.py

Or specify custom paths:
    python backend/scripts/convert_model_to_sqlite.py \
        --input  backend/models/trigram_model.json \
        --output backend/models/trigram_model.db
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# Default paths (relative to project root)
DEFAULT_INPUT  = Path(__file__).resolve().parents[2] / "backend" / "models" / "trigram_model.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "backend" / "models" / "trigram_model.db"


def convert(input_path: Path, output_path: Path) -> None:
    logger.info("Reading %s …", input_path)
    t0 = time.perf_counter()
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info("JSON loaded in %.1fs", time.perf_counter() - t0)

    if output_path.exists():
        output_path.unlink()
        logger.info("Removed existing %s", output_path)

    conn = sqlite3.connect(output_path)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous  = NORMAL")
    conn.execute("PRAGMA cache_size   = -32768")   # 32 MB page cache during build

    # ── Schema ────────────────────────────────────────────────────────────────
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS unigrams (
            t1    INTEGER PRIMARY KEY,
            count INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS bigrams (
            t1    INTEGER NOT NULL,
            t2    INTEGER NOT NULL,
            count INTEGER NOT NULL,
            PRIMARY KEY (t1, t2)
        );

        CREATE TABLE IF NOT EXISTS trigrams (
            t1    INTEGER NOT NULL,
            t2    INTEGER NOT NULL,
            t3    INTEGER NOT NULL,
            count INTEGER NOT NULL,
            PRIMARY KEY (t1, t2, t3)
        );

        CREATE TABLE IF NOT EXISTS metadata (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)

    # ── Unigrams ──────────────────────────────────────────────────────────────
    logger.info("Inserting unigrams …")
    unigrams = [(int(k), int(v)) for k, v in data["unigram_counts"].items()]
    conn.executemany("INSERT OR REPLACE INTO unigrams VALUES (?, ?)", unigrams)
    logger.info("  %d unigrams", len(unigrams))

    # ── Bigrams ───────────────────────────────────────────────────────────────
    logger.info("Inserting bigrams …")
    BATCH = 50_000
    bigram_items = list(data["bigram_counts"].items())
    for i in range(0, len(bigram_items), BATCH):
        batch = bigram_items[i:i + BATCH]
        rows = []
        for k, v in batch:
            t1, t2 = map(int, k.split(","))
            rows.append((t1, t2, int(v)))
        conn.executemany("INSERT OR REPLACE INTO bigrams VALUES (?, ?, ?)", rows)
        if i % 200_000 == 0 and i > 0:
            logger.info("  … %d bigrams inserted", i)
    conn.commit()
    logger.info("  %d bigrams total", len(bigram_items))

    # ── Trigrams ──────────────────────────────────────────────────────────────
    logger.info("Inserting trigrams (this takes a minute) …")
    trigram_items = list(data["trigram_counts"].items())
    for i in range(0, len(trigram_items), BATCH):
        batch = trigram_items[i:i + BATCH]
        rows = []
        for k, v in batch:
            t1, t2, t3 = map(int, k.split(","))
            rows.append((t1, t2, t3, int(v)))
        conn.executemany("INSERT OR REPLACE INTO trigrams VALUES (?, ?, ?, ?)", rows)
        if i % 500_000 == 0 and i > 0:
            logger.info("  … %d trigrams inserted", i)
    conn.commit()
    logger.info("  %d trigrams total", len(trigram_items))

    # ── Query-time index: (t2, t3) for bigram lookup, (t1,t2) for trigram ────
    logger.info("Building indexes …")
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_bigrams_t1   ON bigrams  (t1);
        CREATE INDEX IF NOT EXISTS idx_trigrams_t1t2 ON trigrams (t1, t2);
    """)
    conn.commit()

    # ── Metadata ─────────────────────────────────────────────────────────────
    import json as _json
    conn.executemany(
        "INSERT OR REPLACE INTO metadata VALUES (?, ?)",
        [
            ("lambdas",     _json.dumps(data["lambdas"])),
            ("vocab_size",  str(data.get("vocab_size", len(unigrams)))),
            ("total_tokens", str(sum(v for _, v in unigrams))),
        ],
    )
    conn.commit()
    conn.close()

    size_mb = output_path.stat().st_size / 1024 / 1024
    logger.info(
        "Done in %.1fs → %s (%.1f MB)",
        time.perf_counter() - t0,
        output_path,
        size_mb,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert trigram JSON to SQLite")
    parser.add_argument("--input",  type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.input.exists():
        logger.error("Input file not found: %s", args.input)
        sys.exit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    convert(args.input, args.output)


if __name__ == "__main__":
    main()
