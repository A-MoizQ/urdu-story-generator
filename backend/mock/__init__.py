"""
Mock story data for development mode.

When APP_ENV=development, the backend streams one of these pre-written
Urdu stories word-by-word instead of running the real model pipeline.
This allows frontend development and testing without model artifacts.
"""

from __future__ import annotations

import logging
import random
from typing import Generator

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Pre-written Urdu stories for development / demo
# ──────────────────────────────────────────────────────────────

MOCK_STORIES: list[str] = [
    (
        "ایک دفعہ کا ذکر ہے کہ ایک چھوٹے سے گاؤں میں ایک بوڑھا درویش رہتا تھا۔ "
        "وہ ہر روز صبح سویرے اٹھتا اور پہاڑوں کی طرف چل پڑتا۔ "
        "لوگ اسے دیوانہ سمجھتے تھے مگر وہ ہمیشہ مسکراتا رہتا۔ "
        "ایک دن ایک نوجوان نے اس سے پوچھا کہ آپ ہر روز کہاں جاتے ہیں؟ "
        "درویش نے کہا کہ میں سورج کو سلام کرنے جاتا ہوں۔ "
        "نوجوان حیران ہوا اور بولا کہ سورج تو خود آ جاتا ہے۔ "
        "درویش نے ہنس کر کہا کہ بیٹا سورج آتا ہے مگر اسے ملنے کون جاتا ہے۔ "
        "اس دن سے نوجوان بھی ہر صبح درویش کے ساتھ پہاڑ پر جانے لگا۔ "
        "اور آہستہ آہستہ اسے زندگی کا مقصد سمجھ آنے لگا۔"
    ),
    (
        "بہت پرانے زمانے کی بات ہے کہ ایک شہزادی تھی جو ستاروں سے باتیں کرتی تھی۔ "
        "ہر رات وہ اپنے محل کی چھت پر جاتی اور آسمان کو دیکھتی۔ "
        "ایک رات ایک ستارہ ٹوٹ کر اس کے باغ میں گرا۔ "
        "شہزادی نے دیکھا کہ وہ ستارہ ایک چمکتا ہوا پتھر بن گیا ہے۔ "
        "اس نے اسے اٹھایا تو اس کے ہاتھوں سے روشنی پھیلنے لگی۔ "
        "اس روشنی سے پورا باغ جگمگا اٹھا اور پھول کھلنے لگے۔ "
        "شہزادی نے اس پتھر کو اپنے دل کے قریب رکھا۔ "
        "اور اس دن سے وہ لوگوں کو روشنی بانٹنے لگی۔ "
        "کہتے ہیں کہ آج بھی اس شہزادی کی روشنی ستاروں میں نظر آتی ہے۔"
    ),
    (
        "کسی زمانے میں ایک چالاک لومڑی جنگل میں رہتی تھی۔ "
        "اس کے پاس ایک جادوئی آئینہ تھا جو سچ بولتا تھا۔ "
        "ایک دن شیر نے لومڑی سے کہا کہ مجھے وہ آئینہ دے دو۔ "
        "لومڑی نے کہا کہ یہ آئینہ صرف سچے دل والوں کو جواب دیتا ہے۔ "
        "شیر نے آئینے میں دیکھا تو اسے اپنی اصل شکل نظر آئی۔ "
        "وہ ایک تھکا ہوا بوڑھا شیر تھا جسے اپنے بچوں کی یاد ستاتی تھی۔ "
        "شیر کی آنکھوں میں آنسو آ گئے اور وہ واپس اپنی غار میں چلا گیا۔ "
        "اس دن سے شیر نے کسی کو ڈرانا چھوڑ دیا۔ "
        "اور جنگل میں امن قائم ہو گیا۔"
    ),
    (
        "ایک چھوٹی سی بچی تھی جس کا نام نور تھا۔ "
        "نور کو کتابیں پڑھنے کا بہت شوق تھا۔ "
        "وہ ہر روز لائبریری جاتی اور گھنٹوں کتابیں پڑھتی۔ "
        "ایک دن اسے ایک پرانی کتاب ملی جس کے صفحات سنہری تھے۔ "
        "جب اس نے کتاب کھولی تو حروف ہوا میں اڑنے لگے۔ "
        "حروف نے مل کر ایک خوبصورت کہانی بنائی جو صرف نور کو سنائی دیتی تھی۔ "
        "کہانی میں ایک جادوئی دنیا تھی جہاں لفظ زندہ تھے۔ "
        "نور نے اس دنیا میں قدم رکھا اور لفظوں سے دوستی کر لی۔ "
        "جب وہ واپس آئی تو اس کے پاس لکھنے کا ایک نیا جادو تھا۔"
    ),
]


class MockStoryGenerator:
    """Generates mock stories word-by-word for development/testing.

    Always reports as ready. No model artifacts needed.
    """

    def __init__(self) -> None:
        self._ready = True
        logger.info("MockStoryGenerator initialized (APP_ENV=development)")

    def load(self) -> None:
        """No-op — mock generator needs no artifacts."""
        logger.info("MockStoryGenerator.load() called — nothing to load.")

    @property
    def is_ready(self) -> bool:
        return True

    @property
    def model(self) -> "MockStoryGenerator":
        """Quacks like StoryGenerator — self.model.is_loaded works."""
        return self

    @property
    def tokenizer(self) -> "MockStoryGenerator":
        """Quacks like StoryGenerator — self.tokenizer.is_loaded works."""
        return self

    @property
    def is_loaded(self) -> bool:
        return True

    def generate(
        self, prefix: str, max_length: int = 0
    ) -> Generator[tuple[str, str, bool], None, None]:
        """Yield a mock story word-by-word, prepended with the user's prefix.

        Args:
            prefix: The user-typed starting text (ignored for story selection,
                    but prepended to the output so the UI feels natural).
            max_length: Ignored in mock mode — full story is always returned.

        Yields:
            (word, full_text_so_far, is_finished)
        """
        story = random.choice(MOCK_STORIES)

        # If the story starts with a variant of the user's prefix, use as-is;
        # otherwise prepend prefix so the user sees their input echoed.
        if prefix.strip() and not story.startswith(prefix.strip()):
            story = prefix.strip() + " " + story

        words = story.split()
        full_text = ""

        for i, word in enumerate(words):
            is_last = i == len(words) - 1
            full_text += (" " if full_text else "") + word
            yield word, full_text, is_last

        # Safety: if story was empty, still emit a finish signal
        if not words:
            yield "", prefix, True
