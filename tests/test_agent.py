from datetime import datetime, timezone

from payments_news import agent as A
from payments_news.fetch import NewsItem


class FakeStructured:
    def __init__(self, result):
        self.result, self.messages = result, None

    def invoke(self, messages):
        self.messages = messages
        return self.result


class FakeLLM:
    def __init__(self, result):
        self.structured = FakeStructured(result)

    def with_structured_output(self, schema):
        assert schema is A.DigestSummaries
        return self.structured


def test_summarise_maps_summaries_back_and_keeps_teaser_fallback():
    items = [NewsItem("UPI news", "https://x/1", datetime(2026, 10, 7, tzinfo=timezone.utc), "teaser 1", "ET"),
             NewsItem("Card rules", "https://x/2", None, "teaser 2", "ET")]
    llm = FakeLLM(A.DigestSummaries(stories=[A.StorySummary(index=0, summary="Claude summary")]))
    rows = A.summarise(items, llm=llm)
    assert rows[0]["summary"] == "Claude summary" and rows[1]["summary"] == "teaser 2"
    assert "[0] UPI news" in llm.structured.messages[1][1] and "07 Oct 2026" in llm.structured.messages[1][1]


def test_agent_builds_with_tools(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    graph = A.build_agent()
    assert {"latest_payments_news", "read_article"} <= set(graph.get_graph().nodes["tools"].data.tools_by_name)


def test_missing_key_message(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    try:
        A.build_llm()
    except RuntimeError as e:
        assert "fetch works without it" in str(e)
    else:
        raise AssertionError("expected RuntimeError")
