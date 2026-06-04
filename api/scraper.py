from fastapi import FastAPI
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

app = FastAPI()

def scrape_site(page, site_url):
    page.goto(site_url)
    page.wait_for_load_state("networkidle")

    try:
        page.wait_for_selector("div.house-item", timeout=10000)
    except:
        return []

    listings = page.query_selector_all("div.house-item")
    results = []

    for listing in listings: 
        url = listing.query_selector("a.house-preview")
        href = url.get_attribute("href") if url else None
        image = listing.query_selector("img.house-img")
        address = listing.query_selector("div.house-address a")
        price = listing.query_selector("span.house-price")
        spans = listing.query_selector_all("div.house-basic span")
        beds  = spans[0]
        baths = spans[1]
        sqft  = spans[2]

        results.append({
            "URL": f"https://mountainhomesvail.com{href}" if href else None,
            "Image": image.get_attribute("src") if image else None,
            "Price": price.inner_text().strip() if price else None,
            "Address": address.inner_text().strip() if address else None,
            "Beds": beds.inner_text().strip() if beds else None,
            "Baths": baths.inner_text().strip() if baths else None,
            "Sqft": sqft.inner_text().strip() if sqft else None,
        })

    return results

@app.get("/scrape")
def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ).new_page()
        Stealth()
        results = scrape_site(page, "https://mountainhomesvail.com/vailsexquisite")
        browser.close()
    return {"vailsexquisite": results}
