#!/usr/bin/env python3
"""Fail a draft that cites a URL the research evidence never returned.

Usage:
    check_urls.py --evidence engine_stdout.txt --draft draft.md
    engine ... | check_urls.py --draft draft.md          # evidence on stdin

Exit codes:
    0  every URL in the draft appears in the evidence
    1  at least one URL was invented, or an empty markdown link was found
    2  bad invocation

The engine's stdout is the only source of truth. A URL that is not in it was
assembled by the model, which is the failure this exists to catch. Comparison is
on a lightly normalized form (scheme, case, tracking params, trailing slash) so a
real citation is not rejected over cosmetics, while an invented path or status id
still fails.
"""

from __future__ import annotations

import argparse
import re
import sys
from urllib.parse import parse_qsl, urlsplit, urlunsplit

# Bare URLs plus the target of a markdown link. Stops before characters that are
# almost always prose rather than part of the address.
_URL_RE = re.compile(r"https?://[^\s<>\"'`\]\)}]+")

# Empty markdown links: [Rolling Stone]() and friends.
_EMPTY_LINK_RE = re.compile(r"\[[^\]]*\]\(\s*\)")

# Punctuation that regularly rides along at the end of a sentence.
_TRAILING = ".,;:!?\u2026'\")]}>*_"

_TRACKING_PREFIXES = ("utm_",)
_TRACKING_KEYS = {
    "app", "feature", "fbclid", "gclid", "igshid", "mc_cid", "mc_eid",
    "pp", "ref", "ref_src", "ref_url", "s", "si", "spm", "share_id", "t",
}


def _strip_trailing(url: str) -> str:
    while url and url[-1] in _TRAILING:
        # Keep a closing paren that balances one inside the URL itself.
        if url[-1] == ")" and url.count("(") > url.count(")") - 1:
            break
        url = url[:-1]
    return url


def normalize(url: str) -> str:
    """Collapse cosmetic variation without collapsing meaningful difference.

    Host and scheme are case-insensitive per RFC 3986 and get lowercased. Path
    and query are NOT: a YouTube video id is case-sensitive base64url, so
    folding case there would make two different videos compare equal and let a
    fabricated link pass. Rejecting a real link is a bug. Accepting a fake one
    defeats the point of the tool.
    """
    url = _strip_trailing(url.strip())
    try:
        parts = urlsplit(url)
    except ValueError:
        return url

    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]

    path = parts.path
    query = parts.query

    # youtu.be/<id> and youtube.com/watch?v=<id> address the same video.
    if host == "youtu.be":
        video_id = path.lstrip("/").split("/")[0]
        if video_id:
            path, query = "/watch", f"v={video_id}"
        host = "youtube.com"

    # Reddit and X serve identical content under several front doors.
    host = {
        "old.reddit.com": "reddit.com",
        "new.reddit.com": "reddit.com",
        "np.reddit.com": "reddit.com",
        "m.reddit.com": "reddit.com",
        "twitter.com": "x.com",
        "mobile.twitter.com": "x.com",
        "nitter.net": "x.com",
        "m.youtube.com": "youtube.com",
        "music.youtube.com": "youtube.com",
    }.get(host, host)

    path = path.rstrip("/") or "/"

    pairs = [
        (k, v)
        for k, v in parse_qsl(query, keep_blank_values=True)
        if k.lower() not in _TRACKING_KEYS
        and not k.lower().startswith(_TRACKING_PREFIXES)
    ]
    pairs.sort()
    query_str = "&".join(f"{k}={v}" for k, v in pairs)

    return urlunsplit(("https", host, path, query_str, ""))


def extract(text: str) -> list[str]:
    seen: dict[str, str] = {}
    for raw in _URL_RE.findall(text):
        cleaned = _strip_trailing(raw)
        if not cleaned:
            continue
        seen.setdefault(normalize(cleaned), cleaned)
    return list(seen.values())


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence", default="-", help="Engine stdout file, or - for stdin")
    ap.add_argument("--draft", required=True, help="The synthesis you are about to send")
    ap.add_argument("--quiet", action="store_true", help="Print only failures")
    args = ap.parse_args()

    try:
        evidence_text = _read(args.evidence)
        draft_text = _read(args.draft)
    except OSError as exc:
        print(f"check_urls: {exc}", file=sys.stderr)
        return 2

    if not evidence_text.strip():
        print("check_urls: evidence is empty. Nothing to validate against.", file=sys.stderr)
        return 2

    allowed = {normalize(u) for u in extract(evidence_text)}
    cited = extract(draft_text)
    invented = [u for u in cited if normalize(u) not in allowed]
    empty_links = _EMPTY_LINK_RE.findall(draft_text)

    if invented or empty_links:
        print("FAIL: this draft cites sources the research did not return.\n")
        for url in invented:
            print(f"  fabricated  {url}")
        for link in empty_links:
            print(f"  empty link  {link}")
        print(
            "\nReplace each one with a plain label (u/name, @handle, r/sub, the "
            "publication name) or copy the exact URL from the evidence. Do not "
            "reconstruct a permalink or a status id."
        )
        return 1

    if not args.quiet:
        print(f"OK: {len(cited)} cited URL(s), all present in the evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
