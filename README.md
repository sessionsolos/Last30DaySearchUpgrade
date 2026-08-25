# Last30DaySearchUpgrade

A replacement instruction layer for the [last30days](https://github.com/mvanhorn/last30days-skill)
research skill. Same engine, different contract.

## What this is

last30days searches Reddit, X, YouTube, TikTok, Instagram, Hacker News, GitHub,
LinkedIn, and prediction markets for what people actually posted in the last 30
days, then hands an AI agent an evidence block scored by real engagement. The
Python engine behind it is solid work: about 57,000 lines, roughly 4,000 tests,
an 84 percent coverage floor, and zero pip dependencies.

The instruction file that ships with it is the problem. Three things:

**It is 2,295 lines.** Large enough that the model reads part of it and stops.
The upstream file documents this happening in its own incident notes, including
four consecutive runs that skipped a citation rule because it sat below the read
window. The maintainers' fix has been to move rules higher in the file rather
than split detail into reference files. There is one reference file in the whole
skill.

**It overrides your writing preferences by design.** The file states that its
formatting contract takes precedence over user-level style rules stored in
memory, and names a personal "no em dash" rule as an example of something it
beats. Output comes out in a fixed house voice: an emoji badge, a required
opening phrase, mandated bold lead-ins, an emoji source tree, a canned closing
line.

**Its anti-fabrication guard is a written rule.** The upstream notes log a run
that invented a citation URL. The mitigation is an instruction telling the model
not to reconstruct a status id. Nothing checks.

## What this replaces it with

| | upstream | this |
| --- | --- | --- |
| SKILL.md | 2,295 lines, ~57k tokens | 252 lines, ~2.8k tokens |
| Reference files | 1 | 2, loaded only when needed |
| Output voice | fixed house format | inherits your own style |
| URL validation | a written rule | `scripts/check_urls.py`, exits 1 on a fabricated citation |
| Engine coupling | SKILL.md ships inside the engine repo | separate checkout, `git pull` cannot clobber your contract |

Kept from upstream, because it is genuinely good design: pre-flight resolution of
real handles and subreddits before searching, honest per-source outcome states
that distinguish "returned nothing" from "authentication failed", the untrusted
content warning on scraped text, and the instruction to weave verbatim community
comments into the argument rather than dumping them in an appendix.

Added: a section on reading engagement numbers honestly. Upvotes measure
attention, not accuracy. A brigaded thread and a real consensus produce identical
counts.

## Install

Two pieces. The skill, and the engine it drives.

```bash
# 1. the skill
git clone https://github.com/sessionsolos/Last30DaySearchUpgrade.git
mkdir -p ~/.claude/skills/signal
cp -r Last30DaySearchUpgrade/skill/. ~/.claude/skills/signal/

# 2. the engine
git clone https://github.com/mvanhorn/last30days-skill.git ~/tools/last30days-engine
```

Point the skill somewhere else with `SIGNAL_ENGINE=/your/path`. Update the engine
with `git -C ~/tools/last30days-engine pull`, which pulls their fixes and leaves
your instruction file alone.

Other agent hosts: drop the same folder in `~/.codex/skills/signal/` or
`~/.agents/skills/signal/`.

## Requirements

Python 3.12 or newer. That is the only hard requirement.

Reddit, Hacker News, Polymarket, and GitHub work with no API keys at all, so a
bare install is already useful. `yt-dlp` on PATH adds YouTube search and
transcripts. Keys for X, TikTok, Instagram, and web search go in
`~/.config/last30days/.env`.

Check what is live:

```bash
python3 ~/tools/last30days-engine/skills/last30days/scripts/last30days.py --diagnose
```

See what the engine touches before running it, without reading cookies, writing
files, or making a research call:

```bash
python3 ~/tools/last30days-engine/skills/last30days/scripts/last30days.py --preflight
```

## Use it

Ask your agent for the community read on something.

```
what are people actually saying about Nano Banana Pro this month
how did the Framework 16 refresh land
Cursor vs Claude Code, what do people who use both say
```

The skill resolves handles and subreddits, writes a query plan, runs the engine,
and writes the answer in your voice with attributed verbatim quotes.

## Citation validation

The one thing the model is not trusted to self-police.

```bash
python3 scripts/check_urls.py --evidence engine_stdout.txt --draft draft.md
```

Exits 1 and names every URL in the draft that the research did not return, plus
any empty `[label]()` link. A status id that is one character wrong fails.
Cosmetic differences do not: `old.reddit.com`, `twitter.com`, `youtu.be`, `www.`,
trailing slashes, and `utm_` tracking parameters normalize before comparison, so
a real citation is never rejected over formatting.

Evidence can come in on stdin instead:

```bash
python3 last30days.py "topic" --emit=compact --plan "$PLAN" | tee /tmp/ev.txt
python3 scripts/check_urls.py --evidence /tmp/ev.txt --draft /tmp/draft.md
```

## Privacy

Research saves locally to `~/Documents/Last30Days` by default.

The engine's `--publish-html` and `--publish` flags upload the brief to a
third-party host and the resulting pages are public unless a password is set.
This skill instructs the agent never to run them unless you ask for publishing by
name. Competitor or named-person research landing on a public URL is not a
recoverable mistake.

Browser cookie extraction is scoped to the x.com domain and the `auth_token` and
`ct0` cookie names only, and does nothing at all unless `FROM_BROWSER` is set.

## Status

The instruction layer and the validator are written and the validator is tested
against fabricated status ids, invented permalinks, and empty links. This has not
been run end to end against a live topic. The query plan hitting a real apostrophe
or an unresolvable handle is untested, and the skill description is unoptimized,
so it may not always trigger when it should. Issues and PRs welcome.

## Attribution

The research engine is [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill),
MIT licensed, by Matt Van Horn and contributors. This repository contains no
engine code. It ships an instruction file, a reference document, and a validation
script that drive that engine from a separate checkout you control.

MIT licensed. See [LICENSE](LICENSE).
