# this is the main file for the backend, entrypoint for the FastAPI app and route definitions

import asyncio

# ── Force WindowsProactorEventLoopPolicy before anything else ────────────────
if hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import CloneRequest, CloneResponse
from scraper_sync import fetch_design_context_sync
from llm_client import generate_clone_html

load_dotenv
app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/api/clone")
async def clone_site(req: CloneRequest):
    url = req.url
    if not url:
        raise HTTPException(status_code=400, detail="Missing url")

    # 1) Run the synchronous scraper in a thread to avoid blocking the event loop:
    try:
        design_ctx = await asyncio.to_thread(fetch_design_context_sync, url)
    except HTTPException as e:
        # Propagate any HTTPException raised by the scraper
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Scraper failed: {e}")

    # 2) Call your LLM client (async) to generate the cloned HTML
    try:
        cloned_html = await generate_clone_html(design_ctx)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")

    return {"html": cloned_html}
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
