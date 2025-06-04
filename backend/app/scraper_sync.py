# backend/app/scraper_sync.py

import httpx
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from fastapi import HTTPException
from urllib.parse import urlparse

from utils import to_data_uri, resolve_url

PLAYWRIGHT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/115.0.5790.170 Safari/537.36"
)

def fetch_with_playwright_sync(url: str, timeout: float = 15000) -> dict:
    url = str(url)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=PLAYWRIGHT_USER_AGENT)
            page = context.new_page()

            page.route("**/*", lambda route, request: (
                route.abort() if request.resource_type == "image" else route.continue_()
            ))
            
            # Intercept requests and block invalid URLs
            def route_handler(route, request):
                req_url = request.url
                # Add your own logic here to detect and block invalid URLs
                if "githubgithubassets.com" in req_url:
                    return route.abort()  # skip loading this resource
                # You can extend this check with other patterns or malformed URLs
                route.continue_()

            page.route("**/*", route_handler)  # Intercept all requests

            page.goto(url, wait_until="networkidle", timeout=timeout)

            head_html = page.evaluate("() => document.head.outerHTML")
            body_html = page.evaluate("() => document.body.outerHTML")

            # Collect all inline <style> contents and all linked CSS files
            styles = page.eval_on_selector_all(
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
                            } catch (e) {
                                // ignore fetch errors
                            }
                        }
                    }
                    return cssTexts;
                }
                """
            )

            critical_css = "\n".join(styles)

            context.close()
            browser.close()

            return {
                "head": head_html,
                "body": body_html,
                "critical_css": critical_css,
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Playwright Sync Error: {e}")
    
def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)

def inline_images_sync(html: str, base_url: str) -> str:
    """
    For each <img src="…"> in `html`, fetch and replace with Base64 data URI.
    """
    soup = BeautifulSoup(html, "html.parser")
    img_tags = soup.find_all("img", src=True)

    headers = {"User-Agent": PLAYWRIGHT_USER_AGENT}

    for tag in img_tags:
        raw_src = tag["src"]
        abs_url = resolve_url(base_url, raw_src)

        if not is_valid_url(abs_url):
            print(f"Skipping invalid image URL: {abs_url}")
            continue

        try:
            resp = httpx.get(abs_url, timeout=10.0, follow_redirects=True, headers=headers)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "application/octet-stream")
            data_uri = to_data_uri(content_type, resp.content)
            tag["src"] = data_uri
        except Exception as e:
            print(f"Skipping image {abs_url} due to error: {e}")
            # leave original src unchanged

    return str(soup)


def fetch_design_context_sync(url: str) -> dict:
    """
    High-level function to call the sync scraper + inline-images.
    """
    data = fetch_with_playwright_sync(url)
    head_html = data["head"]
    body_html = data["body"]
    critical_css = data["critical_css"]

    # body_with_images = inline_images_sync(body_html, url)

    return {
        "head": head_html,
        "body": body_html, # withoout images for now
        "css": critical_css,
    }
