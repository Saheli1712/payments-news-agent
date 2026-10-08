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

    def fake_fetch_payments_news(hours, limit, errors):
        requested.update(hours=hours, limit=limit)
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
    assert requested == {"hours": 48, "limit": 5}


def test_news_api_rejects_invalid_duration():
    response = client.get("/api/news?hours=721")

    assert response.status_code == 422


def test_news_api_reports_feed_errors(monkeypatch):
    def fake_fetch_payments_news(hours, limit, errors):
        errors.append("ET feed: 403 Forbidden")
        return []

    monkeypatch.setattr(app, "fetch_payments_news", fake_fetch_payments_news)

    response = client.get("/api/news")

    assert response.status_code == 502
    assert "403 Forbidden" in response.json()["detail"]


def test_homepage_and_stylesheet_are_served():
    homepage = client.get("/")
    stylesheet = client.get("/styles.css")

    assert homepage.status_code == 200
    assert "Payment news extracts" in homepage.text
    assert stylesheet.status_code == 200
    assert "text/css" in stylesheet.headers["content-type"]
