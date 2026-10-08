from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Payments News Agent")

app.mount("/static", StaticFiles(directory="."), name="static")


@app.get("/")
async def read_root():
    return FileResponse("index.html")


@app.get("/health")
async def healthcheck():
    return {"status": "ok", "service": "payments-news-agent"}
