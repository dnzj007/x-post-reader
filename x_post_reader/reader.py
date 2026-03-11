from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, asdict
from typing import List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


OEMBED_BASE = "https://publish.twitter.com/oembed?omit_script=true&url="
STATUS_RE = re.compile(r"^/(?:[^/]+)/status/(\d+)(?:/.*)?$")
ANCHOR_RE = re.compile(r"<a [^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", re.S | re.I)
PARAGRAPH_RE = re.compile(r"<p [^>]*>(.*?)</p>", re.S | re.I)
DATE_RE = re.compile(r"</p>\s*&mdash;.*?<a [^>]*>(.*?)</a>", re.S | re.I)
TCO_RE = re.compile(r"https://t\.co/[A-Za-z0-9]+")


class XPostReaderError(RuntimeError):
    pass


@dataclass
class ExpandedLink:
    short_url: str
    final_url: str


@dataclass
class PostResult:
    author_name: str
    author_url: str
    canonical_url: str
    post_text: str
    published_at: str
    expanded_links: List[ExpandedLink]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["expanded_links"] = [asdict(item) for item in self.expanded_links]
        return data


def normalize_status_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise XPostReaderError("URL must start with http:// or https://")
    if parsed.netloc not in {"x.com", "twitter.com", "www.twitter.com", "www.x.com"}:
        raise XPostReaderError("Only x.com or twitter.com status URLs are supported")
    match = STATUS_RE.match(parsed.path)
    if not match:
        raise XPostReaderError("Only public status URLs are supported")
    username = parsed.path.strip("/").split("/")[0]
    status_id = match.group(1)
    return f"https://twitter.com/{username}/status/{status_id}"


def _fetch_text(url: str, timeout: int = 20, method: str = "GET") -> str:
    request = Request(url, headers={"User-Agent": "x-post-reader/0.1 (+https://github.com)"}, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        raise XPostReaderError(f"HTTP {exc.code} while fetching {url}") from exc
    except URLError as exc:
        raise XPostReaderError(f"Network error while fetching {url}: {exc.reason}") from exc


def fetch_oembed(status_url: str, timeout: int = 20) -> dict:
    canonical_url = normalize_status_url(status_url)
    oembed_url = OEMBED_BASE + quote(canonical_url, safe="")
    payload = _fetch_text(oembed_url, timeout=timeout)
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise XPostReaderError("oEmbed returned invalid JSON") from exc


def _strip_tags(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def extract_post_text_from_html(blockquote_html: str) -> str:
    paragraph_match = PARAGRAPH_RE.search(blockquote_html)
    if not paragraph_match:
        raise XPostReaderError("Unable to extract post text from oEmbed HTML")
    paragraph_html = paragraph_match.group(1)

    def replace_anchor(match: re.Match) -> str:
        href = html.unescape(match.group(1))
        label = _strip_tags(match.group(2))
        if href.startswith("https://t.co/"):
            return href
        return label or href

    paragraph_html = ANCHOR_RE.sub(replace_anchor, paragraph_html)
    text = _strip_tags(paragraph_html)
    return re.sub(r"\s+", " ", text).strip()


def extract_published_at(blockquote_html: str) -> str:
    match = DATE_RE.search(blockquote_html)
    return html.unescape(match.group(1)).strip() if match else ""


def expand_link(url: str, timeout: int = 20) -> str:
    headers = {"User-Agent": "x-post-reader/0.1 (+https://github.com)"}
    for method in ("HEAD", "GET"):
        request = Request(url, headers=headers, method=method)
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.geturl()
        except Exception:
            continue
    return url


def read_post(status_url: str, expand_links: bool = False, timeout: int = 20) -> PostResult:
    payload = fetch_oembed(status_url, timeout=timeout)
    blockquote_html = payload.get("html", "")
    if not blockquote_html:
        raise XPostReaderError("oEmbed returned no HTML content")

    post_text = extract_post_text_from_html(blockquote_html)
    links: List[ExpandedLink] = []
    if expand_links:
        for short_url in TCO_RE.findall(post_text):
            links.append(ExpandedLink(short_url=short_url, final_url=expand_link(short_url, timeout=timeout)))

    return PostResult(
        author_name=payload.get("author_name", ""),
        author_url=payload.get("author_url", ""),
        canonical_url=payload.get("url", normalize_status_url(status_url)),
        post_text=post_text,
        published_at=extract_published_at(blockquote_html),
        expanded_links=links,
    )
