from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

import app

client = TestClient(app.app)


def test_news_api_returns_extracts_for_selected_window(monkeypatch):
    item = SimpleNamespace(
        to_dict=lambda: {
            "headline": "UPI payments update",
            "link": "https://example.com/story",
            "published": datetime(2026, 10, 7, tzinfo=timezone.utc).isoformat(),
            "summary": "The extract describes the payments update.",
            "source": "ET test",
        }
    )
    requested = {}

    def fake_fetch_payments_news(hours, limit, errors, successful_feeds):
        requested.update(hours=hours, limit=limit)
        successful_feeds.append("ET test")
        return [item]

    monkeypatch.setattr(app, "fetch_payments_news", fake_fetch_payments_news)

    response = client.get("/api/news?hours=48&limit=5")

    assert response.status_code == 200
    assert response.json() == {
        "hours": 48,
        "count": 1,
        "items": [item.to_dict()],
        "warnings": [],
    }
    assert requested == {"hours": 48, "limit": None}


def test_news_api_rejects_invalid_duration():
    response = client.get("/api/news?hours=721")

    assert response.status_code == 422


def test_news_api_reports_feed_errors_when_all_feeds_fail(monkeypatch):
    def fake_fetch_payments_news(hours, limit, errors, successful_feeds):
        errors.append("ET feed: 403 Forbidden")
        return []

    monkeypatch.setattr(app, "fetch_payments_news", fake_fetch_payments_news)

    response = client.get("/api/news")

    assert response.status_code == 502
    assert "ET feed" in response.json()["detail"]
    assert "403 Forbidden" not in response.json()["detail"]


def test_news_api_returns_empty_result_and_warnings_for_partial_feed_failures(monkeypatch):
    def fake_fetch_payments_news(hours, limit, errors, successful_feeds):
        errors.append("ETBFSI: 403 Forbidden")
        successful_feeds.append("ET Banking")
        return []

    monkeypatch.setattr(app, "fetch_payments_news", fake_fetch_payments_news)

    response = client.get("/api/news")

    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert response.json()["warnings"] == ["ETBFSI"]


def test_homepage_and_stylesheet_are_served():
    homepage = client.get("/")
    stylesheet = client.get("/styles.css")

    assert homepage.status_code == 200
    assert "Payments and cards related news" in homepage.text
    assert stylesheet.status_code == 200
    assert "text/css" in stylesheet.headers["content-type"]
