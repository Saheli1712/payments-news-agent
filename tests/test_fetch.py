from pathlib import Path

import pytest
import requests

from payments_news import fetch as F

FEED = (Path(__file__).parent / "fixtures" / "et_feed.xml").read_bytes()


class FakeResp:
    def __init__(self, status=200, content=b""):
        self.status_code, self.content, self.text = status, content, content.decode()

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


class FakeSession:
    def __init__(self, routes):
        self.routes, self.headers, self.calls = routes, {}, []

    def get(self, url, timeout=None):
        self.calls.append(url)
        for prefix, resp in self.routes.items():
            if url.startswith(prefix):
                return resp
        return FakeResp(404)


def fetcher(routes):
    return F.Fetcher(session=FakeSession(routes), delay=0)


def test_filters_to_payments_and_sorts_newest_first():
    f = fetcher({"https://economictimes.indiatimes.com/robots.txt": FakeResp(200, b"User-agent: *\nAllow: /\n"),
                 "https://economictimes.indiatimes.com/feed": FakeResp(200, FEED)})
    items = F.fetch_payments_news(hours=None, feeds={"ET test": "https://economictimes.indiatimes.com/feed"}, fetcher=f)
    assert [i.headline for i in items] == [
        "NPCI extends UPI Lite wallet limit for offline payments",
        "RBI grants payment aggregator licence to two fintechs",
    ]
    assert items[0].summary == "The new limit applies to small-value transactions."  # HTML stripped
    assert items[0].published.isoformat() == "2026-10-07T04:00:00+00:00"


def test_respects_robots_txt():
    f = fetcher({"https://economictimes.indiatimes.com/robots.txt": FakeResp(200, b"User-agent: *\nDisallow: /feed\n"),
                 "https://economictimes.indiatimes.com/feed": FakeResp(200, FEED)})
    errors = []
    items = F.fetch_payments_news(hours=None, feeds={"ET": "https://economictimes.indiatimes.com/feed"},
                                  fetcher=f, discover=False, errors=errors)
    assert items == [] and "robots.txt disallows" in errors[0]
    assert "https://economictimes.indiatimes.com/feed" not in f.session.calls


def test_dedupes_same_story_from_two_feeds():
    f = fetcher({"https://economictimes.indiatimes.com/": FakeResp(200, FEED)})
    feeds = {"A": "https://economictimes.indiatimes.com/a", "B": "https://economictimes.indiatimes.com/b"}
    assert len(F.fetch_payments_news(hours=None, feeds=feeds, fetcher=f)) == 2


def test_falls_back_to_rss_index_when_feeds_break():
    index = b'<a href="/industry/banking/finance/rssfeeds/999.cms">Banking</a><a href="/news/sports/rssfeeds/1.cms">Sports</a>'
    f = fetcher({"https://economictimes.indiatimes.com/rss.cms": FakeResp(200, index),
                 "https://economictimes.indiatimes.com/industry/banking/finance/rssfeeds/999.cms": FakeResp(200, FEED)})
    errors = []
    items = F.fetch_payments_news(hours=None, feeds={"Old": "https://economictimes.indiatimes.com/old"}, fetcher=f, errors=errors)
    assert len(items) == 2 and items[0].source == "ET Banking"
    assert all("sports" not in c for c in f.session.calls)


def test_does_not_discover_feeds_when_a_feed_succeeds_without_payment_stories():
    empty_feed = b"""<rss><channel><item>
      <title>Weather forecast</title>
      <link>https://example.com/weather</link>
    </item></channel></rss>"""
    f = fetcher({
        "https://economictimes.indiatimes.com/robots.txt": FakeResp(200, b"User-agent: *\nAllow: /\n"),
        "https://economictimes.indiatimes.com/feed": FakeResp(200, empty_feed),
    })

    items = F.fetch_payments_news(
        hours=None,
        feeds={"ET": "https://economictimes.indiatimes.com/feed"},
        fetcher=f,
    )

    assert items == []
    assert "https://economictimes.indiatimes.com/rss.cms" not in f.session.calls


def test_hours_window_excludes_old_stories():
    f = fetcher({"https://economictimes.indiatimes.com/": FakeResp(200, FEED)})
    assert F.fetch_payments_news(hours=1, feeds={"A": "https://economictimes.indiatimes.com/a"}, fetcher=f) == []


@pytest.mark.parametrize("text,expected", [("UPI volumes hit record", True), ("Visa and Mastercard fees", True),
                                           ("Season scorecard", False), ("Steel output rises", False)])
def test_keyword_match(text, expected):
    assert F.is_payments_story(F.NewsItem(text, "l", None, "", "x")) is expected


def test_keeps_card_network_visa_story():
    item = F.NewsItem("Visa expands credit card payments", "l", None, "", "ET Tech Fintech")

    assert F.is_payments_story(item)


def test_excludes_work_visa_story_that_only_matches_the_visa_keyword():
    item = F.NewsItem(
        "Trump proposes to end H-1B grace period",
        "l",
        None,
        "The proposal affects work visa holders.",
        "ET Tech Fintech",
    )

    assert not F.is_payments_story(item)
    assert not F.is_payments_story(item)

def test_excludes_employment_visa_story_that_only_matches_the_visa_keyword():
    item = F.NewsItem(
        "Cognizant PERM suspension raises talent retention concerns",
        "l",
        None,
        "The investigation concerns employment visa programmes.",
        "ET Tech Fintech",
    )

    assert not F.is_payments_story(item)
