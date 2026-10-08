"""LangChain + Claude layer: summaries for a digest, and a tool-using agent for questions."""

from __future__ import annotations

import json
import os

from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from .fetch import NewsItem, fetch_article_text, fetch_payments_news

DEFAULT_MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = """You are a payments-industry news analyst covering India.
You answer only from Economic Times stories returned by your tools, never from memory.
Use `latest_payments_news` to get recent stories, and `read_article` when a headline
and teaser are not enough to answer. For every story you mention give the headline,
the publication date, a one or two sentence summary, and the link. If the tools return
nothing relevant, say so plainly."""


def build_llm(model: str | None = None) -> ChatAnthropic:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("Set ANTHROPIC_API_KEY to use the summary and ask commands (fetch works without it).")
    return ChatAnthropic(model=model or os.environ.get("PAYMENTS_NEWS_MODEL", DEFAULT_MODEL), max_tokens=4096)


# ---------- digest: one structured call that summarises every story ----------

class StorySummary(BaseModel):
    index: int = Field(description="The story's number from the input list")
    summary: str = Field(description="One or two plain sentences on what happened and why it matters for payments")


class DigestSummaries(BaseModel):
    stories: list[StorySummary]


def summarise(items: list[NewsItem], llm=None) -> list[dict]:
    """Return items as dicts with a Claude-written `summary`."""
    if not items:
        return []
    llm = llm or build_llm()
    listing = "\n\n".join(
        f"[{i}] {it.headline}\nDate: {it.published:%d %b %Y}\nTeaser: {it.summary or '(none)'}"
        if it.published else f"[{i}] {it.headline}\nTeaser: {it.summary or '(none)'}"
        for i, it in enumerate(items)
    )
    result: DigestSummaries = llm.with_structured_output(DigestSummaries).invoke(
        [
            ("system", "Summarise each Economic Times payments story using only its headline and teaser. Do not invent facts."),
            ("human", listing),
        ]
    )
    by_index = {s.index: s.summary for s in result.stories}
    out = []
    for i, it in enumerate(items):
        d = it.to_dict()
        d["summary"] = by_index.get(i) or it.summary
        out.append(d)
    return out


# ---------- agent: answers free-form questions with tools ----------

@tool
def latest_payments_news(hours: int = 72, limit: int = 25) -> str:
    """Latest payments stories (UPI, cards, wallets, fintech, RBI/NPCI rules) from Economic Times.

    Args:
        hours: how far back to look.
        limit: maximum number of stories.
    """
    errors: list[str] = []
    items = fetch_payments_news(hours=hours, limit=limit, errors=errors)
    return json.dumps({"stories": [i.to_dict() for i in items], "feed_errors": errors}, ensure_ascii=False)


@tool
def read_article(url: str) -> str:
    """Full text (trimmed) of an Economic Times article, for detail beyond the headline."""
    try:
        return fetch_article_text(url)
    except Exception as exc:  # report to the model rather than crash the run
        return f"Could not read article: {exc}"


def build_agent(model: str | None = None):
    return create_agent(build_llm(model), tools=[latest_payments_news, read_article], system_prompt=SYSTEM_PROMPT)


def ask(question: str, model: str | None = None) -> str:
    result = build_agent(model).invoke({"messages": [{"role": "user", "content": question}]})
    return result["messages"][-1].text
