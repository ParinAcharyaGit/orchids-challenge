# scraper that uses playwright to render react sites, extract DOM/CSS, inline images as Base64 and extract CSS ranges

import asyncio

if hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# rest of the imports    
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Playwright
from utils import to_data_uri, resolve_url
from fastapi import HTTPException



PLAYWRIGHT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/115.0.5790.170 Safari/537.36"
)

async def fetch_with_playwright(url:str, timeout: float = 15000) -> dict:
    playwright: Playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless = True)
    context = await browser.new_context(user_agent=PLAYWRIGHT_USER_AGENT)
    page = await context.new_page()

    await page.coverage.start_css_coverage()

    try:
        await page.goto(url, wait_until="networkidle", timeout=timeout)
        head_html = await page.evaluate("() => document.head.outerHTML")
        body_html = await page.evaluate("() => document.body.outerHTML")

        raw_coverage = await page.coverage.stop_css_coverage()
        critical_css_rules = []

        for entry in raw_coverage:
            text = entry["text"]
            ranges = entry["ranges"]
            for r in ranges:
                critical_css_rules.append(text[r["start"] : r["end"]])

        critical_css = "\n".join(critical_css_rules)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Playwright error: {e}")
    
    finally:
        await context.close()
        await browser.close()
        await playwright.stop()

    return {
        "head": head_html,
        "body": body_html,
        "critical_css": critical_css,
    }

async def inline_images(html: str, base_url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    img_tags = soup.find_all("img", src=True)

    async def process_img(tag):
        raw_src = tag["src"]
        abs_url = resolve_url(base_url, raw_src)
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(abs_url)
                resp.raise_for_status()
                content_type = resp.headers.get("Content-Type", "application/octet-stream")
                data_uri = to_data_uri(content_type, resp.content)
                tag["src"] = data_uri
        except Exception:
            pass

    await asyncio.gather(*(process_img(tag) for tag in img_tags))
    return str(soup)

async def fetch_design_context(url: str) -> dict:
    data = await fetch_with_playwright(url)
    head_html = data["head"]
    body_html = data["body"]
    critical_css = data["critical_css"]

    body_with_images = await inline_images(body_html, url)

    return {
        "head": head_html,
        "body": body_with_images,
        "css": critical_css,
    }
