from fastapi import FastAPI
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

app = FastAPI()

_playwright = None
_browser = None

def get_browser():
    global _playwright, _browser
    if _browser is None or not _browser.is_connected():
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-sync",
                "--disable-translate",
                "--hide-scrollbars",
                "--metrics-recording-only",
                "--mute-audio",
                "--no-first-run",
                "--safebrowsing-disable-auto-update",
                "--js-flags=--max-old-space-size=256",
            ]
        )
    return _browser

def scrape_site(page, site_url):
    page.route("**/*", lambda route: route.abort()
        if route.request.resource_type in {"image", "stylesheet", "font", "media", "websocket"}
        else route.continue_()
    )

    page.goto(site_url, wait_until="domcontentloaded")
    try:
        page.wait_for_selector("div.house-item", timeout=10000)
    except:
        return []

    results = page.evaluate("""
        () => Array.from(document.querySelectorAll("div.house-item")).map(el => {
            const spans = el.querySelectorAll("div.house-basic span");
            const href = el.querySelector("a.house-preview")?.getAttribute("href");
            return {
                URL:     href ? "https://mountainhomesvail.com" + href : null,
                Image:   el.querySelector("img.house-img")?.getAttribute("src") ?? null,
                Price:   el.querySelector("span.house-price")?.innerText.trim() ?? null,
                Address: el.querySelector("div.house-address a")?.innerText.trim() ?? null,
                Beds:    spans[0]?.innerText.trim() ?? null,
                Baths:   spans[1]?.innerText.trim() ?? null,
                Sqft:    spans[2]?.innerText.trim() ?? null,
            };
        })
    """)
    return results

@app.get("/scrape")
def scrape():
    browser = get_browser()
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        java_script_enabled=True,
        bypass_csp=True,
    )
    stealth = Stealth()
    page = context.new_page()
    stealth.apply_stealth_sync(page)

    page.set_viewport_size({"width": 800, "height": 600})

    try:
        results = scrape_site(page, "https://mountainhomesvail.com/vailsexquisite")
    finally:
        page.close()
        context.close()

    return {"vailsexquisite": results}

@app.on_event("shutdown")
def shutdown():
    global _playwright, _browser
    if _browser:
        _browser.close()
    if _playwright:
        _playwright.stop()
