from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from payments_news.fetch import fetch_payments_news

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Payments News Agent")


@app.get("/")
async def read_root():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/styles.css")
async def read_stylesheet():
    return FileResponse(BASE_DIR / "styles.css", media_type="text/css")


@app.get("/api/news")
def get_news(
    hours: float = Query(default=72, gt=0, le=720),
    limit: int = Query(default=30, ge=1, le=50),
):
    errors: list[str] = []
    successful_feeds: list[str] = []
    items = fetch_payments_news(
        hours=hours,
        limit=limit,
        errors=errors,
        successful_feeds=successful_feeds,
    )
    if not successful_feeds and errors:
        raise HTTPException(
            status_code=502,
            detail=(
                "Could not retrieve payment news from the feeds. "
                + "Feed errors: "
                + "; ".join(errors)
            ),
        )
    return {
        "hours": hours,
        "count": len(items),
        "items": [item.to_dict() for item in items],
        "warnings": errors,
    }


@app.get("/health")
async def healthcheck():
    return {"status": "ok", "service": "payments-news-agent"}
