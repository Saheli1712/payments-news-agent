# Payments and cards news agent

Pulls recent payments and card-industry articles for India and global coverage,
including UPI, wallets, ACH, RTGS, RTP, cards, and cross-border payment rails.
Stories are shown with **headline, date, publisher, feed-provided extract and link**.

It reads public **RSS feeds** from major Indian and international newspapers and
payments publications, checks each publisher's `robots.txt` before every request,
and waits between requests to the same publisher. Sources currently include
Economic Times, Mint, The Hindu, The Hindu BusinessLine, The Indian Express,
Times of India, Financial Times, BBC, The Guardian, The New York Times, The Wall
Street Journal, ABC Australia, Payments Dive, and PYMNTS. Any publisher with an
accessible, permitted RSS feed can be added in `payments_news/sources.py`.

The Vercel web app displays every matching article returned by those feeds for
the selected window (up to 30 days). RSS feeds can only provide the articles they
publish and may omit articles or excerpts; story links point to the original publisher.

## Setup

```bash
cd payments-news-agent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Use

```bash
# 1. Just the news, no API key needed (uses feed-provided extracts)
python -m payments_news fetch                  # last 72 hours, up to 30 stories
python -m payments_news fetch --hours 24 --limit 10
python -m payments_news fetch --json --out news.json

# 2. Digest with Claude-written summaries (needs a key)
export ANTHROPIC_API_KEY=sk-ant-...            # Windows: set ANTHROPIC_API_KEY=...
python -m payments_news digest --out digest.md

# 3. Ask the LangChain agent anything about recent payments news
python -m payments_news ask "What changed for UPI this week?"
python -m payments_news ask "Any new payment aggregator licences? Read the articles and compare them."
```

## How it works

| File | What it does |
|---|---|
| `payments_news/sources.py` | Publisher RSS feed URLs and the payments keyword list. Add any RSS source that allows automated feed access. |
| `payments_news/fetch.py` | Downloads feeds, keeps relevant payment stories, removes duplicates, sorts newest first, and filters to the selected time window. Also `fetch_article_text` for full articles. |
| `payments_news/agent.py` | LangChain layer. `summarise` makes one structured Claude call for the digest; `build_agent` is a `create_agent` agent with two tools, `latest_payments_news` and `read_article`. |
| `payments_news/cli.py` | The `fetch`, `digest` and `ask` commands. |

Model: `claude-opus-5-5` by default; set `PAYMENTS_NEWS_MODEL` to change it
(e.g. `claude-sonnet-5-5` or `claude-haiku-5-5` for cheaper daily runs).

## If a feed stops working

ET occasionally renumbers feeds. You'll see `warning: <feed>: 404` lines. Open
<https://economictimes.indiatimes.com/rss.cms>, copy the new URL into
`payments_news/sources.py`, or pass it once with `--feed URL`.

## Run it every morning (optional)

macOS/Linux cron, 8am daily:

```
0 8 * * * cd /path/to/payments-news-agent && .venv/bin/python -m payments_news digest --hours 24 --out ~/payments-$(date +\%F).md
```

## Tests

```bash
pytest -q        # offline tests, no network or key needed
```

Use for personal reading; ET's content belongs to ET, so link back rather than republishing.
