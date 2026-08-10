#!/usr/bin/env python3
"""Fetch one approved web page with persistent crawl guards."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

MAX_MARKDOWN_BYTES = 40 * 1024
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


def load_state(path: Path | None) -> dict:
    if path and path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("crawl state must be a JSON object")
        return data
    return {}


def fetch(url: str) -> dict:
    request = Request(url, headers={
        "User-Agent": "okf-manager-codex/0.2 (+https://github.com/DrMarty/skills)",
        "Accept": "text/html,*/*;q=0.5",
    })
    with urlopen(request, timeout=10) as response:
        content_type = response.headers.get("Content-Type", "")
        final_url = response.geturl() or url
        body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError(f"response exceeds {MAX_RESPONSE_BYTES} bytes")
    if "html" not in content_type.lower():
        raise ValueError(f"non-HTML content-type: {content_type or 'unknown'}")
    soup = BeautifulSoup(body.decode("utf-8", errors="replace"), "lxml")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    links: list[str] = []
    seen: set[str] = set()
    for element in soup.find_all("a", href=True):
        absolute, _ = urldefrag(urljoin(final_url, str(element["href"])))
        if urlparse(absolute).scheme not in {"http", "https"} or absolute in seen:
            continue
        seen.add(absolute)
        links.append(absolute)
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    markdown = soup.get_text("\n", strip=True)
    encoded = markdown.encode("utf-8", errors="replace")
    if len(encoded) > MAX_MARKDOWN_BYTES:
        markdown = encoded[:MAX_MARKDOWN_BYTES].decode("utf-8", errors="ignore") + "\n\n[...truncated...]"
    return {"url": final_url, "title": title, "markdown": markdown, "links": links}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Fetch an approved page for OKF ingestion")
    parser.add_argument("url")
    parser.add_argument("--state", help="Persistent JSON crawl state")
    parser.add_argument("--seed", action="append", default=[])
    parser.add_argument("--allowed-host", action="append", default=[])
    parser.add_argument("--allowed-path-prefix", action="append", default=[])
    parser.add_argument("--denied-path-substring", action="append", default=[])
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--reset-state", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args(argv[1:])
    state_path = Path(args.state).expanduser().resolve() if args.state else None
    try:
        state = {} if args.reset_state else load_state(state_path)
        seeds = args.seed or state.get("seeds") or [args.url]
        hosts = set(args.allowed_host or state.get("allowed_hosts") or [urlparse(seed).netloc for seed in seeds])
        prefixes = tuple(args.allowed_path_prefix or state.get("allowed_path_prefixes") or ())
        denied = tuple(args.denied_path_substring or state.get("denied_path_substrings") or ())
        max_pages = int(args.max_pages if args.max_pages != 100 or "max_pages" not in state else state["max_pages"])
        max_depth = int(args.max_depth if args.max_depth != 2 or "max_depth" not in state else state["max_depth"])
        visited = set(state.get("visited") or [])
        depths = dict(state.get("url_depth") or {seed: 0 for seed in seeds})
        fetched_count = int(state.get("fetched_count") or 0)
        parsed = urlparse(args.url)
        path = parsed.path or "/"
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"unsupported scheme: {parsed.scheme or '(none)'}")
        if hosts and parsed.netloc not in hosts:
            raise ValueError(f"host not allowed: {parsed.netloc}")
        if prefixes and not any(path.startswith(prefix) for prefix in prefixes):
            raise ValueError(f"path not in allowed prefixes: {path}")
        if any(part and part in path for part in denied):
            raise ValueError(f"path is denied: {path}")
        if args.url in visited:
            raise ValueError("already fetched in this crawl state")
        if fetched_count >= max_pages:
            raise ValueError("max_pages reached")
        if args.url not in depths:
            raise ValueError("URL is not reachable from an approved seed")
        if int(depths[args.url]) > max_depth:
            raise ValueError(f"depth {depths[args.url]} exceeds max_depth {max_depth}")
        page = fetch(args.url)
        if hosts and urlparse(page["url"]).netloc not in hosts:
            raise ValueError(f"redirected host not allowed: {urlparse(page['url']).netloc}")
        visited.add(args.url)
        fetched_count += 1
        for link in page["links"]:
            depths.setdefault(link, int(depths[args.url]) + 1)
        state = {
            "seeds": seeds,
            "allowed_hosts": sorted(hosts),
            "allowed_path_prefixes": list(prefixes),
            "denied_path_substrings": list(denied),
            "max_pages": max_pages,
            "max_depth": max_depth,
            "visited": sorted(visited),
            "fetched_count": fetched_count,
            "url_depth": depths,
        }
        if state_path:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        page.update({"depth": depths[args.url], "fetched_count": fetched_count, "max_pages": max_pages, "max_depth": max_depth})
        output = json.dumps(page, indent=2, ensure_ascii=False) + "\n"
        if args.out:
            out_path = Path(args.out).expanduser().resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output, encoding="utf-8")
        else:
            print(output, end="")
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "url": args.url, "error": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
