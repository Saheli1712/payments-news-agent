"""Fetch payments news from Economic Times RSS feeds. Needs no API key."""

from __future__ import annotations

import html
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import feedparser
import requests
from bs4 import BeautifulSoup

from .sources import ET_RSS_INDEX, FEEDS, PAYMENTS_KEYWORDS, PAYMENTS_ONLY_FEEDS

USER_AGENT = "payments-news-agent/1.0 (+personal news digest; respects robots.txt)"
TIMEOUT = 20

_KEYWORD_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(PAYMENTS_KEYWORDS, key=len, reverse=True)) + r")s?\b",
    re.IGNORECASE,
)
_PAYMENT_KEYWORD_RE = re.compile(
    r"\b("
    + "|".join(
        re.escape(k)
        for k in sorted((keyword for keyword in PAYMENTS_KEYWORDS if keyword != "visa"), key=len, reverse=True)
    )
    + r")s?\b",
    re.IGNORECASE,
)
_WORK_VISA_RE = re.compile(
    r"\b(?:work\s+visas?|visa\s+holders?|employment\s+visa(?:\s+programmes?)?|"
    r"h[- ]?1b|immigration|permanent residency|green card)\b",
    re.IGNORECASE,
)


@dataclass
class NewsItem:
    headline: str
    link: str
    published: datetime | None
    summary: str
    source: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["published"] = self.published.isoformat() if self.published else None
        return d


class Fetcher:
    """HTTP access with a robots.txt check per host and a polite delay."""

    def __init__(self, session: requests.Session | None = None, delay: float = 1.0):
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        self.delay = delay
        self._robots: dict[str, RobotFileParser | None] = {}
        self._last = 0.0

    def allowed(self, url: str) -> bool:
        host = "{0.scheme}://{0.netloc}".format(urlparse(url))
        if host not in self._robots:
            rp = RobotFileParser()
            try:
                r = self._get_raw(host + "/robots.txt")
                if r.status_code >= 400:
                    rp = None  # no robots.txt: everything allowed
                else:
                    rp.parse(r.text.splitlines())
            except requests.RequestException:
                rp = None
            self._robots[host] = rp
        rp = self._robots[host]
        return rp is None or rp.can_fetch(USER_AGENT, url)

    def get(self, url: str) -> requests.Response:
        if not self.allowed(url):
            raise PermissionError(f"robots.txt disallows {url}")
        return self._get_raw(url)

    def _get_raw(self, url: str) -> requests.Response:
        wait = self.delay - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        try:
            return self.session.get(url, timeout=TIMEOUT)
        finally:
            self._last = time.monotonic()


def clean_text(raw: str) -> str:
    text = BeautifulSoup(html.unescape(raw or ""), "html.parser").get_text(" ")
    return re.sub(r"\s+", " ", text).strip()


def is_payments_story(item: NewsItem) -> bool:
    if item.source in PAYMENTS_ONLY_FEEDS:
        return True
    text = f"{item.headline} {item.summary}"
    if _WORK_VISA_RE.search(text) and not _PAYMENT_KEYWORD_RE.search(text):
        return False
    return bool(_KEYWORD_RE.search(text))


def parse_feed(content: bytes | str, source: str) -> list[NewsItem]:
    parsed = feedparser.parse(content)
    items = []
    for e in parsed.entries:
        stamp = e.get("published_parsed") or e.get("updated_parsed")
        published = datetime(*stamp[:6], tzinfo=timezone.utc) if stamp else None
        title = clean_text(e.get("title", ""))
        link = e.get("link", "").strip()
        if title and link:
            items.append(NewsItem(title, link, published, clean_text(e.get("summary", "")), source))
    return items


def discover_feeds(fetcher: Fetcher) -> dict[str, str]:
    """Find banking/fintech/payments feeds listed on ET's RSS index page."""
    try:
        r = fetcher.get(ET_RSS_INDEX)
        r.raise_for_status()
    except (requests.RequestException, PermissionError):
        return {}
    soup = BeautifulSoup(r.text, "html.parser")
    found = {}
    for a in soup.find_all("a", href=True):
        href = urljoin(ET_RSS_INDEX, a["href"])
        label = a.get_text(" ", strip=True)
        if "rssfeeds" in href and re.search(r"bank|financ|fintech|payment|bfsi", label + href, re.I):
            found[f"ET {label or 'feed'}"] = href
    return found


def fetch_payments_news(
    hours: float | None = 72,
    limit: int | None = 30,
    feeds: dict[str, str] | None = None,
    discover: bool = True,
    fetcher: Fetcher | None = None,
    errors: list[str] | None = None,
    successful_feeds: list[str] | None = None,
) -> list[NewsItem]:
    """Latest payments stories across ET feeds, newest first, de-duplicated."""
    fetcher = fetcher or Fetcher()
    feeds = dict(feeds or FEEDS)
    errors = errors if errors is not None else []
    successful_feeds = successful_feeds if successful_feeds is not None else []

    items: list[NewsItem] = []
    for name, url in feeds.items():
        try:
            r = fetcher.get(url)
            r.raise_for_status()
            successful_feeds.append(name)
            items.extend(parse_feed(r.content, name))
        except (requests.RequestException, PermissionError) as exc:
            errors.append(f"{name}: {exc}")

    # If every configured feed failed (ET changed its feed IDs), try the RSS index.
    if not successful_feeds and discover:
        for name, url in discover_feeds(fetcher).items():
            if url in feeds.values():
                continue
            try:
                r = fetcher.get(url)
                r.raise_for_status()
                successful_feeds.append(name)
                items.extend(parse_feed(r.content, name))
            except (requests.RequestException, PermissionError) as exc:
                errors.append(f"{name}: {exc}")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours) if hours else None
    seen, out = set(), []
    for it in sorted(items, key=lambda i: i.published or datetime.min.replace(tzinfo=timezone.utc), reverse=True):
        key = _canonical(it.link)
        if key in seen or not is_payments_story(it):
            continue
        if cutoff and it.published and it.published < cutoff:
            continue
        seen.add(key)
        out.append(it)
    return out[:limit] if limit else out


def fetch_article_text(url: str, fetcher: Fetcher | None = None, max_chars: int = 6000) -> str:
    """Plain text of an ET article page (for deeper summaries)."""
    fetcher = fetcher or Fetcher()
    r = fetcher.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    body = soup.find("div", class_=re.compile(r"artText|article|story", re.I)) or soup.find("article") or soup.body or soup
    paras = [p.get_text(" ", strip=True) for p in body.find_all("p")] or [body.get_text(" ", strip=True)]
    text = re.sub(r"\s+", " ", " ".join(p for p in paras if len(p) > 40)).strip()
    return text[:max_chars]


def _canonical(link: str) -> str:
    p = urlparse(link)
    return f"{p.netloc.removeprefix('www.')}{p.path}".rstrip("/").lower()
