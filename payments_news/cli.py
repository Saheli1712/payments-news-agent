"""Command line: fetch (no key), digest (Claude summaries), ask (agent)."""

from __future__ import annotations

import argparse
import json
import sys

from .fetch import fetch_payments_news


def _render_md(rows: list[dict]) -> str:
    if not rows:
        return "No payments stories found in that window."
    lines = []
    for n, r in enumerate(rows, 1):
        date = (r["published"] or "")[:10] or "date n/a"
        lines.append(f"{n}. **{r['headline']}**  \n   {date} · {r['source']}  \n   {r['summary']}  \n   {r['link']}")
    return "\n\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="payments_news", description="Latest payments news from Economic Times")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, help_ in [("fetch", "list stories using the feeds' own teasers (no API key)"),
                        ("digest", "list stories with Claude-written summaries")]:
        s = sub.add_parser(name, help=help_)
        s.add_argument("--hours", type=float, default=72, help="look-back window (default 72; 0 = no limit)")
        s.add_argument("--limit", type=int, default=30)
        s.add_argument("--feed", action="append", metavar="URL", help="use this feed URL instead of the defaults (repeatable)")
        s.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
        s.add_argument("--out", help="also write the result to this file")
    a = sub.add_parser("ask", help="ask the agent a question, e.g. 'What changed for UPI this week?'")
    a.add_argument("question")
    a.add_argument("--model")
    args = p.parse_args(argv)

    if args.cmd == "ask":
        from .agent import ask
        print(ask(args.question, model=args.model))
        return 0

    feeds = {f"Custom feed {i + 1}": u for i, u in enumerate(args.feed)} if args.feed else None
    errors: list[str] = []
    items = fetch_payments_news(hours=args.hours or None, limit=args.limit, feeds=feeds, errors=errors)
    if args.cmd == "digest":
        from .agent import summarise
        rows = summarise(items)
    else:
        rows = [i.to_dict() for i in items]

    if not rows and errors and not args.json:
        text = "Could not reach any Economic Times feed (see warnings below)."
    else:
        text = json.dumps(rows, indent=2, ensure_ascii=False) if args.json else _render_md(rows)
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    for e in errors:
        print(f"warning: {e}", file=sys.stderr)
    return 0 if rows or not errors else 1
