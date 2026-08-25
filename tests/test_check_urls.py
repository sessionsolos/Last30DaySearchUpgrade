#!/usr/bin/env python3
"""Tests for check_urls.normalize and the pass/fail behavior.

Run: python3 tests/test_check_urls.py

Two failure modes, and they are not equally bad.

A FALSE REJECT flags a real citation. The skill tells the model not to send
around a failure, so a legitimate link gets stripped from a brief. Annoying.

A FALSE ACCEPT passes a fabricated citation. That is the one thing this script
exists to prevent, so every case below that guards against it is load-bearing.
Both shipped in the first version because it was hand-checked on three cases the
author chose rather than tested.
"""

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skill", "scripts"))
from check_urls import normalize, extract  # noqa: E402

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "skill", "scripts", "check_urls.py")

# Pairs that must normalize to the same value. A miss here is a false reject.
SAME = [
    ("youtu.be short form",
     "https://youtu.be/dQw4w9WgXcQ",
     "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    ("youtu.be with timestamp",
     "https://youtu.be/dQw4w9WgXcQ?t=42",
     "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    ("youtube feature param",
     "https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=shared",
     "https://youtube.com/watch?v=dQw4w9WgXcQ"),
    ("youtube mobile host",
     "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
     "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    ("old.reddit",
     "https://old.reddit.com/r/Luthier/comments/1abc234/neck/",
     "https://www.reddit.com/r/Luthier/comments/1abc234/neck"),
    ("np.reddit",
     "https://np.reddit.com/r/Luthier/comments/1abc234/neck",
     "https://reddit.com/r/Luthier/comments/1abc234/neck"),
    ("twitter to x",
     "https://twitter.com/sessiontone/status/1899887766554433221",
     "https://x.com/sessiontone/status/1899887766554433221"),
    ("mobile twitter",
     "https://mobile.twitter.com/a/status/123",
     "https://x.com/a/status/123"),
    ("utm params stripped",
     "https://premierguitar.com/gear/review?utm_source=nl&utm_campaign=aug",
     "https://www.premierguitar.com/gear/review"),
    ("x share suffix",
     "https://x.com/a/status/123?s=20&t=abc",
     "https://x.com/a/status/123"),
    ("http vs https",
     "http://example.com/page",
     "https://example.com/page"),
    ("query order",
     "https://example.com/p?b=2&a=1",
     "https://example.com/p?a=1&b=2"),
    ("host case",
     "https://EXAMPLE.com/Page",
     "https://example.com/Page"),
    ("trailing sentence period",
     "https://example.com/page.",
     "https://example.com/page"),
]

# Pairs that must NOT collapse. A miss here is a false accept, the dangerous one.
DIFFERENT = [
    ("video id differing only in case",
     "https://www.youtube.com/watch?v=aBcDeFgHiJk",
     "https://www.youtube.com/watch?v=abcdefghijk"),
    ("path case",
     "https://example.com/Report",
     "https://example.com/report"),
    ("one digit off in a status id",
     "https://x.com/a/status/1899887766554433221",
     "https://x.com/a/status/1899887766554433229"),
    ("different reddit post",
     "https://reddit.com/r/Luthier/comments/1abc234/neck",
     "https://reddit.com/r/Luthier/comments/9zz999/frets"),
    ("different youtube video",
     "https://youtu.be/dQw4w9WgXcQ",
     "https://youtu.be/oHg5SJYRHA0"),
    ("different subreddit",
     "https://reddit.com/r/Luthier/comments/1abc234/neck",
     "https://reddit.com/r/Guitar/comments/1abc234/neck"),
    ("meaningful query value",
     "https://example.com/search?q=alpha",
     "https://example.com/search?q=beta"),
]

EXTRACT_CASES = [
    ("markdown link", "see [it](https://example.com/a) here", ["https://example.com/a"]),
    ("trailing comma", "at https://example.com/a, then", ["https://example.com/a"]),
    ("wrapped in parens", "(https://example.com/a)", ["https://example.com/a"]),
    ("bare in prose", "go to https://example.com/a now", ["https://example.com/a"]),
    ("no urls", "u/name said it plainly", []),
]


def run_cli(evidence: str, draft: str):
    with tempfile.TemporaryDirectory() as d:
        ev, dr = os.path.join(d, "e.txt"), os.path.join(d, "d.md")
        open(ev, "w").write(evidence)
        open(dr, "w").write(draft)
        p = subprocess.run(
            [sys.executable, SCRIPT, "--evidence", ev, "--draft", dr],
            capture_output=True, text=True,
        )
        return p.returncode, p.stdout


def main() -> int:
    failures = []

    for name, a, b in SAME:
        if normalize(a) != normalize(b):
            failures.append(
                f"FALSE REJECT [{name}]\n    {a}\n      -> {normalize(a)}\n"
                f"    {b}\n      -> {normalize(b)}"
            )

    for name, a, b in DIFFERENT:
        if normalize(a) == normalize(b):
            failures.append(
                f"FALSE ACCEPT [{name}] both normalize to {normalize(a)}\n"
                f"    {a}\n    {b}"
            )

    for name, text, expected in EXTRACT_CASES:
        got = extract(text)
        if got != expected:
            failures.append(f"EXTRACT [{name}] expected {expected}, got {got}")

    ev = "evidence https://reddit.com/r/a/comments/1abc/t and https://youtu.be/dQw4w9WgXcQ"

    code, _ = run_cli(ev, "per [thread](https://old.reddit.com/r/a/comments/1abc/t/)")
    if code != 0:
        failures.append("CLI rejected an honest draft (exit %d)" % code)

    code, out = run_cli(ev, "per https://reddit.com/r/a/comments/9zz999/fake")
    if code != 1:
        failures.append("CLI passed a fabricated URL (exit %d)" % code)

    code, out = run_cli(ev, "per [Premier Guitar]()")
    if code != 1:
        failures.append("CLI passed an empty markdown link (exit %d)" % code)

    code, _ = run_cli(ev, "per u/name and @handle, no links at all")
    if code != 0:
        failures.append("CLI rejected a draft with zero URLs (exit %d)" % code)

    total = len(SAME) + len(DIFFERENT) + len(EXTRACT_CASES) + 4
    if failures:
        print("\n\n".join(failures))
        print(f"\n{len(failures)} of {total} checks FAILED")
        return 1

    print(f"all {total} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
