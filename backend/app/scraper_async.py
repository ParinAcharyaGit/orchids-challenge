# backend/app/scraper_async.py

import re
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from fastapi import HTTPException
from urllib.parse import urlparse
import json

from utils import to_data_uri, resolve_url

PLAYWRIGHT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
)

def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)

def extract_dom_structure(soup):
    """
    Extract the complete DOM structure with all nested elements
    """
    def element_to_dict(element):
        if element.name is None:  # Text node
            text = element.strip()
            return {"type": "text", "content": text} if text else None
        
        result = {
            "type": "element",
            "tag": element.name,
            "attributes": dict(element.attrs) if element.attrs else {},
            "children": []
        }
        
        for child in element.children:
            child_dict = element_to_dict(child)
            if child_dict:
                result["children"].append(child_dict)
        
        return result
    
    return element_to_dict(soup)

async def fetch_with_playwright_async(url: str, timeout: float = 30000) -> dict:
    print(f"🚀 Starting Playwright scrape for: {url}")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ])
            context = await browser.new_context(
                user_agent=PLAYWRIGHT_USER_AGENT,
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            # Route handler to block unnecessary resources
            async def route_handler(route, request):
                if request.resource_type in ["image", "font", "media"]:
                    await route.abort()
                    return

                if any(domain in request.url for domain in ["githubgithubassets.com", "analytics", "tracking"]):
                    await route.abort()
                    return

                await route.continue_()

            await page.route("**/*", route_handler)

            print("📡 Navigating to URL...")
            await page.goto(url, wait_until="networkidle", timeout=timeout)

            print("⏳ Waiting for dynamic content...")
            await page.wait_for_timeout(8000)

            print("📄 Extracting page content...")
            full_html = await page.content()

            soup = BeautifulSoup(full_html, 'html.parser')
            head_html = str(soup.find('head')) or ""
            body_element = soup.find('body')
            body_html = str(body_element) if body_element else ""

            print("🎨 Extracting CSS...")
            styles = await page.eval_on_selector_all(
                "style, link[rel='stylesheet']",
                """
                async (elements) => {
                    const cssTexts = [];
                    for (const el of elements) {
                        if (el.tagName === 'STYLE') {
                            cssTexts.push(el.innerHTML);
                        } else if (el.tagName === 'LINK' && el.href) {
                            try {
                                const res = await fetch(el.href);
                                if (res.ok) {
                                    const text = await res.text();
                                    cssTexts.push(text);
                                }
                            } catch (_) {}
                        }
                    }
                    return cssTexts;
                }
                """
            )
            critical_css = "\n".join(styles)

            await context.close()
            await browser.close()

            return {
                "head": head_html,
                "body": body_html,
                "critical_css": critical_css,
                "debug_info": {
                    "full_html_length": len(full_html),
                    "head_length": len(head_html),
                    "body_length": len(body_html),
                    "css_length": len(critical_css),
                }
            }

    except Exception as e:
        print(f"❌ Playwright Async Error: {e}")
        raise HTTPException(status_code=400, detail=f"Playwright Async Error: {e}")

def inline_images_sync(html: str, base_url: str) -> str:
    """
    For each <img src="…"> in `html`, fetch and replace with Base64 data URI.
    """
    print("🖼️  Starting image inlining...")
    soup = BeautifulSoup(html, "html.parser")
    img_tags = soup.find_all("img", src=True)
    print(f"Found {len(img_tags)} images to process")

    headers = {"User-Agent": PLAYWRIGHT_USER_AGENT}

    for i, tag in enumerate(img_tags):
        raw_src = tag["src"]
        abs_url = resolve_url(base_url, raw_src)

        if not is_valid_url(abs_url):
            print(f"Skipping invalid image URL: {abs_url}")
            continue

        try:
            print(f"Processing image {i+1}/{len(img_tags)}: {abs_url[:100]}...")
            resp = httpx.get(abs_url, timeout=15.0, follow_redirects=True, headers=headers)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "application/octet-stream")
            data_uri = to_data_uri(content_type, resp.content)
            tag["src"] = data_uri
            print(f"✅ Successfully inlined image {i+1}")
        except Exception as e:
            print(f"❌ Skipping image {abs_url} due to error: {e}")

    print("🖼️  Image inlining completed!")
    return str(soup)

async def fetch_design_context_async(url: str) -> dict:
    if not is_valid_url(url):
        raise HTTPException(status_code=400, detail=f"Invalid URL: {url}")
    
    data = await fetch_with_playwright_async(url)
    return {
        "head": data["head"],
        "body": data["body"],
        "css": data["critical_css"],
        "debug_info": data["debug_info"],
        "url": url
    }
