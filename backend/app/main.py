import asyncio, os

# ── On Windows, use ProactorEventLoopPolicy so subprocesses work ─────────────
if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv
import logging
import time
from pathlib import Path

from models import CloneRequest
from scraper_sync import fetch_design_context_sync
from llm_client import generate_clone_html

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.post("/api/clone")
async def clone_website(request: CloneRequest):
    """
    Clone a website into a standalone HTML file.
    """
    start_time = time.time()
    url = str(request.url)

    logger.info(f"🎯 Starting clone process for: {url}")

    try:
        logger.info("📡 Step 1: Scraping website...")
        scrape_start = time.time()
        design_context = await asyncio.to_thread(fetch_design_context_sync, url)
        scrape_time = time.time() - scrape_start

        logger.info(f"✅ Scraping completed in {scrape_time:.2f}s")
        logger.info("🔍 SCRAPING RESULTS DEBUG:")
        logger.info(f"   Head length: {len(design_context.get('head', ''))} chars")
        logger.info(f"   Body length: {len(design_context.get('body', ''))} chars")
        logger.info(f"   CSS length: {len(design_context.get('css', ''))} chars")

        if not design_context.get('body'):
            raise HTTPException(status_code=400, detail="Failed to extract website content – no body content found")

        body_content = design_context.get('body', '')
        main_elements = body_content.count('<main')
        section_elements = body_content.count('<section')
        div_elements = body_content.count('<div')

        logger.info(f"   Content elements: main={main_elements}, section={section_elements}, div={div_elements}")
        if main_elements == 0 and section_elements == 0 and div_elements < 5:
            logger.warning("⚠️  Very few content elements found – page might not have loaded properly")

        # 💾 Step 1.5: Save raw HTML to disk
        save_dir = Path("cloned_sites")
        save_dir.mkdir(exist_ok=True)
        timestamp_str = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        html_path = save_dir / f"{timestamp_str}_scraped.html"

        full_html = f"<html><head>{design_context.get('head', '')}</head><body>{body_content}</body></html>"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        logger.info(f"📁 Saved raw scraped HTML to {html_path}")

        # Step 2: Generate clean HTML
        logger.info("🤖 Step 2: Generating clean HTML...")
        llm_start = time.time()
        generated_html = await generate_clone_html(design_context)
        llm_time = time.time() - llm_start

        # Checks
        if not generated_html or len(generated_html) < 100:
            raise HTTPException(status_code=500, detail="LLM failed to generate valid HTML content")
        if not generated_html.strip().startswith('<!DOCTYPE'):
            logger.warning("⚠️  Generated HTML doesn’t start with <!DOCTYPE")

        total_time = time.time() - start_time

        debug_info = {
            **design_context.get('debug_info', {}),
            'processing_times': {
                'scraping': round(scrape_time, 2),
                'llm_generation': round(llm_time, 2),
                'total': round(total_time, 2)
            },
            'validation': {
                'has_doctype': generated_html.strip().startswith('<!DOCTYPE'),
                'has_body_tag': '<body' in generated_html,
                'has_head_tag': '<head' in generated_html,
                'final_html_length': len(generated_html),
                'main_elements_in_final': generated_html.count('<main'),
                'section_elements_in_final': generated_html.count('<section'),
                'div_elements_in_final': generated_html.count('<div')
            },
            'source_analysis': {
                'main_elements_scraped': main_elements,
                'section_elements_scraped': section_elements,
                'div_elements_scraped': div_elements
            },
            'saved_raw_html_path': str(html_path)
        }

        logger.info(f"🎉 Clone completed successfully in {total_time:.2f}s")
        logger.info(f"📊 Final HTML size: {len(generated_html)} characters")

        # ✅ Final return: no CloneResponse, just dict
        return {
            "html": generated_html,
            "debug_info": debug_info,
            "processing_time": total_time,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during cloning: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
