import asyncio, os

# ── On Windows, use ProactorEventLoopPolicy so subprocesses work ─────────────
if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging
import time
from pathlib import Path
import hashlib
from bs4 import BeautifulSoup
import glob # Import glob to find files

from models import CloneRequest, ScrapeRequest, EditRequest, EditResponse, LatestScrapedResponse
from scraper_sync import fetch_design_context_sync
from llm_client import generate_clone_html, generate_with_google, edit_html_with_gemini

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

# Ensure cloned_sites directory exists on startup
CLONED_SITES_DIR = Path("cloned_sites")
CLONED_SITES_DIR.mkdir(exist_ok=True)

# Check for required environment variables on startup
required_env_vars = ['GOOGLE_API_KEY', 'GROQ_API_KEY']
for var in required_env_vars:
    if not os.getenv(var):
        logger.warning(f"⚠️  Environment variable '{var}' not set. LLM functionality may be limited.")

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/api/scrape")
async def scrape_website_endpoint(request: ScrapeRequest):
    """
    Scrape a website and return the raw HTML.
    """
    start_time = time.time()
    url = request.url

    logger.info(f"📡 Starting scrape process for: {url}")

    try:
        scrape_start = time.time()
        # Use asyncio.to_thread for potentially blocking sync function
        design_context = await asyncio.to_thread(fetch_design_context_sync, url)
        scrape_time = time.time() - scrape_start

        logger.info(f"✅ Scraping completed in {scrape_time:.2f}s")
        logger.info("🔍 SCRAPING RESULTS DEBUG:")
        logger.info(f"   Head length: {len(design_context.get('head', ''))} chars")
        logger.info(f"   Body length: {len(design_context.get('body', ''))} chars")
        logger.info(f"   CSS length: {len(design_context.get('css', ''))} chars")

        if not design_context.get('body'):
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to extract website content – no body content found")

        # Check for minimal content as before
        body_content = design_context.get('body', '')
        main_elements = body_content.count('<main')
        section_elements = body_content.count('<section')
        div_elements = body_content.count('<div')
        logger.info(f"   Content elements: main={main_elements}, section={section_elements}, div={div_elements}")
        if main_elements == 0 and section_elements == 0 and div_elements < 5:
            logger.warning("⚠️  Very few content elements found – page might not have loaded properly")

        # 💾 Save raw HTML to disk
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
        timestamp_str = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        filename = f"{timestamp_str}_{url_hash}_raw.html"
        html_path = CLONED_SITES_DIR / filename

        full_html = f"<html><head>{design_context.get('head', '')}</head><body>{design_context.get('body', '')}</body></html>"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        logger.info(f"📁 Saved raw scraped HTML to {html_path}")

        total_time = time.time() - start_time
        logger.info(f"🎉 Scrape completed successfully in {total_time:.2f}s")

        # Return relevant scrape data, including the path
        return {
            "raw_html": full_html,
            "raw_html_path": str(html_path),
            "debug_info": design_context.get('debug_info', {}),
            "processing_time": round(total_time, 2),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during scraping: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during scraping: {str(e)}")

@app.post("/api/generate")
async def generate_website_endpoint(request: CloneRequest):
    """
    Generate clean HTML from raw HTML using an LLM.
    """
    start_time = time.time()
    raw_html_path = request.raw_html_path
    model_id = request.model

    logger.info(f"🤖 Starting HTML generation for {raw_html_path} using model: {model_id}")

    try:
        # Read the raw HTML content from the saved file
        raw_html_file = Path(raw_html_path)
        if not raw_html_file.exists():
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Raw HTML file not found at {raw_html_path}")

        # To pass data to generate_clone_html, we need the head, body, and css
        # A more robust approach would save the full design_context from the scrape step
        # or re-scrape (less efficient).
        # Given the flow, let's reconstruct a minimal context
        # by parsing the saved raw HTML file. CSS links/styles might be lost this way.
        # If fetch_design_context_sync can work with local file paths or content, that's better.
        # For now, let's read and parse to get head/body.

        with open(raw_html_file, "r", encoding="utf-8") as f:
             raw_full_html = f.read()

        soup = BeautifulSoup(raw_full_html, 'html.parser')
        # Reconstruct minimal design_context
        # This might not include all original CSS, especially external stylesheets
        design_context_for_llm = {
            'head': str(soup.head) if soup.head else '',
            'body': str(soup.body) if soup.body else '',
            'css': '', # Significant limitation here, might need re-scraping CSS or saving more data
            'debug_info': {} # Start with empty debug info
        }

        # You might want to re-run CSS scraping or pass the original CSS from /api/scrape
        # For now, passing empty CSS might lead to unstyled generated HTML.

        llm_start = time.time()
        # Pass the reconstructed context and the model_id to the generation function
        # The generate_clone_html function in llm_client.py needs to handle this structure
        generated_html = await generate_clone_html(design_context_for_llm, model_id=model_id)
        llm_time = time.time() - llm_start

        # Checks
        if not generated_html or len(generated_html) < 100:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="LLM failed to generate valid HTML content or content is too short")

        # Check if it starts with doctype case-insensitively and optionally whitespace
        if not re.match(r'^\s*<!DOCTYPE', generated_html, re.IGNORECASE):
             logger.warning("⚠️  Generated HTML doesn't start with <!DOCTYPE")

        # 💾 Save generated HTML to disk
        timestamp_str = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        # Use same URL hash for consistency, plus model ID
        # Extract the original URL hash from the raw file name
        try:
             url_hash_from_raw_file = raw_html_file.stem.split('_')[1] # Assuming format timestamp_hash_raw.html
        except IndexError:
             logger.warning(f"Could not extract URL hash from raw filename: {raw_html_file.name}. Using generic hash.")
             url_hash_from_raw_file = hashlib.md5(raw_html_path.encode('utf-8')).hexdigest()[:8] # Fallback hash

        filename = f"{timestamp_str}_{url_hash_from_raw_file}_{model_id.replace('-', '_')}_generated.html" # Include model in filename
        generated_html_path = CLONED_SITES_DIR / filename

        with open(generated_html_path, "w", encoding="utf-8") as f:
            f.write(generated_html)
        logger.info(f"📁 Saved generated HTML to {generated_html_path}")


        total_time = time.time() - start_time
        logger.info(f"🎉 Generation completed successfully in {total_time:.2f}s")
        logger.info(f"📊 Final HTML size: {len(generated_html)} characters")

        # Return the generated HTML and its path
        return {
            "generated_html": generated_html,
            "generated_html_path": str(generated_html_path),
            "processing_time": round(total_time, 2),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during generation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during generation: {str(e)}")

@app.get("/api/latest-scraped", response_model=LatestScrapedResponse)
async def get_latest_scraped_file():
    """
    Find the path of the most recently saved raw scraped HTML file.
    """
    try:
        # List all files matching the pattern *_*_raw.html
        scraped_files = sorted(
            CLONED_SITES_DIR.glob("*_*_raw.html"),
            key=os.path.getmtime, # Sort by modification time
            reverse=True # Get the latest first
        )

        if not scraped_files:
            logger.warning("No raw scraped HTML files found.")
            return LatestScrapedResponse(latest_scraped_path=None, error="No raw scraped HTML files found.")

        latest_file_path = scraped_files[0]
        logger.info(f"Found latest scraped file: {latest_file_path}")
        return LatestScrapedResponse(latest_scraped_path=str(latest_file_path))

    except Exception as e:
        logger.error(f"❌ Error finding latest scraped file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error finding latest scraped file: {str(e)}")

@app.post("/api/edit", response_model=EditResponse)
async def edit_html_endpoint(request: EditRequest):
    """
    Edit HTML content using a specified LLM based on user instruction.
    """
    start_time = time.time()
    html_content_to_edit = request.html_content
    instruction = request.instruction
    model_id = request.model # Should default to Gemini Pro

    logger.info(f"✂️ Starting HTML editing with model: {model_id}")
    logger.info(f"Instruction: {instruction}")
    # Log snippet of HTML to edit
    logger.info(f"Editing HTML (snippet): {html_content_to_edit[:200]}...")


    try:
        llm_start = time.time()
        # Use the new editing function in llm_client
        edited_html = await edit_html_with_gemini(html_content_to_edit, instruction, model_id=model_id)
        llm_time = time.time() - llm_start

        if not edited_html or len(edited_html) < 100:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="LLM failed to generate valid edited HTML content or content is too short")

        # Check if it starts with doctype case-insensitively and optionally whitespace
        if not re.match(r'^\s*<!DOCTYPE', edited_html, re.IGNORECASE):
             logger.warning("⚠️  Edited HTML doesn't start with <!DOCTYPE")


        # 💾 Save edited HTML to disk
        # Need a way to link edited file back to original scrape/generation.
        # For simplicity, let's just append "_edited" and a timestamp.
        timestamp_str = time.strftime("%Y%m%d_%H%M%S", time.gmtime())

        # Attempt to get the base filename from the raw_html_path if available,
        # though this endpoint receives html_content directly.
        # If you want to track edits of specific files, the request should ideally include the source file path.
        # For now, let's create a new file named based on timestamp and a simple hash of the edited content or instruction
        instruction_hash = hashlib.md5(instruction.encode('utf-8')).hexdigest()[:8]
        filename = f"{timestamp_str}_edited_{instruction_hash}_{model_id.replace('-', '_')}.html"
        edited_html_path = CLONED_SITES_DIR / filename

        with open(edited_html_path, "w", encoding="utf-8") as f:
            f.write(edited_html)
        logger.info(f"📁 Saved edited HTML to {edited_html_path}")

        total_time = time.time() - start_time
        logger.info(f"✅ HTML editing completed successfully in {total_time:.2f}s")
        logger.info(f"📊 Edited HTML size: {len(edited_html)} characters")

        # Return the edited HTML content
        return EditResponse(
            edited_html=edited_html,
            processing_time=round(total_time, 2),
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            # debug_info=... # Include any debug info from the LLM call if available
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during HTML editing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during HTML editing: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
