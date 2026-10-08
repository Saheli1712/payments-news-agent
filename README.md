# Payments news agent (Economic Times + LangChain)

Pulls the latest payments stories (UPI, NPCI, cards, wallets, payment aggregators,
RBI payment rules, fintech) from Economic Times and gives you a list with
**headline, date, short summary and link**.

It reads ET's public **RSS feeds** rather than scraping pages, checks `robots.txt`
before every request, and waits a second between requests.

The Vercel web app displays the feed's extracted story text (not just headlines
or links). Enter a duration in hours or days to filter recent payment stories;
the source link is available below each extract.

## Setup

```bash
cd payments-news-agent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Use

```bash
# 1. Just the news, no API key needed (uses ET's own teaser text as the summary)
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
| `payments_news/sources.py` | ET feed URLs and the payments keyword list. Edit here to add feeds or words. |
| `payments_news/fetch.py` | Downloads feeds, keeps payments stories, removes duplicates, sorts newest first. If every feed fails it looks up current feed URLs on ET's RSS index page. Also `fetch_article_text` for full articles. |
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
pytest -q        # 12 offline tests, no network or key needed
```

Use for personal reading; ET's content belongs to ET, so link back rather than republishing.
