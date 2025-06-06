from scraper_sync import fetch_with_playwright_sync

if __name__ == "__main__":
    result = fetch_with_playwright_sync("https://pages-themes.github.io/cayman/")
    print("HEAD LENGTH:", len(result["head"]))
    print("BODY LENGTH:", len(result["body"]))
    # Print first 300 characters of body to verify content
    print("BODY PREVIEW:\n", result["body"][:300])