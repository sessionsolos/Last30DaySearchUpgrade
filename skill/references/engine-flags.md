# Engine flags and modes

Verified against `last30days.py` at v3.21.1. Read the section you need.

- [Output modes](#output-modes)
- [Scope and depth](#scope-and-depth)
- [Resolution flags](#resolution-flags)
- [Comparison runs](#comparison-runs)
- [Discovery runs](#discovery-runs)
- [Private local corpus](#private-local-corpus)
- [Saving output](#saving-output)
- [Diagnostics](#diagnostics)
- [Environment variables](#environment-variables)
- [What each source is good for](#what-each-source-is-good-for)

## Output modes

`--emit` takes `compact`, `json`, `context`, `md`, `html`, or `brief`. Default is
`compact`.

Use `compact` for essentially everything. It is the only mode carrying
`## Top Community Comments`, `## Best Takes`, Polymarket odds, and per-source
outcome states. `context` is leaner but silently drops all of those, which removes
most of the value.

`--emit=json` returns a versioned agent contract (`schema_version` 1.2). Top-level
fields: `schema_version`, `query`, `generated_at`, `window_days`, `source_status`,
`freshness_verdicts`, `clusters`, `results`. Each result carries `candidate_id`,
`title`, `source`, `url`, `published_at`, `summary`, `engagement`,
`relevance_score`, and `cluster`. Comments are not in this contract. Use it for
pipelines and dashboards, not for writing a brief.

`--json-profile` takes `agent` (default) or `raw`. Raw is an unversioned internal
dump and can contain local corpus paths and text.

`--register` takes `default`, `exec`, `dev`, `creator`, or `eli5`. These change
the engine's own rendered brief. Since this skill writes its own prose, the flag
mostly does not matter. Skip it.

## Scope and depth

| Flag | Effect |
| --- | --- |
| `--days N` (alias `--lookback-days`) | Window size. Default 30. |
| `--as-of DATE` | Historical lookback, ending at a past date. |
| `--quick` | Lower-latency profile, fewer results. |
| `--deep` | Higher-recall profile, slower. |
| `--search a,b,c` | Restrict to a comma-separated source list. |
| `--max-results N` | Override the final ranked-pool cap. |
| `--max-per-source N` | Override the per-stream cap. |
| `--web-backend` | `auto`, `brave`, `exa`, `serper`, `parallel`, `keyless`, `none`. `keyless` forces a zero-key floor. |
| `--verify-freshness` | Re-checks source-grounded claims after research and returns per-claim verdicts: `current`, `stale`, `contradicted`, `unsupported`. Worth it when a number is going into something that matters. |
| `--drill` | Deep follow-up on one cluster from the cached last report. |

`--verify-freshness` is the most underrated flag here. `unsupported` means the
claim could not be re-checked, which is not the same as false. Do not report a
verdict as if it were a fact check of the underlying claim.

## Resolution flags

Pass only what you actually resolved.

| Flag | Use |
| --- | --- |
| `--x-handle` | Subject's own X account. Surfaces their first-party posts. |
| `--x-related` | Comma-separated related handles, searched at lower weight. |
| `--dedicated-subreddits` | Entity-home subs, pulled in full (`Kanye,WestSubEver`). |
| `--subreddits` | Broad category subs (`SaaS,Entrepreneur`). |
| `--github-user` | Person mode. Surfaces PR velocity and repos. |
| `--github-repo` | `owner/repo`, comma-separated, for project mode. |
| `--tiktok-hashtags` | Without the `#`. |
| `--tiktok-creators` | Creator handles. |
| `--ig-creators` | Instagram handles. |
| `--trustpilot-domain` | Consumer brand reviews. Opt-in. |
| `--polymarket-keywords` | Steer prediction-market matching. |
| `--auto-resolve` | Engine discovers subs and handles itself. For hosts with no web search. Prefer resolving yourself. |
| `--hiring-signals` | Reads public jobs and careers pages as evidence of company focus. Report what hiring suggests, never what the roadmap will ship. |

On a person topic, first-party posts are the richest vein. An item tagged
`interaction:→@handle` is the subject replying to someone. Who a person
repeatedly engages is meaningful even at zero engagement, and the raw counts will
not show it.

## Comparison runs

```bash
python3 "$ENGINE_PY" "Tool A vs Tool B" --emit=compact --plan "$PLAN"
```

`--competitors N` auto-discovers N competitors and fans out.
`--competitors-list "A,B,C"` skips discovery. `--competitors-plan` takes a
per-entity plan file, written the same way as a normal plan.

For comparisons, land on a recommendation. A table with no verdict makes the
reader do the work they delegated. Name what each option is actually best at,
then say which one and under what condition.

## Discovery runs

`--discover "domain"` finds what is spiking instead of researching a known topic.
With no domain, it sweeps globally. Discovery is mutually exclusive with a topic
argument and with `--drill`.

The engine supports a three-command protocol where you judge the nominations:

```bash
python3 "$ENGINE_PY" --discover "DOMAIN" --nominate-only --save-dir "$DIR"
# read the nominations, write judgments to a file
python3 "$ENGINE_PY" --discover "DOMAIN" --judgments "$JUDGMENTS" --save-dir "$DIR"
# optionally write content angles to a file
python3 "$ENGINE_PY" --discover "DOMAIN" --finalize --angles "$ANGLES" --save-dir "$DIR"
```

Every leg needs the same `--save-dir`. Same tempfile pattern as the plan. A
one-shot `--discover` falls back to deterministic name heuristics and prints a
note saying so; that note means you skipped the protocol, not that you lack a
credential. There is no key that unlocks a judge. You are the judge.

`--discover-shallow` is faster and skips the per-topic research pass, which means
no `top_comment`.

A `nothing-solid` outcome is a valid answer. Relay it and suggest a narrower
domain.

## Private local corpus

```bash
--corpus /path/to/dir          # repeatable, .md/.txt/.pdf
--corpus-all-time              # include files older than the window
```

Ranks the user's own documents alongside public sources. Useful for checking
internal research against what the market is saying.

Corpus content is excluded from the `--emit=json` agent profile by default.
`LAST30DAYS_CORPUS_IN_EXPORT=1` overrides that, and `--json-profile=raw` may
contain corpus paths and text regardless. Only point `--corpus` at directories the
user named.

## Saving output

| Flag | Effect |
| --- | --- |
| `--save-dir PATH` | Directory for the raw saved brief. |
| `--output FILE` | Exact file path, format set by `--emit`. |
| `--save-suffix NAME` | Keeps variants of the same topic separate, e.g. per client. |
| `--store` | Persists findings to a local SQLite store, enabling `watchlist.py` and `briefing.py` for scheduled runs and digests. |
| `--synthesis-file` | Embeds your written synthesis into `--emit=html` output. |

Default save location is `~/Documents/Last30Days`, overridable with
`LAST30DAYS_MEMORY_DIR`.

**Do not run these without an explicit request in the same turn:**
`--publish-html` and `--publish` upload to `api.ht-ml.app` and the resulting pages
are public unless `--publish-password` is set.

## Diagnostics

| Command | Purpose |
| --- | --- |
| `--diagnose` | Which providers and sources are actually live. |
| `--preflight` | Human-readable permission summary. Reads no cookies, writes no files, runs no research. |
| `--preflight --emit=json` | Machine-readable version. |
| `--no-browser-cookies` | Hard off for cookie extraction even if `FROM_BROWSER` is set. |
| `--mock` | Runs against fixtures. Useful for testing without network calls. |
| `--debug` | HTTP debug logging. |

Run `--preflight` before the first real run on a new machine, and any time the
user asks what this thing touches.

## Environment variables

Config lives at `~/.config/last30days/.env`. Process environment wins over the
file; macOS Keychain is lowest priority.

| Variable | Effect |
| --- | --- |
| `SIGNAL_ENGINE` | Where this skill looks for the engine checkout. |
| `LAST30DAYS_MEMORY_DIR` | Save location. |
| `LAST30DAYS_CORPUS_DIRS` | Default corpus directories. |
| `FROM_BROWSER` | Browser cookie source for X auth. Unset means no cookie reads at all. `off` disables. `auto` tries every Chromium browser. |
| `AUTH_TOKEN`, `CT0` | X cookies passed directly, no browser read. |
| `SCRAPECREATORS_API_KEY` | Full Reddit comment threads (the free path rate-limits after roughly 3 to 22 items), plus TikTok, Instagram, Threads, Pinterest, LinkedIn, YouTube comments. Paid: 100 free credits one time, then from $10. |
| `BRAVE_API_KEY` | Web search. |
| `PERPLEXITY_API_KEY`, `OPENROUTER_API_KEY`, `XAI_API_KEY` | Optional providers. |
| `BSKY_HANDLE`, `BSKY_APP_PASSWORD` | Bluesky. |

Cookie extraction is scoped to the x.com domain and the `auth_token` and `ct0`
cookie names only. It reads nothing else and does nothing when `FROM_BROWSER` is
unset.

## What each source is good for

**Reddit.** The most useful source most of the time. Threaded argument, real
disagreement, top comments with counts. Skews technical, US, and toward the
motivated minority who post. Discovery is free, but the keyless path gets
rate-limited before it can read most comment threads, so deep Reddit needs
`SCRAPECREATORS_API_KEY`. Without it, expect titles and scores rather than the
argument underneath.

**Hacker News.** Developer consensus with unusually high comment quality.
Contrarian by default and confidently wrong about anything outside software.
Free, no key.

**X.** Fastest and least reliable. First-party posts from the subject are the
real prize; the ambient conversation is mostly noise and quote-dunks. Needs auth.

**YouTube.** Full transcripts, which means long-form reasoning no other source
carries. A 40-minute review has more substance than 200 tweets. View counts
measure thumbnails.

**TikTok and Instagram.** Cultural reach and whether normal people have heard of
this. Poor for factual claims. Needs a key.

**GitHub.** Actual behavior instead of stated intent. Commits, PR velocity, and
release notes are hard to fake.

**Polymarket.** Odds with money behind them. Better calibrated than pundits,
badly calibrated on thin markets. Always cite the volume next to the percentage,
because 74 percent on 800 dollars means nothing.

**LinkedIn.** Articles carry more signal than posts. Everything is performed.

**Web.** Editorial coverage. One signal among many, useful for pinning a date or
an official statement the community got wrong.

Cross-source agreement is the thing worth reporting. Any single source agreeing
with itself is just that source.
