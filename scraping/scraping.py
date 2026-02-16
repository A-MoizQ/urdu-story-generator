"""
Urdu Story Web Scraper
=====================================
Scrapes Urdu stories from 3 websites using multiprocessing + multithreading.

Websites:
  1. milkystory.com      – Uses sitemap.xml for URL discovery
  2. urdupoint.com        – Uses category pages (moral/true/funny stories)
  3. adabiduniya.com      – Paginated listing, h2-only link extraction

  - milkystory: sitemap-based discovery (listing page is JS-rendered)
  - urdupoint: category pages instead of blocked stories-pageN.html
  - adabiduniya: only h2>a links from main area, Urdu content validation
  - All: content quality validation (Urdu ratio, min length, no boilerplate)
"""

import json
import sys
import time
import logging
import re
import random
import multiprocessing
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, local as threading_local
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

# ─────────────────── configuration ───────────────────
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REQUEST_DELAY = (0.5, 1.5)        # default delay range (seconds)
URDUPOINT_DELAY = (1.5, 3.0)      # urdupoint needs slower crawling
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30
SAVE_EVERY_N = 5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ur;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}


# ─────────────────── logging ─────────────────────────
def setup_logging():
    fmt = "[%(asctime)s] [%(name)-16s] [%(levelname)-7s] %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


# ─────────────────── system auto-config ──────────────
def get_optimal_threads():
    cores = multiprocessing.cpu_count()
    try:
        import psutil
        ram_gb = psutil.virtual_memory().available / (1024 ** 3)
    except ImportError:
        ram_gb = 4.0
    threads = max(2, min(max(2, cores), 8))
    return threads, cores, round(ram_gb, 1)


# ─────────────────── HTTP helpers ────────────────────
_tl = threading_local()


def get_session():
    """Return a thread-local HTTP session.

    Uses curl_cffi with Chrome impersonation when available (bypasses
    Cloudflare / anti-bot).  Falls back to plain requests.
    """
    if not getattr(_tl, "session", None):
        if HAS_CURL_CFFI:
            s = cffi_requests.Session(
                impersonate="chrome",
                headers=HEADERS,
            )
        else:
            s = requests.Session()
            s.headers.update(HEADERS)
            retry = Retry(
                total=MAX_RETRIES,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET"],
            )
            adapter = HTTPAdapter(max_retries=retry)
            s.mount("https://", adapter)
            s.mount("http://", adapter)
        _tl.session = s
    return _tl.session


def fetch_page(url: str, referer: str = None) -> str | None:
    """Fetch a page with automatic retry on transient errors."""
    session = get_session()
    hdrs = {}
    if referer:
        hdrs["Referer"] = referer

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT, headers=hdrs)
            resp.raise_for_status()
            # curl_cffi handles encoding; for plain requests set it
            if not HAS_CURL_CFFI:
                resp.encoding = resp.apparent_encoding
            return resp.text
        except Exception as exc:
            if attempt < MAX_RETRIES:
                wait = 2 ** attempt + random.random()
                logging.debug(
                    "Retry %d/%d for %s (%s) — wait %.1fs",
                    attempt, MAX_RETRIES, url, exc, wait,
                )
                time.sleep(wait)
            else:
                logging.warning("Request failed %s: %s", url, exc)
                return None
    return None


# ─────────────────── text helpers ────────────────────
def clean(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_urdu(text: str, threshold: float = 0.3) -> bool:
    """True if *text* has >= *threshold* fraction of Urdu/Arabic chars."""
    if not text:
        return False
    stripped = text.replace(" ", "")
    if not stripped:
        return False
    urdu = sum(1 for c in stripped if "\u0600" <= c <= "\u06FF")
    return (urdu / len(stripped)) >= threshold


def delay(delay_range=REQUEST_DELAY):
    time.sleep(random.uniform(*delay_range))


# ─────────────────── base scraper ────────────────────
class BaseScraper(ABC):

    def __init__(self, name: str, output_filename: str, num_threads: int):
        self.name = name
        self.output_file = DATA_DIR / output_filename
        self.num_threads = num_threads
        self.stories: list[dict] = []
        self.scraped_urls: set[str] = set()
        self._lock = Lock()
        self._new = 0
        self.logger = logging.getLogger(name)
        self._load_existing()

    # ── resume ──
    def _load_existing(self):
        if self.output_file.exists():
            try:
                with open(self.output_file, "r", encoding="utf-8") as fh:
                    self.stories = json.load(fh)
                self.scraped_urls = {s["url"] for s in self.stories}
                self.logger.info("Resumed with %d existing stories", len(self.stories))
            except (json.JSONDecodeError, KeyError, TypeError):
                self.logger.warning("Corrupt JSON — starting fresh")
                self.stories, self.scraped_urls = [], set()

    # ── save ──
    def _save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = self.output_file.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.stories, fh, ensure_ascii=False, indent=2)
        tmp.rename(self.output_file)

    def save(self):
        with self._lock:
            self._save()

    def add_story(self, story: dict) -> bool:
        with self._lock:
            if story["url"] in self.scraped_urls:
                return False
            self.stories.append(story)
            self.scraped_urls.add(story["url"])
            self._new += 1
            if self._new % SAVE_EVERY_N == 0:
                self._save()
            return True

    # ── abstract ──
    @abstractmethod
    def collect_links(self) -> list[tuple[str, str]]: ...

    @abstractmethod
    def parse_story(self, url: str, title: str, html: str) -> dict | None: ...

    # ── per-scraper delay (override in subclass) ──
    def _delay_range(self):
        return REQUEST_DELAY

    # ── single story ──
    def _scrape_one(self, url: str, title: str) -> bool:
        delay(self._delay_range())
        html = fetch_page(url)
        if not html:
            return False
        try:
            story = self.parse_story(url, title, html)
        except Exception as exc:
            self.logger.error("Parse error %s: %s", url, exc)
            return False
        if not story:
            return False
        content = story.get("content", "")
        if len(content.strip()) < 100:
            self.logger.warning("  x too short (%d chars): %s", len(content), url)
            return False
        if not is_urdu(content, 0.2):
            self.logger.warning("  x not Urdu: %s", url)
            return False
        self.add_story(story)
        self.logger.info("  + %s (%d chars)", story["title"][:60], len(content))
        return True

    # ── main loop ──
    def run(self):
        self.logger.info("=== %s scraper starting ===", self.name)

        self.logger.info("[Phase 1] Collecting story links …")
        all_links = self.collect_links()
        seen: set[str] = set()
        unique: list[tuple[str, str]] = []
        for u, t in all_links:
            if u not in seen:
                seen.add(u)
                unique.append((u, t))
        new = [(u, t) for u, t in unique if u not in self.scraped_urls]
        self.logger.info(
            "  total=%d  unique=%d  new=%d",
            len(all_links), len(unique), len(new),
        )
        if not new:
            self.logger.info("Nothing new — done.")
            return

        self.logger.info("[Phase 2] Scraping with %d threads …", self.num_threads)
        ok = err = 0
        with ThreadPoolExecutor(max_workers=self.num_threads) as pool:
            futs = {pool.submit(self._scrape_one, u, t): u for u, t in new}
            for fut in as_completed(futs):
                try:
                    if fut.result():
                        ok += 1
                    else:
                        err += 1
                except Exception as exc:
                    self.logger.error("Thread error: %s", exc)
                    err += 1

        self.save()
        self.logger.info(
            "=== %s done: %d OK, %d ERR, %d total ===",
            self.name, ok, err, len(self.stories),
        )

    def _make_entry(self, *, title, url, content, author="", date="",
                    category="", source=""):
        return {
            "title": title,
            "url": url,
            "content": content,
            "author": author,
            "date": date,
            "category": category,
            "source": source or self.name,
            "scraped_at": datetime.now().isoformat(),
        }


# ═════════════════════════════════════════════════════
# 1.  milkystory.com  —  sitemap-based discovery
# ═════════════════════════════════════════════════════
class MilkyStoryScraper(BaseScraper):
    BASE = "https://milkystory.com"
    SITEMAP = f"{BASE}/sitemap.xml"

    # Non-story path prefixes to skip
    SKIP_PREFIXES = (
        "urdu-stories", "kids-stories", "urdu-poetry", "urdu-news",
        "dilchasp-aur-ajeeb", "entertainment-showbiz", "urdu-sports",
        "business-news", "about", "contact", "submit-a-story",
        "terms-and-conditions", "privacy-policy", "kids-zone",
        "kids-stories-urdu", "en/", "en", "ur/", "ur",
        "blog-post",
    )

    def __init__(self, num_threads: int):
        super().__init__("milkystory", "milkystory.json", num_threads)

    def collect_links(self):
        links: list[tuple[str, str]] = []

        self.logger.info("  Fetching sitemap: %s", self.SITEMAP)
        xml = fetch_page(self.SITEMAP)
        if not xml:
            self.logger.error("  Sitemap fetch failed — trying listing page")
            return self._collect_from_listing()

        urls = re.findall(r"<loc>(https?://[^<]+)</loc>", xml)
        self.logger.info("  Sitemap contains %d URLs", len(urls))

        for raw_url in urls:
            url = raw_url.rstrip("/")
            if url == self.BASE or url == f"{self.BASE}/":
                continue
            path = url.replace(self.BASE + "/", "")
            if any(path.startswith(p) for p in self.SKIP_PREFIXES):
                continue
            if not path:
                continue
            slug_title = path.replace("-", " ").title()
            links.append((url, slug_title))

        self.logger.info("  %d candidate story URLs", len(links))
        return links

    def _collect_from_listing(self):
        """Fallback: scrape the listing page if sitemap fails."""
        links: list[tuple[str, str]] = []
        page = 1
        while page <= 10:
            url = f"{self.BASE}/urdu-stories" + (f"?page={page}" if page > 1 else "")
            self.logger.info("  listing page %d", page)
            html = fetch_page(url)
            if not html:
                break
            soup = BeautifulSoup(html, "lxml")
            found = 0
            for a in soup.find_all("a", href=True):
                href = a["href"].rstrip("/")
                if not href.startswith(self.BASE):
                    continue
                path = href.replace(self.BASE, "").strip("/")
                if not path or any(path.startswith(p) for p in self.SKIP_PREFIXES):
                    continue
                title = clean(a.get_text())
                if title and len(title) > 3:
                    links.append((href, title))
                    found += 1
            if found == 0:
                break
            page += 1
            delay()
        return links

    def parse_story(self, url, title, html):
        soup = BeautifulSoup(html, "lxml")

        # ── Title ──
        story_title = title
        h1 = soup.find("h1")
        if h1:
            story_title = clean(h1.get_text())

        # ── Category check — only keep story pages ──
        page_text = soup.get_text().lower()
        is_story_page = any(
            kw in page_text
            for kw in ("اردو کہانیاں", "بچوں کی دنیا", "کہانی", "story", "novel")
        )
        if not is_story_page:
            self.logger.debug("  x not a story page: %s", url)
            return None

        # ── Author ──
        author = ""
        for el in soup.find_all(["span", "a", "div", "p"]):
            cls = " ".join(el.get("class", []))
            if "author" in cls.lower() or "writer" in cls.lower():
                author = clean(el.get_text())
                break

        # ── Date ──
        date_str = ""
        time_el = soup.find("time")
        if time_el:
            date_str = time_el.get("datetime", clean(time_el.get_text()))
        if not date_str:
            m = re.search(r"\d{1,2}/\d{1,2}/\d{4}", html)
            if m:
                date_str = m.group(0)

        # ── Content ──
        paragraphs: list[str] = []

        # Milkystory (Zyrosite builder) puts story text in div.text-box
        # elements.  Standard selectors (article, rich-text, etc.) don't
        # apply, so we scan the whole page body for Urdu paragraphs.
        target = soup.body or soup

        if target:
            # remove footer / boilerplate nodes
            for junk in target.find_all(
                ["footer", "nav", "aside", "script", "style", "iframe", "form"],
            ):
                junk.decompose()

            for el in target.find_all(["p"]):
                cls = " ".join(el.get("class", []))
                if any(kw in cls.lower() for kw in (
                    "footer", "nav", "sidebar", "ad", "share", "social",
                    "comment", "related", "subscribe", "newsletter", "header",
                )):
                    continue
                t = clean(el.get_text())
                if not t or len(t) < 20:
                    continue
                if any(kw in t.lower() for kw in (
                    "subscribe", "privacy", "copyright", "milky story ©",
                    "terms & conditions", "email address", "submit a story",
                    "ملکی اسٹوری اگلی نسل",
                )):
                    continue
                if is_urdu(t, 0.3):
                    paragraphs.append(t)

        # deduplicate consecutive identical paragraphs
        deduped: list[str] = []
        for p in paragraphs:
            if not deduped or p != deduped[-1]:
                deduped.append(p)

        content = "\n\n".join(deduped)
        if not is_urdu(content, 0.3):
            return None

        return self._make_entry(
            title=story_title, url=url, content=content,
            author=author, date=date_str, source="milkystory.com",
        )


# ═════════════════════════════════════════════════════
# 2.  urdupoint.com  —  category-based scraping
# ═════════════════════════════════════════════════════
class UrduPointScraper(BaseScraper):
    BASE = "https://www.urdupoint.com"

    CATEGORIES = [
        "moral-stories",
        "true-stories",
        "funny-stories",
    ]

    def __init__(self, num_threads: int):
        super().__init__("urdupoint", "urdupoint.json", num_threads)

    def _delay_range(self):
        return URDUPOINT_DELAY

    # ── link collection ──────────────────────────────
    def collect_links(self):
        links: list[tuple[str, str]] = []

        for cat in self.CATEGORIES:
            self.logger.info("  ── Category: %s ──", cat)

            cat_url = f"{self.BASE}/kids/category/{cat}.html"
            html = fetch_page(cat_url, referer=f"{self.BASE}/kids/")
            if not html:
                self.logger.error("  Failed to fetch %s", cat)
                continue

            cat_links = self._extract_links(html)
            links.extend(cat_links)
            self.logger.info("  Main page: %d links", len(cat_links))

            total_pages = self._get_total_pages(html, cat)
            self.logger.info("  Total pages: %d", total_pages)

            consecutive_fails = 0
            for pn in range(1, total_pages + 1):
                page_url = f"{self.BASE}/kids/category/{cat}-page{pn}.html"
                delay(URDUPOINT_DELAY)
                ph = fetch_page(page_url, referer=cat_url)
                if not ph:
                    consecutive_fails += 1
                    if consecutive_fails >= 5:
                        self.logger.error(
                            "  %d consecutive failures at page %d — stopping %s",
                            consecutive_fails, pn, cat,
                        )
                        break
                    continue
                consecutive_fails = 0
                pl = self._extract_links(ph)
                links.extend(pl)
                if pn % 25 == 0:
                    self.logger.info(
                        "  %s p%d/%d  links=%d",
                        cat, pn, total_pages, len(links),
                    )

        self.logger.info("  Total collected: %d links", len(links))
        return links

    def _extract_links(self, html: str) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/kids/detail/" not in href:
                continue
            if any(x in href for x in (
                "/jokes/", "/puzzels/", "/recipes/", "/games/",
            )):
                continue
            full = urljoin(self.BASE, href)
            title = clean(a.get_text())
            if title:
                out.append((full, title))
        return out

    def _get_total_pages(self, html: str, cat: str) -> int:
        # Primary: find max page number from pagination links
        mx = 1
        for m2 in re.finditer(rf"{re.escape(cat)}-page(\d+)\.html", html):
            mx = max(mx, int(m2.group(1)))
        if mx > 1:
            return mx
        # Fallback: parse "Total N Records" text
        m = re.search(r"Total\s+(\d+)\s+Records", html)
        if m:
            return (int(m.group(1)) + 11) // 12  # 12 per page
        return mx

    # ── story parsing ────────────────────────────────
    def parse_story(self, url, title, html):
        soup = BeautifulSoup(html, "lxml")

        # ── Title: prefer Urdu h2 inside shad_box ──
        story_title = title
        for h in soup.find_all("h2", class_=re.compile(r"urdu", re.I)):
            t = clean(h.get_text())
            if t and re.search(r"[\u0600-\u06FF]", t):
                t = re.sub(r"\s*-\s*تحریر نمبر\s*\d+", "", t)
                story_title = t
                break
        if story_title == title:
            for h in soup.find_all(["h1", "h2"]):
                t = clean(h.get_text())
                if re.search(r"[\u0600-\u06FF]", t):
                    t = re.sub(r"\s*-\s*تحریر نمبر\s*\d+", "", t)
                    story_title = t
                    break

        # ── Category from URL ──
        category = ""
        cm = re.search(r"/kids/detail/([^/]+)/", url)
        if cm:
            category = cm.group(1).replace("-", " ").title()

        # ── Author: first line of txt_detail is often the author ──
        author = ""

        # ── Date from art_info_bar ──
        date_str = ""
        info_bar = soup.find("p", class_=re.compile(r"art_info_bar", re.I))
        if info_bar:
            date_str = clean(info_bar.get_text())
        if not date_str:
            for day in ("پیر", "منگل", "بدھ", "جمعرات", "جمعہ", "ہفتہ", "اتوار"):
                dm = re.search(rf"{day}\s+\d{{1,2}}\s+\S+\s+\d{{4}}", html)
                if dm:
                    date_str = clean(dm.group(0))
                    break

        # ── Content: primary selector is div.txt_detail ──
        paragraphs: list[str] = []

        container = soup.find("div", class_="txt_detail")
        if not container:
            # Fallback selectors
            container = (
                soup.find("div", class_=re.compile(
                    r"detail_main|detail-main|storyCont|story[-_]cont|"
                    r"article[-_]?body|content_detail",
                    re.I,
                ))
                or soup.find("article")
                or soup.find("div", class_=re.compile(r"col-lg-8|col-md-8", re.I))
            )

        target = container or soup.body or soup

        # Clean out non-story elements
        for junk in target.find_all(
            ["aside", "iframe", "script", "ins", "style", "figure", "form"],
        ):
            junk.decompose()

        first_urdu_para = True
        for el in target.find_all(["p", "div", "span"]):
            if el.find(["p", "div"]):
                continue
            t = clean(el.get_text())
            if not t or len(t) < 15:
                continue
            if not re.search(r"[\u0600-\u06FF]", t):
                continue
            if any(kw in t.lower() for kw in (
                "facebook", "twitter", "whatsapp", "pinterest",
                "browse more", "urdu jokes", "urdu paheliyan",
                "urdupoint.com", "copyright", "all rights",
                "advertisement", "disclaimer", "privacy policy",
            )):
                continue
            # First short Urdu paragraph in txt_detail is usually the author
            if first_urdu_para and len(t) < 40 and not author:
                author = t
                first_urdu_para = False
                continue
            first_urdu_para = False
            paragraphs.append(t)

        # Deduplicate neighbours
        deduped: list[str] = []
        for p in paragraphs:
            if not deduped or p != deduped[-1]:
                deduped.append(p)
        content = "\n\n".join(deduped)

        return self._make_entry(
            title=story_title, url=url, content=content,
            author=author, date=date_str, category=category,
            source="urdupoint.com",
        )


# ═════════════════════════════════════════════════════
# 3.  adabiduniya.com  —  strict h2-only link extraction
# ═════════════════════════════════════════════════════
class AdabiDuniyaScraper(BaseScraper):
    BASE = "https://adabiduniya.com"
    LISTING = f"{BASE}/urdu-short-story/"

    # Category/landing pages that are NOT individual stories
    SKIP_PATHS = {
        "urdu-afsana", "international-literature-in-urdu", "urdu-notes",
        "urdu-grammer", "urdu-novel", "urdu-essay", "urdu-poetry",
        "best-urdu-books", "urdu-short-story",
    }

    def __init__(self, num_threads: int):
        super().__init__("adabiduniya", "adabiduniya.json", num_threads)

    # ── link collection ──────────────────────────────
    def collect_links(self):
        links: list[tuple[str, str]] = []
        page = 1

        while True:
            url = self.LISTING if page == 1 else f"{self.LISTING}page/{page}/"
            self.logger.info("  listing page %d", page)
            html = fetch_page(url)
            if not html:
                break
            soup = BeautifulSoup(html, "lxml")

            # Only extract story links from <h2> headings in the main
            # content area.  This avoids sidebar, footer, and nav links.
            main = (
                soup.find("main")
                or soup.find("div", class_=re.compile(
                    r"content-area|main-content|site-content", re.I,
                ))
                or soup.find("div", id=re.compile(r"content|primary|main", re.I))
                or soup  # fallback
            )

            found = 0
            for h2 in main.find_all("h2"):
                a = h2.find("a", href=True)
                if not a:
                    continue
                href = a["href"].rstrip("/")
                if not href.startswith(self.BASE):
                    continue
                path = href.replace(self.BASE, "").strip("/")
                if not path:
                    continue
                if path in self.SKIP_PATHS:
                    continue
                if any(
                    path.startswith(pfx)
                    for pfx in (
                        "category/", "tag/", "author/", "page/",
                        "contact", "privacy", "about", "disclaimer",
                        "terms", "wp-content", "urdu-short-story/page",
                    )
                ):
                    continue
                title = clean(a.get_text())
                if title and len(title) > 3:
                    links.append((href, title))
                    found += 1

            self.logger.info("  page %d → %d stories", page, found)
            if found == 0:
                break

            has_next = bool(
                soup.find("a", href=re.compile(rf"page/{page + 1}"))
                or soup.find("a", class_=re.compile(r"next", re.I))
            )
            if not has_next:
                self.logger.info("  last page at %d", page)
                break
            page += 1
            delay()

        return links

    # ── story parsing ────────────────────────────────
    def parse_story(self, url, title, html):
        soup = BeautifulSoup(html, "lxml")

        # ── Title: prefer Urdu h3 inside entry-content ──
        story_title = title
        entry = (
            soup.find("div", class_=re.compile(r"entry[-_]content", re.I))
            or soup.find("div", class_=re.compile(r"post[-_]content", re.I))
            or soup.find("article")
        )
        if entry:
            h3 = entry.find("h3")
            if h3:
                t = clean(h3.get_text())
                if t and is_urdu(t, 0.3):
                    story_title = t
                h3.decompose()  # remove so it won't duplicate in content
        else:
            # no entry-content found at all
            h1 = soup.find("h1")
            if h1:
                story_title = clean(h1.get_text())

        # ── Author ──
        author = ""
        for el in soup.find_all(["a", "span", "div"]):
            cls = " ".join(el.get("class", []))
            if "author" in cls.lower():
                author = clean(el.get_text())
                break

        # ── Date ──
        date_str = ""
        time_el = soup.find("time")
        if time_el:
            date_str = time_el.get("datetime", clean(time_el.get_text()))
        if not date_str:
            for el in soup.find_all("span", class_=re.compile(r"date|time", re.I)):
                date_str = clean(el.get_text())
                break

        # ── Category ──
        category = ""
        cat_el = soup.find("a", attrs={"rel": "category tag"})
        if not cat_el:
            cat_el = soup.find("span", class_=re.compile(r"cat", re.I))
        if cat_el:
            category = clean(cat_el.get_text())

        # ── Content ──
        paragraphs: list[str] = []
        container = entry  # already found above
        if not container:
            container = soup.find("article")

        if container:
            # Remove unwanted sections
            for junk in container.find_all(
                ["div", "aside", "section", "nav", "footer",
                 "script", "style", "iframe", "ins", "figure"],
                class_=re.compile(
                    r"share|social|related|comment|sidebar|ad|widget|"
                    r"yarpp|sharedaddy|jp-relatedposts|author-box|"
                    r"nav-links|post-navigation",
                    re.I,
                ),
            ):
                junk.decompose()

            for el in container.find_all(["p", "blockquote", "li"]):
                t = clean(el.get_text())
                if not t or len(t) < 10:
                    continue
                # Skip promotional / boilerplate
                if any(kw in t for kw in (
                    "adabiduniya.com", "ہماری ویب سائٹ",
                    "ابھی وزٹ کریں", "پر ضرور آئیں",
                    "ادبی مواد دستیاب", "نئی کہانیاں پڑھنے کے لیے",
                    "ادبی دنیا –", "ادبی دنیا–",
                    "موٹیویشنل کہانیاں", "اردو موٹیویشنل",
                    "اخلاقی قصے اور ادبی مواد",
                    "لوک کہانیاں، مزاحیہ قصے",
                )):
                    continue
                if any(kw in t.lower() for kw in (
                    "subscribe", "copyright", "leave a reply",
                    "email", "required fields", "post comment",
                    "اس موضوع پر مزید",
                )):
                    continue
                # Only keep text that has meaningful Urdu content
                if len(t) > 20 and not is_urdu(t, 0.15):
                    continue
                paragraphs.append(t)

        content = "\n\n".join(paragraphs)

        # Must have substantial Urdu story content
        if not is_urdu(content, 0.4):
            return None

        return self._make_entry(
            title=story_title, url=url, content=content,
            author=author, date=date_str, category=category,
            source="adabiduniya.com",
        )


# ═════════════════════════════════════════════════════
#  process entry point
# ═════════════════════════════════════════════════════
def run_scraper(scraper_cls, num_threads: int):
    setup_logging()
    scraper = scraper_cls(num_threads)
    try:
        scraper.run()
    except KeyboardInterrupt:
        scraper.save()
        logging.getLogger(scraper.name).info("Interrupted — progress saved.")
    except Exception as exc:
        scraper.save()
        logging.getLogger(scraper.name).error("Fatal: %s", exc, exc_info=True)


# ═════════════════════════════════════════════════════
#  main
# ═════════════════════════════════════════════════════
def main():
    setup_logging()
    logger = logging.getLogger("main")

    threads, cores, ram = get_optimal_threads()
    logger.info("System: %d cores, %.1f GB avail RAM", cores, ram)
    logger.info("Config: 3 processes × %d threads (urdupoint: %d)", threads, max(2, threads // 2))
    logger.info("Data dir: %s", DATA_DIR)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    scrapers = [
        (MilkyStoryScraper, threads),
        (UrduPointScraper, max(2, threads // 2)),      # fewer threads → rate-limit
        (AdabiDuniyaScraper, threads),
    ]

    procs: list[multiprocessing.Process] = []
    for cls, nt in scrapers:
        p = multiprocessing.Process(
            target=run_scraper, args=(cls, nt), name=cls.__name__,
        )
        procs.append(p)
        p.start()
        logger.info("Started %s (pid %d, %d threads)", p.name, p.pid, nt)

    try:
        for p in procs:
            p.join()
            logger.info("Process %s finished (exit %s)", p.name, p.exitcode)
    except KeyboardInterrupt:
        logger.info("Ctrl+C — terminating …")
        for p in procs:
            if p.is_alive():
                p.terminate()
        for p in procs:
            p.join(timeout=10)
        logger.info("All terminated. Partial data saved.")

    logger.info("=== All scrapers finished ===")
    for name in ("milkystory", "urdupoint", "adabiduniya"):
        fp = DATA_DIR / f"{name}.json"
        if fp.exists():
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info("  %s: %d stories", name, len(data))
        else:
            logger.info("  %s: no data", name)


if __name__ == "__main__":
    main()
