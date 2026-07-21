"""
Gaming news from RSS/Atom feeds for the manual poster.

Fetches a small set of reliable sources, normalizes entries, and builds
simple non-AI tweet drafts from headlines.
"""

from __future__ import annotations

import html
import hashlib
import os
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from time import mktime
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

import feedparser
import requests

from steam_deals import TWEET_MAX_LENGTH

USER_AGENT = "SteamDealBot/2.1.8 (+news reader; https://github.com/rfnco/steamdealbot)"
REQUEST_TIMEOUT = 20
DEFAULT_NEWS_LIMIT = 10
# Fetch a larger merged pool so Refresh can rotate to the next page.
NEWS_POOL_LIMIT = 80
# X counts each http(s) URL as this many characters regardless of real length.
TWITTER_URL_LENGTH = 23
NEWS_IMAGES_DIR = Path(__file__).resolve().parent / "images" / "news"

# Gaming-focused RSS/Atom sources (fetched with a browser-like User-Agent).
DEFAULT_FEEDS: List[Dict[str, str]] = [
    {
        "id": "stathetic",
        "name": "Stathetic Blog",
        "url": "https://stathetic.blogspot.com/feeds/posts/default?alt=rss",
    },
    {"id": "steam", "name": "Steam", "url": "https://store.steampowered.com/feeds/news.xml"},
    {
        "id": "steam_client",
        "name": "Steam Client",
        "url": "https://store.steampowered.com/feeds/news/app/593110/?l=english",
    },
    {"id": "pcgamer", "name": "PC Gamer", "url": "https://www.pcgamer.com/rss/"},
    {
        "id": "nintendolife",
        "name": "Nintendo Life",
        "url": "https://www.nintendolife.com/feeds/latest",
    },
    {
        "id": "rps",
        "name": "Rock Paper Shotgun",
        "url": "https://www.rockpapershotgun.com/feed",
    },
    {"id": "eurogamer", "name": "Eurogamer", "url": "https://www.eurogamer.net/feed"},
    {"id": "polygon", "name": "Polygon", "url": "https://www.polygon.com/rss/index.xml"},
    {"id": "xboxwire", "name": "Xbox Wire", "url": "https://news.xbox.com/en-us/feed/"},
    {
        "id": "playstation",
        "name": "PlayStation Blog",
        "url": "https://blog.playstation.com/feed/",
    },
    {"id": "gematsu", "name": "Gematsu", "url": "https://www.gematsu.com/feed"},
    {"id": "vg247", "name": "VG247", "url": "https://www.vg247.com/feed"},
    {"id": "ign", "name": "IGN", "url": "https://feeds.ign.com/ign/games-all"},
    {
        "id": "gamespot",
        "name": "GameSpot",
        "url": "https://www.gamespot.com/feeds/news/",
    },
]

# Pin a few of your own blog posts near the top so high-volume outlets don't bury them.
# Only include owned posts newer than this age (stale blog posts stay hidden).
OWNED_FEED_IDS = {"stathetic"}
OWNED_FEED_PIN_COUNT = 3
OWNED_FEED_MAX_AGE_DAYS = 2

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
_IMG_SRC_RE = re.compile(
    r'<img[^>]+src=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

# Rotate openers so Question/Hype drafts do not reuse the same line every time.
QUESTION_OPENERS = [
    "What's your take?",
    "Agree or disagree?",
    "Did you catch this?",
    "Thoughts?",
    "How are we feeling about this?",
    "Anyone else seeing this?",
    "Worth weighing in?",
    "Does this change anything for you?",
    "Hype or overblown?",
    "Playing this weekend or skipping?",
]

HYPE_OPENERS = [
    "Hot off the feed:",
    "Big one today:",
    "Worth a look:",
    "This just hit:",
    "Gaming news desk:",
    "Fresh headline:",
    "On the timeline:",
    "Passing this along:",
    "Just dropped:",
    "Don't sleep on this:",
]


def _strip_html(value: str) -> str:
    text = _TAG_RE.sub(" ", value or "")
    text = html.unescape(text)
    return _SPACE_RE.sub(" ", text).strip()


def _parse_published(entry) -> Optional[datetime]:
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            try:
                return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
            except (OverflowError, ValueError, TypeError, OSError):
                pass

    for key in ("published", "updated"):
        raw = entry.get(key)
        if not raw:
            continue
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (TypeError, ValueError, IndexError, OverflowError):
            continue
    return None


def _entry_link(entry) -> str:
    link = (entry.get("link") or "").strip()
    if link:
        return link
    for item in entry.get("links") or []:
        href = (item.get("href") or "").strip()
        if href:
            return href
    return ""


def _media_type_hint(url: str, declared_type: str = "", medium: str = "") -> str:
    combined = f"{declared_type} {medium} {url}".lower()
    if any(token in combined for token in ("video", ".mp4", ".webm", ".mov", "m3u8")):
        return "video"
    if any(token in combined for token in ("image", ".jpg", ".jpeg", ".png", ".webp", ".gif")):
        return "image"
    return ""


def _collect_media_candidates(entry) -> List[Tuple[str, str, int]]:
    """Return (url, kind, preference) candidates. Higher preference wins."""
    candidates: List[Tuple[str, str, int]] = []

    def add(url: str, declared_type: str = "", medium: str = "", preference: int = 0) -> None:
        url = (url or "").strip()
        if not url.startswith("http"):
            return
        kind = _media_type_hint(url, declared_type, medium)
        if not kind:
            return
        # Prefer larger / explicit media:content over tiny thumbnails.
        score = preference
        lower = url.lower()
        if "large" in lower or "1280" in lower or "original" in lower:
            score += 5
        if "small" in lower or "thumb" in lower or "width=69" in lower:
            score -= 3
        candidates.append((url, kind, score))

    for item in entry.get("media_content") or []:
        add(
            item.get("url") or "",
            item.get("type") or "",
            item.get("medium") or "",
            preference=10,
        )

    for item in entry.get("media_thumbnail") or []:
        add(item.get("url") or "", "image/jpeg", "image", preference=2)

    for item in entry.get("enclosures") or []:
        add(
            item.get("href") or item.get("url") or "",
            item.get("type") or "",
            "",
            preference=8,
        )

    # Fall back to first <img> in HTML content/summary when feeds omit media tags.
    html_blobs = []
    for block in entry.get("content") or []:
        html_blobs.append(block.get("value") or "")
    html_blobs.append(entry.get("summary") or "")
    html_blobs.append(entry.get("description") or "")
    for blob in html_blobs:
        match = _IMG_SRC_RE.search(blob or "")
        if match:
            add(match.group(1), "image", "image", preference=1)
            break

    return candidates


def extract_media(entry) -> Dict[str, Optional[str]]:
    candidates = _collect_media_candidates(entry)
    image_url = None
    video_url = None
    for url, kind, _score in sorted(candidates, key=lambda row: row[2], reverse=True):
        if kind == "image" and not image_url:
            image_url = url
        elif kind == "video" and not video_url:
            video_url = url
        if image_url and video_url:
            break
    return {"image_url": image_url, "video_url": video_url}


def normalize_entry(entry, source_name: str, source_id: str) -> Optional[Dict]:
    title = _strip_html(entry.get("title") or "")
    url = _entry_link(entry)
    if not title or not url:
        return None

    summary = _strip_html(entry.get("summary") or entry.get("description") or "")
    if len(summary) > 320:
        summary = summary[:317].rstrip() + "..."

    media = extract_media(entry)
    published = _parse_published(entry)
    return {
        "source": source_name,
        "source_id": source_id,
        "title": title,
        "url": url,
        "published": published,
        "summary": summary,
        "image_url": media["image_url"],
        "video_url": media["video_url"],
    }


def format_published_age(published: Optional[datetime], now: Optional[datetime] = None) -> str:
    if not published:
        return "unknown time"
    now = now or datetime.now(timezone.utc)
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    delta = now - published.astimezone(timezone.utc)
    seconds = int(delta.total_seconds())
    if seconds < 0:
        return "just now"
    if seconds < 3600:
        minutes = max(1, seconds // 60)
        return f"{minutes}m ago"
    if seconds < 86400:
        hours = seconds // 3600
        return f"{hours}h ago"
    days = seconds // 86400
    return f"{days}d ago"


def media_badge(item: Dict) -> str:
    parts = []
    if item.get("image_url"):
        parts.append("img")
    if item.get("video_url"):
        parts.append("vid")
    if not parts:
        return ""
    return "[" + "+".join(parts) + "]"


def fetch_feed(feed: Dict[str, str], session: Optional[requests.Session] = None) -> List[Dict]:
    sess = session or requests.Session()
    response = sess.get(
        feed["url"],
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    parsed = feedparser.parse(response.content)
    items: List[Dict] = []
    for entry in parsed.entries:
        item = normalize_entry(entry, feed["name"], feed["id"])
        if item:
            items.append(item)
    return items


def _owned_feed_is_fresh(item: Dict, now: Optional[datetime] = None) -> bool:
    """Owned-blog posts only appear when newer than OWNED_FEED_MAX_AGE_DAYS."""
    published = item.get("published")
    if not published:
        return False
    now = now or datetime.now(timezone.utc)
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    age = now - published.astimezone(timezone.utc)
    return age.total_seconds() < (OWNED_FEED_MAX_AGE_DAYS * 86400)


def _filter_and_prioritize_owned_feeds(items: List[Dict]) -> List[Dict]:
    """Drop stale owned-blog posts; pin a few fresh ones near the top."""
    if not items or not OWNED_FEED_IDS:
        return items

    now = datetime.now(timezone.utc)
    fresh_owned: List[Dict] = []
    others: List[Dict] = []
    for item in items:
        if item.get("source_id") in OWNED_FEED_IDS:
            if _owned_feed_is_fresh(item, now=now):
                fresh_owned.append(item)
            # else: hide stale owned posts entirely
        else:
            others.append(item)

    if not fresh_owned or OWNED_FEED_PIN_COUNT <= 0:
        return fresh_owned + others if fresh_owned else others

    pin = fresh_owned[:OWNED_FEED_PIN_COUNT]
    pinned_urls = {(item.get("url") or "").rstrip("/").lower() for item in pin}
    rest = [
        item
        for item in (fresh_owned + others)
        if (item.get("url") or "").rstrip("/").lower() not in pinned_urls
    ]
    return pin + rest


def fetch_news_pool(
    feeds: Optional[Sequence[Dict[str, str]]] = None,
    pool_limit: int = NEWS_POOL_LIMIT,
) -> Tuple[List[Dict], List[str]]:
    """Fetch a larger newest-first pool for paging. Returns (items, errors)."""
    selected = list(feeds or DEFAULT_FEEDS)
    session = requests.Session()
    merged: List[Dict] = []
    errors: List[str] = []

    for feed in selected:
        try:
            merged.extend(fetch_feed(feed, session=session))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{feed['name']}: {exc}")

    seen = set()
    unique: List[Dict] = []
    for item in merged:
        key = item["url"].rstrip("/").lower() or item["title"].lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    unique.sort(
        key=lambda item: item["published"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    unique = _filter_and_prioritize_owned_feeds(unique)
    return unique[: max(1, pool_limit)], errors


def fetch_news(
    feeds: Optional[Sequence[Dict[str, str]]] = None,
    limit: int = DEFAULT_NEWS_LIMIT,
    offset: int = 0,
) -> List[Dict]:
    """Fetch and merge news from configured feeds, newest first.

    Use ``offset`` to page through results (Refresh in the manual poster).
    """
    pool, errors = fetch_news_pool(feeds=feeds, pool_limit=max(NEWS_POOL_LIMIT, offset + limit))
    page_size = max(1, limit)
    start = max(0, offset)
    if start >= len(pool) and pool:
        start = 0
    result = pool[start : start + page_size]

    for item in result:
        item["_pool_size"] = len(pool)
        item["_offset"] = start
    if errors:
        for item in result:
            item.setdefault("_fetch_errors", errors)
        if not result:
            raise RuntimeError("; ".join(errors))
    return result


def weighted_tweet_length(text: str) -> int:
    """Approximate X character count (each URL counts as TWITTER_URL_LENGTH)."""
    length = 0
    last = 0
    for match in _URL_RE.finditer(text):
        length += len(text[last:match.start()])
        length += TWITTER_URL_LENGTH
        last = match.end()
    length += len(text[last:])
    return length


def _fit_plain(text: str, budget: int) -> str:
    text = text.strip()
    if budget <= 0:
        return ""
    if len(text) <= budget:
        return text
    if budget <= 3:
        return text[:budget]
    trimmed = text[: budget - 3].rstrip()
    if " " in trimmed and len(trimmed) > 20:
        trimmed = trimmed.rsplit(" ", 1)[0]
    return trimmed.rstrip() + "..."


def _hook_from_summary(summary: str, title: str, max_len: int = 110) -> str:
    """Short supporting line that is not just a repeat of the title."""
    summary = (summary or "").strip()
    if len(summary) < 40:
        return ""
    title_l = title.lower().strip()
    summary_l = summary.lower()
    if summary_l.startswith(title_l[:40]):
        return ""
    # Avoid dumping whole article blurbs into the tweet.
    sentence = summary.split(". ")[0].strip()
    if sentence.endswith("."):
        sentence = sentence[:-1]
    if len(sentence) < 40:
        return ""
    return _fit_plain(sentence, max_len)


def _compose_with_budget(parts_before_url: List[str], url: str, parts_after_url: List[str]) -> str:
    """Keep the full URL, but fit body text using X's weighted URL length."""
    before = "\n".join(part for part in parts_before_url if part is not None and part != "")
    after = "\n".join(part for part in parts_after_url if part is not None and part != "")

    if before:
        available_for_prefix = TWEET_MAX_LENGTH - (
            TWITTER_URL_LENGTH + (2 + len(after) if after else 0) + 2
        )
        fitted_prefix = _fit_plain(before, available_for_prefix)
        body = f"{fitted_prefix}\n\n{url}"
    else:
        body = url
    if after:
        remaining = TWEET_MAX_LENGTH - weighted_tweet_length(body) - 2
        fitted_after = _fit_plain(after, remaining)
        if fitted_after:
            body = f"{body}\n\n{fitted_after}"

    # Safety: if somehow still over (weird edge cases), trim prefix further.
    while weighted_tweet_length(body) > TWEET_MAX_LENGTH and "\n\n" in body:
        head, _sep, rest = body.partition("\n\n")
        if not head or head.startswith("http"):
            break
        head = _fit_plain(head, max(0, len(head) - 16))
        body = f"{head}\n\n{rest}" if head else rest
    return body


def _pick_opener(pool: Sequence[str], seed: str) -> str:
    """Stable per-article pick so reopening the same story keeps the same opener."""
    digest = hashlib.md5(seed.encode("utf-8")).hexdigest()
    return pool[int(digest[:8], 16) % len(pool)]


def format_news_tweets(item: Dict) -> List[Dict[str, str]]:
    """Return non-AI tweet drafts with varied Question/Hype openers."""
    title = item["title"].strip()
    source = item["source"]
    url = item["url"]
    hook = _hook_from_summary(item.get("summary") or "", title)
    seed = url or title

    question_opener = _pick_opener(QUESTION_OPENERS, f"question:{seed}")
    hype_opener = _pick_opener(HYPE_OPENERS, f"hype:{seed}")

    drafts_spec = [
        (
            "Headline",
            [title, hook] if hook else [title],
            f"Via {source} · #GamingNews",
        ),
        (
            "Question",
            [f"{question_opener}\n{title}", hook] if hook else [f"{question_opener}\n{title}"],
            "#Gaming",
        ),
        (
            "Hype",
            [f"{hype_opener}\n{title}"],
            f"Source: {source}",
        ),
    ]

    drafts: List[Dict[str, str]] = []
    for label, before_parts, after in drafts_spec:
        before_block = "\n".join(p for p in before_parts if p)
        text = _compose_with_budget([before_block], url, [after])
        drafts.append(
            {
                "label": label,
                "text": text,
                "weighted_length": weighted_tweet_length(text),
            }
        )
    return drafts


class NewsImageBlockedError(RuntimeError):
    """Raised when an image CDN returns a bot challenge (e.g. Cloudflare)."""

    def __init__(self, message: str, image_url: str = ""):
        super().__init__(message)
        self.image_url = image_url


def _looks_like_image_bytes(content: bytes, content_type: str) -> bool:
    ctype = (content_type or "").lower()
    if content_type and "html" in ctype:
        return False
    if content[:20].lstrip().lower().startswith((b"<!doctype", b"<html")):
        return False
    if b"just a moment" in content[:800].lower() or b"cloudflare" in content[:800].lower():
        return False
    if ctype.startswith("image/"):
        return True
    # Magic bytes for common formats when CDN omits/mislabels content-type.
    if content.startswith(b"\xff\xd8\xff"):
        return True  # jpeg
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if content.startswith((b"GIF87a", b"GIF89a")):
        return True
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return True
    return False


def save_news_image(item: Dict, destination_dir: Optional[Path] = None) -> Optional[str]:
    """Download the article image when available. Returns saved path or None."""
    image_url = item.get("image_url")
    if not image_url:
        return None

    dest_dir = Path(destination_dir or NEWS_IMAGES_DIR)
    dest_dir.mkdir(parents=True, exist_ok=True)

    parsed = urlparse(image_url)
    ext = os.path.splitext(parsed.path)[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        ext = ".jpg"

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    source_id = re.sub(r"[^a-z0-9]+", "-", (item.get("source_id") or "news").lower()).strip("-")
    slug = re.sub(r"[^a-z0-9]+", "-", item["title"].lower()).strip("-")[:48] or "story"
    filename = f"{stamp}-{source_id}-{slug}{ext}"
    path = dest_dir / filename

    article_url = (item.get("url") or "").strip()
    referer = article_url or f"{parsed.scheme}://{parsed.netloc}/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Referer": referer,
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = requests.get(
        image_url,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )
    content_type = response.headers.get("Content-Type", "")
    if response.status_code == 403 or not _looks_like_image_bytes(
        response.content, content_type
    ):
        host = parsed.netloc or "this source"
        raise NewsImageBlockedError(
            f"{host} blocked the image download (often Cloudflare). "
            "Open the image URL in a browser and save it manually.",
            image_url=image_url,
        )
    response.raise_for_status()
    path.write_bytes(response.content)
    return str(path)
